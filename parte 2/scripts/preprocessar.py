"""Tokeniza, lematiza e tira as stopwords das questões da parte 1 (item 2a.i).

Saída: dados/intermediario/questoes_lematizadas.jsonl, com os lemas de cada questão e a forma original
de cada lema (usada depois para mostrar exemplos no palavras.csv).
"""
import json
import unicodedata

import spacy

from comum import CORPUS_QUESTOES, QUESTOES_LEMATIZADAS

# palavras de instrução de prova, que aparecem em todas as áreas, e números romanos dos itens
EXTRAS = set("assinalar assinale alternativa correto incorreto afirmar afirmação afirmativa considerar considere "
             "seguinte seguir questão item analise analiser respectivamente exemplo opção apresentar utilizar poder "
             "dever ser estar ter haver acordo relação referir ii iii iv vi vii viii ix xi xii xiii xiv xv".split())

with open(CORPUS_QUESTOES, encoding="utf-8") as f:
    questoes = sorted(json.load(f)["questoes"], key=lambda q: q["id"])

nlp = spacy.load("pt_core_news_sm", disable=["parser", "ner"])
stopwords = nlp.Defaults.stop_words | EXTRAS
textos = [q["enunciado"] + "\n" + "\n".join(a["texto"] for a in q["alternativas"]) for q in questoes]

QUESTOES_LEMATIZADAS.parent.mkdir(parents=True, exist_ok=True)
with open(QUESTOES_LEMATIZADAS, "w", encoding="utf-8") as saida:
    for q, doc in zip(questoes, nlp.pipe(textos, batch_size=32)):
        lemas, formas = [], []
        for token in doc:
            # siglas ficam como estão, porque o lematizador às vezes transforma a sigla em outra palavra
            sigla = token.text.isupper() and len(token.text) >= 2
            lema = unicodedata.normalize("NFC", (token.text if sigla else token.lemma_).lower().strip())
            if not token.is_alpha or token.is_stop or len(lema) < 2:
                continue
            if lema in stopwords or token.text.lower() in stopwords:
                continue
            if not sigla and token.pos_ not in {"NOUN", "PROPN", "ADJ", "VERB"}:
                continue
            lemas.append(lema)
            formas.append(token.text.lower())
        saida.write(json.dumps({"id": q["id"], "lemas": lemas, "formas": formas}, ensure_ascii=False) + "\n")

print(f"{len(questoes)} questões processadas")
