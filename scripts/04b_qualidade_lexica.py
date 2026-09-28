"""Etapa 4b (item g / campo "Qualidade dos textos" do dataset card): qualidade léxica.

Mede a proporção de tokens alfabéticos (>= 2 letras) reconhecidos em dicionários de português ou de
inglês (pyspellchecker). Termos técnicos em inglês são comuns em TI, por isso os dois idiomas. Tokens não
reconhecidos são, em grande parte, siglas e nomes de produtos (ex.: "kubernetes") e palavras comuns que faltam
no dicionário de português da biblioteca (ex.: "gerenciamento"), não erros de conversão; então a medida é um
limite inferior da qualidade do texto.

Requer: pip install pyspellchecker        Saída: corpus/qualidade_lexica.json (lido por 04_estatisticas.py)
"""
import json
import re
from collections import Counter

from spellchecker import SpellChecker

from comum import CORPUS

ALFA = re.compile(r"[^\W\d_]{2,}")


def main():
    qs = json.load(open(CORPUS / "corpus.json", encoding="utf-8"))["questoes"]
    pt, en = SpellChecker(language="pt"), SpellChecker(language="en")
    tokens = [t.lower() for q in qs for t in ALFA.findall(q["enunciado"] + " " + " ".join(a["texto"] for a in q["alternativas"]))]
    freq = Counter(tokens)
    conhecidos = {w for w in freq if w in pt or w in en}
    reconhecidos = sum(n for w, n in freq.items() if w in conhecidos)
    desconhecidos = Counter({w: n for w, n in freq.items() if w not in conhecidos})
    res = {
        "metodo": "proporção de tokens alfabéticos (>= 2 letras, minúsculas) presentes no dicionário pt ou en do pyspellchecker",
        "tokens_alfabeticos": len(tokens),
        "tokens_reconhecidos": reconhecidos,
        "proporcao_reconhecida": round(reconhecidos / len(tokens), 4),
        "types_alfabeticos": len(freq),
        "types_reconhecidos": len(conhecidos),
        "proporcao_types_reconhecidos": round(len(conhecidos) / len(freq), 4),
        "nao_reconhecidos_mais_frequentes": desconhecidos.most_common(40),
    }
    json.dump(res, open(CORPUS / "qualidade_lexica.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"tokens reconhecidos: {res['proporcao_reconhecida']:.2%} | types: {res['proporcao_types_reconhecidos']:.2%}")


if __name__ == "__main__":
    main()
