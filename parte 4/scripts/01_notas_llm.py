"""Parte 4 (LLM): pede ao Claude uma nota de 1 a 5 para cada par de palavras, na mesma escala das anotadoras.

Precisa da chave da API: export ANTHROPIC_API_KEY=...
Saída: parte 4/dados/notas_llm.csv (e notas_llm_aula.csv, se existir parte 4/dados/dataset_aula.csv)
"""
import csv
import sys
from pathlib import Path

import anthropic
import pandas as pd
from pydantic import BaseModel, Field

RAIZ = Path(__file__).resolve().parents[2]
DADOS = RAIZ / "parte 4" / "dados"
MODELO = "claude-opus-5-5"

# mesma escala e mesmas instruções que as anotadoras receberam (parte 2/README.md)
INSTRUCOES = """Você vai avaliar a semelhança de significado entre duas palavras no domínio de TI.
Avalie semelhança de significado, não apenas associação temática. Use a escala:
1 = nenhuma semelhança relevante de significado
2 = baixa: ligação principalmente temática ou funcional
3 = moderada: propriedades em comum, conceitos distintos
4 = alta: significados próximos, com diferenças importantes
5 = muito alta: sinônimos ou praticamente equivalentes"""


class Nota(BaseModel):
    nota: int = Field(ge=1, le=5)
    justificativa: str


def avaliar(cliente, p1, p2):
    r = cliente.messages.parse(
        model=MODELO,
        max_tokens=1024,
        output_config={"effort": "low"},
        system=INSTRUCOES,
        messages=[{"role": "user", "content": f"Palavra 1: {p1}\nPalavra 2: {p2}"}],
        output_format=Nota,
    )
    if r.stop_reason == "refusal" or r.parsed_output is None:
        raise RuntimeError(f"sem resposta para o par {p1}/{p2} (stop_reason={r.stop_reason})")
    return r.parsed_output


def rodar(pares, saida):
    cliente = anthropic.Anthropic()  # lê ANTHROPIC_API_KEY do ambiente
    saida.parent.mkdir(exist_ok=True)
    with open(saida, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["palavra_1", "palavra_2", "nota_llm", "justificativa", "modelo"])
        for i, (p1, p2) in enumerate(pares, 1):
            n = avaliar(cliente, p1, p2)
            w.writerow([p1, p2, n.nota, n.justificativa, MODELO])
            print(f"{i:3}/{len(pares)} {p1} / {p2}: {n.nota}")


if __name__ == "__main__":
    try:
        nosso = pd.read_csv(RAIZ / "parte 2/corpus/corpus_similaridade.csv", encoding="utf-8-sig")
        rodar(list(zip(nosso.palavra_1, nosso.palavra_2)), DADOS / "notas_llm.csv")
        if (DADOS / "dataset_aula.csv").exists():
            aula = pd.read_csv(DADOS / "dataset_aula.csv", encoding="utf-8-sig")
            rodar(list(zip(aula.palavra_1, aula.palavra_2)), DADOS / "notas_llm_aula.csv")
    except anthropic.AuthenticationError:
        sys.exit("Chave inválida ou ausente: defina ANTHROPIC_API_KEY antes de rodar.")
