"""Parte 3c: compara os 3 modelos (tabela, matrizes de confusão, erros em comum). Saída: parte 3/classificacao/."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = Path(__file__).resolve().parents[2]
OUT = RAIZ / "parte 3" / "classificacao"
tf = json.load(open(OUT / "resultados_tfidf.json"))
emb = json.load(open(OUT / "resultados_embeddings.json"))
modelos = {"TF-IDF + LogReg": tf, "spaCy pt_core_news_lg": emb["spacy_pt_core_news_lg"],
           "BERTimbau (mean pooling)": emb["bert_base_portuguese_cased"]}
qs = {q["id"]: q for q in json.load(open(RAIZ / "parte 1/corpus/corpus.json"))["questoes"]}

fig, eixos = plt.subplots(1, 3, figsize=(18, 5.5))
curto = lambda c: c.replace("_e_", " e ").replace("_", " ")[:18]
for ax, (nome, r) in zip(eixos, modelos.items()):
    m, cl = r["matriz_confusao"]["valores"], r["matriz_confusao"]["classes"]
    ax.imshow(m, cmap="Blues")
    ax.set_xticks(range(5), [curto(c) for c in cl], rotation=45, ha="right")
    ax.set_yticks(range(5), [curto(c) for c in cl])
    for i in range(5):
        for j in range(5):
            ax.text(j, i, m[i][j], ha="center", va="center", color="white" if m[i][j] > 60 else "black")
    ax.set_title(f"{nome}\nF1-macro={r['teste_f1_macro']:.3f}")
    ax.set_xlabel("previsto"); ax.set_ylabel("real")
plt.tight_layout(); plt.savefig(OUT / "matrizes_confusao.png", dpi=130)

# erros: quantos modelos erraram cada questão do teste
erros = {i: [n for n, r in modelos.items() if r["predicoes_teste"][i] != qs[i]["subarea"]] for i in tf["predicoes_teste"]}
todos = [i for i, e in erros.items() if len(e) == 3]
linhas = ["# Parte 3 - comparação dos modelos\n", "| Modelo | F1-macro | Acurácia |", "|---|---:|---:|"]
linhas += [f"| {n} | {r['teste_f1_macro']:.3f} | {r['teste_acuracia']:.3f} |" for n, r in modelos.items()]
linhas += [f"\nTeste: {len(erros)} questões. Erradas por nenhum modelo: {sum(not e for e in erros.values())}; "
           f"por todos os 3: {len(todos)}; só pelos embeddings (TF-IDF acertou): "
           f"{sum(bool(e) and 'TF-IDF + LogReg' not in e for e in erros.values())}.\n",
           "## Questões que os 3 modelos erraram (amostra)\n"]
for i in todos[:12]:
    q = qs[i]
    linhas.append(f"- `{i}` real=**{q['subarea']}**, TF-IDF previu **{tf['predicoes_teste'][i]}**: {q['enunciado'][:160]}…")
open(OUT / "COMPARACAO.md", "w").write("\n".join(linhas))
print("\n".join(linhas))
