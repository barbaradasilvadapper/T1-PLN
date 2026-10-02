"""Parte 4 (LLM): pede ao Gemini uma nota de similaridade para cada par de palavras.

Usa a escala da anotação feita em aula (0, 0.25, 0.5, 0.75, 1), a mesma para os dois datasets.
Os pares vão em lotes de 25 por pedido, porque o plano gratuito só permite 20 pedidos por dia em cada modelo.
Precisa da chave do Gemini (gratuita, Google AI Studio): export GEMINI_API_KEY=...
Saída: parte 4/dados/notas_llm_nosso.csv (e notas_llm_aula.csv, se existir o dataset de aula)
"""
import csv
import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent))
from comum import DADOS, ler_dataset_aula, ler_nosso_dataset

MODELO = "gemini-3.5-flash"
LOTE = 25
GRAUS = (0, 0.25, 0.5, 0.75, 1)

# mesmas definições e exemplos da planilha de anotação da aula
INSTRUCOES = """Você vai avaliar a similaridade de significado entre pares de termos da área de computação.
Avalie cada par separadamente e use apenas um destes graus:
0 = nada similar (ex.: ponteiro / teclado)
0.25 = baixa similaridade (ex.: criptografia / backup)
0.5 = média similaridade (ex.: ajustar / padronizar)
0.75 = alta similaridade (ex.: repositório / diretório)
1 = sinônimos (ex.: executar / rodar)
Responda com uma nota para cada número de par da lista."""


class NotaPar(BaseModel):
    par: int
    grau: float
    justificativa: str


def avaliar_lote(cliente, pares):
    lista = "\n".join(f"{i}. {a} / {b}" for i, (a, b) in enumerate(pares, 1))
    for tentativa in range(5):
        try:
            r = cliente.models.generate_content(
                model=MODELO,
                contents=lista,
                config=types.GenerateContentConfig(system_instruction=INSTRUCOES, temperature=0,
                                                   response_mime_type="application/json",
                                                   response_schema=list[NotaPar]),
            )
        except genai.errors.APIError as e:
            if e.code not in (429, 503):  # limite do plano gratuito ou servidor ocupado: espera e tenta de novo
                raise
            print(f"  Gemini respondeu {e.code}, tentando de novo em 60 s", flush=True)
            time.sleep(60)
            continue
        notas = {n.par: n for n in r.parsed or []}
        if sorted(notas) == list(range(1, len(pares) + 1)) and all(n.grau in GRAUS for n in notas.values()):
            return [notas[i] for i in range(1, len(pares) + 1)]
        print("  resposta incompleta ou fora da escala, pedindo de novo", flush=True)
    raise RuntimeError("o Gemini não respondeu o lote; rode de novo mais tarde (a cota gratuita renova por dia)")


def rodar(cliente, pares, saida):
    """Retomável: se o arquivo já existe, só avalia os pares que ainda não têm nota."""
    feitos = set()
    if saida.exists():
        with open(saida, encoding="utf-8") as f:
            feitos = {(l["palavra_1"], l["palavra_2"]) for l in csv.DictReader(f)}
    faltam = [p for p in pares if p not in feitos]
    with open(saida, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not feitos:
            w.writerow(["palavra_1", "palavra_2", "nota_llm", "justificativa", "modelo"])
        for ini in range(0, len(faltam), LOTE):
            lote = faltam[ini:ini + LOTE]
            for (a, b), n in zip(lote, avaliar_lote(cliente, lote)):
                w.writerow([a, b, n.grau, n.justificativa, MODELO])
            f.flush()
            print(f"{saida.name}: {len(feitos) + ini + len(lote)}/{len(pares)} pares", flush=True)


if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit("Defina a chave antes de rodar: export GEMINI_API_KEY=...")
    cliente = genai.Client()  # lê GEMINI_API_KEY do ambiente
    DADOS.mkdir(exist_ok=True)
    nosso = ler_nosso_dataset()
    rodar(cliente, list(zip(nosso.palavra_1, nosso.palavra_2)), DADOS / "notas_llm_nosso.csv")
    aula = ler_dataset_aula()
    if aula is not None:
        rodar(cliente, list(zip(aula.palavra_1, aula.palavra_2)), DADOS / "notas_llm_aula.csv")
