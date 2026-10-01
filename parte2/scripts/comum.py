"""Caminhos e escrita de CSV para o corpus de similaridade."""
import csv
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CORPUS = RAIZ / "corpus"
DADOS = RAIZ / "dados"
ORIGEM_CORPUS = RAIZ.parent / "corpus" / "corpus.json"


def salvar_csv(path, linhas, campos):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=campos, lineterminator="\n")
        writer.writeheader()
        writer.writerows(linhas)
