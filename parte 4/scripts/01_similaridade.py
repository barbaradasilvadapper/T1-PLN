"""Parte 4: similaridade de palavras com 3 modelos (spaCy estático, BERT, LLM) vs. anotação humana.

Entrada : parte 2/corpus/corpus_similaridade.csv (100 pares, 2 anotadoras, escala 1-5)
          parte 4/dados/notas_llm_claude.csv (notas do LLM na mesma escala, ver README)
Saída   : parte 4/resultados/{similaridades.csv, correlacoes.json, dispersao.png}
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
OUT = RAIZ / "parte 4" / "resultados"
d = pd.read_csv(RAIZ / "parte 2/corpus/corpus_similaridade.csv", encoding="utf-8-sig")
d = d.merge(pd.read_csv(RAIZ / "parte 4/dados/notas_llm_claude.csv"), on="id_par")
palavras = sorted(set(d.palavra_1) | set(d.palavra_2))

# spaCy estático: vetor de 300d por palavra, similaridade = cosseno (token.similarity, como no notebook)
nlp = spacy.load("pt_core_news_lg")
tok = {p: nlp(p)[0] for p in palavras}
sem_vetor = [p for p, t in tok.items() if not t.has_vector]
d["spacy"] = [tok[a].similarity(tok[b]) for a, b in zip(d.palavra_1, d.palavra_2)]

# BERT: cada palavra isolada → média dos vetores dos subtokens (sem [CLS]/[SEP]) da última camada; cosseno
nome = "neuralmind/bert-base-portuguese-cased"
bt, bm = AutoTokenizer.from_pretrained(nome), AutoModel.from_pretrained(nome).eval()
vec = {}
with torch.no_grad():
    for p in palavras:
        b = bt(p, return_tensors="pt")
        vec[p] = bm(**b).last_hidden_state[0, 1:-1].mean(0).numpy()
cos = lambda u, v: float(u @ v / (np.linalg.norm(u) * np.linalg.norm(v)))
d["bert"] = [cos(vec[a], vec[b]) for a, b in zip(d.palavra_1, d.palavra_2)]
d["llm"] = d.nota_llm

d.to_csv(OUT / "similaridades.csv", index=False)

# correlação com a anotação humana (média das 2 anotadoras e cada uma separada)
alvos = {"humano_media": d.similaridade_media, "Luiza": d.nota_1, "Rafaela": d.nota_2}
modelos = ["spacy", "bert", "llm"]
res = {"n_pares": len(d), "palavras_sem_vetor_spacy": sem_vetor, "vs_humano": {}, "entre_modelos": {}}
for m in modelos:
    res["vs_humano"][m] = {a: {"spearman": spearmanr(d[m], v)[0], "pearson": pearsonr(d[m], v)[0]}
                           for a, v in alvos.items()}
for i, m1 in enumerate(modelos):
    for m2 in modelos[i + 1:]:
        res["entre_modelos"][f"{m1}~{m2}"] = spearmanr(d[m1], d[m2])[0]
res["humano_Luiza~Rafaela"] = spearmanr(d.nota_1, d.nota_2)[0]
json.dump(res, open(OUT / "correlacoes.json", "w"), indent=1, ensure_ascii=False)

fig, ax = plt.subplots(1, 3, figsize=(15, 4.5))
for a, m in zip(ax, modelos):
    a.scatter(d.similaridade_media + np.random.default_rng(0).normal(0, .03, len(d)), d[m], alpha=.6)
    a.set_title(f"{m}  (Spearman={res['vs_humano'][m]['humano_media']['spearman']:.2f})")
    a.set_xlabel("similaridade humana (média, escala 1-5)"); a.set_ylabel(m)
plt.tight_layout(); plt.savefig(OUT / "dispersao.png", dpi=130)

print("sem vetor no spaCy:", sem_vetor)
for m in modelos:
    r = res["vs_humano"][m]
    print(f"{m:6} Spearman vs média humana={r['humano_media']['spearman']:.3f} (Luiza {r['Luiza']['spearman']:.3f}, Rafaela {r['Rafaela']['spearman']:.3f}) | Pearson={r['humano_media']['pearson']:.3f}")
print("entre modelos:", {k: round(v, 3) for k, v in res["entre_modelos"].items()}, "| Luiza~Rafaela:", round(res["humano_Luiza~Rafaela"], 3))
print("\nmaiores discordâncias (rank humano vs modelo):")
for m in modelos:
    dif = (d[m].rank() - d.similaridade_media.rank()).abs().sort_values(ascending=False).index[:3]
    print(m, [(d.palavra_1[i], d.palavra_2[i], round(float(d[m][i]), 2), d.similaridade_media[i]) for i in dif])
