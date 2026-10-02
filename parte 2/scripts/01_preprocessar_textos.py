"""Passo 1 (item 2a.i): tokenizar, lematizar e remover stopwords."""
import argparse
import json
import unicodedata
from pathlib import Path

import spacy

from comum import ORIGEM_CORPUS, QUESTOES_LEMATIZADAS

# Termos de instrução e marcadores de prova removidos além das stopwords.
EXTRAS = set("assinalar assinale alternativa correto incorreto afirmar afirmação afirmativa considerar considere seguinte seguir questão item analise analiser respectivamente exemplo opção apresentar utilizar poder dever ser estar ter haver acordo relação referir ii iii iv vi vii viii ix xi xii xiii xiv xv".split())


def preprocessar(origem, saida):
    if saida.exists():
        raise ValueError("Arquivo processado já existe. Use outra --saida para preservá-lo.")
    questoes = sorted(json.loads(origem.read_bytes())["questoes"], key=lambda q: q["id"])
    nlp = spacy.load("pt_core_news_sm", disable=["parser", "ner"])
    stopwords = nlp.Defaults.stop_words | EXTRAS
    textos = [q["enunciado"] + "\n" + "\n".join(a["texto"] for a in q["alternativas"]) for q in questoes]
    processadas = []
    for q, doc in zip(questoes, nlp.pipe(textos, batch_size=32)):
        lemas, formas = [], []
        for token in doc:
            # Siglas usam a forma original para evitar flexões do lematizador.
            sigla = token.text.isupper() and len(token.text) >= 2
            lema = unicodedata.normalize("NFC", (token.text if sigla else token.lemma_).lower().strip())
            if (not token.is_alpha or token.is_stop or len(lema) < 2
                    or lema in stopwords or token.text.lower() in stopwords):
                continue
            if not sigla and token.pos_ not in {"NOUN", "PROPN", "ADJ", "VERB"}:
                continue
            lemas.append(lema)
            formas.append(token.text.lower())
        processadas.append({"id": q["id"], "lemas": lemas, "formas": formas})
    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("w", encoding="utf-8") as f:
        for q in processadas:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    print(f"{len(processadas)} questões tokenizadas e lematizadas. Saída: {saida}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--origem", type=Path, default=ORIGEM_CORPUS)
    p.add_argument("--saida", type=Path, default=QUESTOES_LEMATIZADAS)
    args = p.parse_args()
    try:
        preprocessar(args.origem, args.saida)
    except (ValueError, OSError) as e:
        p.exit(1, f"Erro: {e}\n")
