"""Embaralha as 200 palavras e forma 100 pares, sem repetir palavra (item 2a.iii).

A semente fixa (42) faz o sorteio sair sempre igual. Saída: corpus/pares.csv
"""
import random

from comum import CORPUS, ler_csv, salvar_csv

palavras = [linha["palavra"] for linha in ler_csv(CORPUS / "palavras.csv")]
random.Random(42).shuffle(palavras)

pares = []
for i in range(100):
    pares.append({"id_par": f"P{i + 1:03}", "palavra_1": palavras[2 * i], "palavra_2": palavras[2 * i + 1]})

salvar_csv(CORPUS / "pares.csv", pares)
print("100 pares salvos em corpus/pares.csv")
