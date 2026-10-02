"""Parte 4: similaridade de palavras com spaCy (estático), BERTimbau e um LLM, comparada às notas humanas.

Conjuntos avaliados:
  - nosso: parte 2/corpus/corpus_similaridade.csv (100 pares, notas de Luiza e Rafaela)
  - aula:  parte 4/dados/dataset_aula.csv, se existir (colunas palavra_1, palavra_2, similaridade)
Notas do LLM: parte 4/dados/notas_llm*.csv, geradas pelo 01_notas_llm.py (se ainda não existirem, o LLM fica de fora).
Saída: parte 4/resultados/
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import spacy
import torch
from scipy.stats import pearsonr, spearmanr
from transformers import AutoModel, AutoTokenizer

RAIZ = Path(__file__).resolve().parents[2]
DADOS = RAIZ / "parte 4" / "dados"
OUT = RAIZ / "parte 4" / "resultados"
OUT.mkdir(exist_ok=True)

nlp = spacy.load("pt_core_news_lg")
NOME_BERT = "neuralmind/bert-base-portuguese-cased"
bt, bm = AutoTokenizer.from_pretrained(NOME_BERT), AutoModel.from_pretrained(NOME_BERT).eval()


def sim_spacy(a, b):
    # cosseno entre os vetores estáticos (300d), como no notebook similaridadeEntreTokens
    return nlp(a)[0].similarity(nlp(b)[0])


def vetor_bert(p):
    # palavra isolada: média dos subtokens da última camada, sem [CLS] e [SEP]
    with torch.no_grad():
        return bm(**bt(p, return_tensors="pt")).last_hidden_state[0, 1:-1].mean(0).numpy()


def sim_bert(a, b):
    u, v = vetor_bert(a), vetor_bert(b)
    return float(u @ v / (np.linalg.norm(u) * np.linalg.norm(v)))


def avaliar(nome, d, humanos, arquivo_llm):
    """d tem palavra_1, palavra_2 e as colunas de nota humana listadas em `humanos` (a primeira é a referência)."""
    d = d.copy()
    d["spacy"] = [sim_spacy(a, b) for a, b in zip(d.palavra_1, d.palavra_2)]
    d["bert"] = [sim_bert(a, b) for a, b in zip(d.palavra_1, d.palavra_2)]
    modelos = ["spacy", "bert"]
    if arquivo_llm.exists():
        llm = pd.read_csv(arquivo_llm)[["palavra_1", "palavra_2", "nota_llm"]]
        d = d.merge(llm, on=["palavra_1", "palavra_2"], how="left").rename(columns={"nota_llm": "llm"})
        modelos.append("llm")
    else:
        print(f"[{nome}] sem {arquivo_llm.name}: rode o 01_notas_llm.py para incluir o LLM")
    d.to_csv(OUT / f"similaridades_{nome}.csv", index=False)

    res = {"pares": len(d), "vs_humano": {}, "entre_modelos": {}}
    for m in modelos:
        res["vs_humano"][m] = {h: {"spearman": spearmanr(d[m], d[h])[0], "pearson": pearsonr(d[m], d[h])[0]}
                               for h in humanos}
    for i, m1 in enumerate(modelos):
        for m2 in modelos[i + 1:]:
            res["entre_modelos"][f"{m1} x {m2}"] = spearmanr(d[m1], d[m2])[0]

    ref = humanos[0]
    fig, ax = plt.subplots(1, len(modelos), figsize=(5 * len(modelos), 4.2))
    for a, m in zip(np.atleast_1d(ax), modelos):
        jitter = np.random.default_rng(0).normal(0, .03, len(d))  # só para os pontos não se sobreporem
        a.scatter(d[ref] + jitter, d[m], alpha=.6)
        a.set_title(f"{m} (Spearman = {res['vs_humano'][m][ref]['spearman']:.2f})")
        a.set_xlabel(f"nota humana ({ref})")
        a.set_ylabel(m)
    plt.tight_layout()
    plt.savefig(OUT / f"dispersao_{nome}.png", dpi=130)

    print(f"\n== {nome} ({len(d)} pares)")
    for m in modelos:
        r = res["vs_humano"][m]
        print(f"{m:6} " + " | ".join(f"{h}: Spearman {v['spearman']:.3f}, Pearson {v['pearson']:.3f}" for h, v in r.items()))
    print("entre modelos:", {k: round(float(v), 3) for k, v in res["entre_modelos"].items()})
    print("pares em que cada modelo mais discorda das notas humanas:")
    for m in modelos:
        idx = (d[m].rank() - d[ref].rank()).abs().sort_values(ascending=False).index[:3]
        print(f"  {m}: " + "; ".join(f"{d.palavra_1[i]}/{d.palavra_2[i]} ({d[m][i]:.2f} x {d[ref][i]})" for i in idx))
    return res


nosso = pd.read_csv(RAIZ / "parte 2/corpus/corpus_similaridade.csv", encoding="utf-8-sig")
nosso = nosso.rename(columns={"nota_1": "Luiza", "nota_2": "Rafaela"})
resultados = {"nosso": avaliar("nosso", nosso, ["similaridade_media", "Luiza", "Rafaela"], DADOS / "notas_llm.csv")}
resultados["nosso"]["Luiza x Rafaela"] = spearmanr(nosso.Luiza, nosso.Rafaela)[0]

if (DADOS / "dataset_aula.csv").exists():
    aula = pd.read_csv(DADOS / "dataset_aula.csv", encoding="utf-8-sig")
    resultados["aula"] = avaliar("aula", aula, ["similaridade"], DADOS / "notas_llm_aula.csv")
else:
    print("\nsem parte 4/dados/dataset_aula.csv: o dataset feito em aula ainda não foi incluído")

json.dump(resultados, open(OUT / "correlacoes.json", "w"), indent=1, ensure_ascii=False)
