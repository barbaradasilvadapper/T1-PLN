"""Junta as anotações das duas anotadoras, mede a concordância e gera o corpus final (itens 2d e 2e).

Entrada: corpus/pares.csv e dados/anotacoes_similaridade/anotador_*.csv (uma nota de 1 a 5 por par)
Saída:   corpus/corpus_similaridade.csv e corpus/concordancia.json
"""
import json

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import cohen_kappa_score, confusion_matrix

from comum import CORPUS, DADOS, ler_csv, salvar_csv

pares = ler_csv(CORPUS / "pares.csv")
arquivos = sorted((DADOS / "anotacoes_similaridade").glob("anotador_*.csv"))

anotadoras = []   # (nome, {id_par: nota})
for arquivo in arquivos:
    linhas = ler_csv(arquivo)
    notas = {linha["id_par"]: int(linha["nota"]) for linha in linhas}
    assert len(notas) == len(pares), f"{arquivo.name} não tem nota para todos os pares"
    anotadoras.append((linhas[0]["anotador"], notas))

(nome_1, notas_1), (nome_2, notas_2) = anotadoras
ids = [p["id_par"] for p in pares]
a = np.array([notas_1[i] for i in ids])
b = np.array([notas_2[i] for i in ids])
escala = [1, 2, 3, 4, 5]

corpus = []
for par in pares:
    n1, n2 = notas_1[par["id_par"]], notas_2[par["id_par"]]
    corpus.append({
        **par,
        "tipo_anotacao": "humana",
        "anotador_1": nome_1, "nota_1": n1,
        "anotador_2": nome_2, "nota_2": n2,
        "similaridade_media": (n1 + n2) / 2,
        "similaridade_mediana": float(np.median([n1, n2])),
        "amplitude": abs(n1 - n2),
        "revisar": "sim" if abs(n1 - n2) >= 2 else "nao",   # diferença de 2 pontos ou mais
    })
salvar_csv(CORPUS / "corpus_similaridade.csv", corpus)

resultado = {
    "anotadoras": [nome_1, nome_2],
    "pares": len(ids),
    "distribuicao_notas": {nome: {str(n): list(notas.values()).count(n) for n in escala} for nome, notas in anotadoras},
    "kappa_linear": cohen_kappa_score(a, b, labels=escala, weights="linear"),
    "kappa_quadratico": cohen_kappa_score(a, b, labels=escala, weights="quadratic"),
    "kappa_sem_pesos": cohen_kappa_score(a, b, labels=escala),
    "concordancia_exata": float(np.mean(a == b)),
    "diferenca_ate_1": float(np.mean(np.abs(a - b) <= 1)),
    "diferenca_absoluta_media": float(np.mean(np.abs(a - b))),
    "spearman": float(spearmanr(a, b).statistic),
    "matriz_confusao": confusion_matrix(a, b, labels=escala).tolist(),
    "pares_para_revisar": [linha["id_par"] for linha in corpus if linha["revisar"] == "sim"],
}
with open(CORPUS / "concordancia.json", "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)

print(f"Kappa linear: {resultado['kappa_linear']:.2f}  |  concordância exata: {resultado['concordancia_exata']:.0%}"
      f"  |  Spearman: {resultado['spearman']:.2f}")
