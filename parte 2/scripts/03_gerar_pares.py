"""Passo 3 (item 2a.iii): sortear 100 pares a partir das 200 palavras."""
import argparse
import csv
import random
from pathlib import Path

from comum import CORPUS, salvar_csv


def gerar_pares(origem, saida, semente=42):
    if saida.exists():
        raise ValueError("Pares já existem. Use outra --saida para preservar as anotações.")
    with origem.open(encoding="utf-8-sig", newline="") as f:
        palavras = [r["palavra"] for r in csv.DictReader(f)]
    if len(palavras) != 200 or len(set(palavras)) != 200 or any(not p.strip() for p in palavras):
        raise ValueError("A entrada deve conter exatamente 200 palavras distintas e não vazias.")
    random.Random(semente).shuffle(palavras)
    pares = [{"id_par": f"P{i+1:03}", "palavra_1": palavras[2*i], "palavra_2": palavras[2*i+1]} for i in range(100)]
    saida.parent.mkdir(parents=True, exist_ok=True)
    salvar_csv(saida, pares, list(pares[0]))
    print(f"100 pares sorteados sem reposição (semente {semente}). Saída: {saida}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--origem", type=Path, default=CORPUS / "palavras_similaridade.csv")
    p.add_argument("--saida", type=Path, default=CORPUS / "pares_similaridade.csv")
    p.add_argument("--semente", type=int, default=42)
    args = p.parse_args()
    try:
        gerar_pares(args.origem, args.saida, args.semente)
    except (ValueError, OSError) as e:
        p.exit(1, f"Erro: {e}\n")
