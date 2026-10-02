"""Leitura dos dois datasets de similaridade, já na escala da aula (0, 0.25, 0.5, 0.75, 1)."""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
DADOS = RAIZ / "parte 4" / "dados"
RESULTADOS = RAIZ / "parte 4" / "resultados"
ARQUIVO_AULA = DADOS / "dataset_aula.xlsx"


def para_escala_aula(nota):
    """Escala da parte 2 (1 a 5) -> escala da aula (0 a 1). Os graus são os mesmos:
    1 nenhuma/nada similar, 2 baixa, 3 moderada/média, 4 alta, 5 muito alta/sinônimos."""
    return (nota - 1) / 4


def ler_nosso_dataset():
    d = pd.read_csv(RAIZ / "parte 2/corpus/corpus_similaridade.csv", encoding="utf-8-sig")
    return pd.DataFrame({
        "palavra_1": d.palavra_1, "palavra_2": d.palavra_2,
        "Luiza": para_escala_aula(d.nota_1), "Rafaela": para_escala_aula(d.nota_2),
        "similaridade": para_escala_aula(d.similaridade_media),
    })


def ler_dataset_aula():
    """Planilha da aula (aba AmostraParaAnotar), com a coluna 'Anotação Final' preenchida. None se não existir."""
    if not ARQUIVO_AULA.exists():
        return None
    d = pd.read_excel(ARQUIVO_AULA, sheet_name="AmostraParaAnotar").dropna(subset=["Anotação Final"])
    return pd.DataFrame({
        "palavra_1": d["Termo A"].str.strip().str.lower(), "palavra_2": d["Termo B"].str.strip().str.lower(),
        "similaridade": d["Anotação Final"].astype(float),
    })
