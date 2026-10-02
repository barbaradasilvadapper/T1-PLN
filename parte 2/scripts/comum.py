"""Caminhos e funções usados pelos scripts da parte 2."""
import csv
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CORPUS = RAIZ / "corpus"
DADOS = RAIZ / "dados"
CORPUS_QUESTOES = RAIZ.parent / "parte 1" / "corpus" / "corpus.json"
QUESTOES_LEMATIZADAS = DADOS / "intermediario" / "questoes_lematizadas.jsonl"


def ler_csv(caminho):
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def salvar_csv(caminho, linhas):
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(linhas[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(linhas)
