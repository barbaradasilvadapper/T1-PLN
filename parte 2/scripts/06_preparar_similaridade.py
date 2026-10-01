"""Item 2a: lematização, ranking TF-IDF e sorteio sem reposição."""
import argparse
import json
import random
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import spacy
from sklearn.feature_extraction.text import TfidfVectorizer

from comum import CORPUS, ORIGEM_CORPUS, salvar_csv
# Palavras do formato de prova, explicitadas para auditoria (não são termos de TI).
EXTRAS = set("assinalar assinale alternativa correto incorreto afirmar afirmação afirmativa considerar considere seguinte seguir questão item analise analiser respectivamente exemplo opção apresentar utilizar poder dever ser estar ter haver acordo relação referir ii iii iv vi vii viii ix xi xii xiii xiv xv".split())


def preparar(origem, saida, semente=42):
    if any((saida / nome).exists() for nome in ("palavras_similaridade.csv", "pares_similaridade.csv")):
        raise ValueError("Arquivos de similaridade já existem. Use outra --saida para preservar os pares anotados.")
    bruto = origem.read_bytes()
    questoes = sorted(json.loads(bruto)["questoes"], key=lambda q: q["id"])
    nlp = spacy.load("pt_core_news_sm", disable=["parser", "ner"])
    stopwords = nlp.Defaults.stop_words | EXTRAS
    textos = [q["enunciado"] + "\n" + "\n".join(a["texto"] for a in q["alternativas"]) for q in questoes]
    documentos = []
    frequencias, formas, contextos = Counter(), defaultdict(Counter), defaultdict(list)
    for q, doc in zip(questoes, nlp.pipe(textos, batch_size=32)):
        termos = []
        for token in doc:
            # Siglas são preservadas; o modelo português pode flexionar nomes técnicos.
            sigla = token.text.isupper() and len(token.text) >= 2
            lema = unicodedata.normalize("NFC", (token.text if sigla else token.lemma_).lower().strip())
            if (not token.is_alpha or token.is_stop or len(lema) < 2
                    or lema in stopwords or token.text.lower() in stopwords):
                continue
            if not sigla and token.pos_ not in {"NOUN", "PROPN", "ADJ", "VERB"}:
                continue
            termos.append(lema)
            formas[lema][token.text.lower()] += 1
        frequencias.update(termos)
        for lema in sorted(set(termos)):
            if len(contextos[lema]) < 3:
                contextos[lema].append(q["id"])
        documentos.append(" ".join(termos))
    vet = TfidfVectorizer(tokenizer=str.split, token_pattern=None, lowercase=False,
                         min_df=5, max_df=0.8, sublinear_tf=True, norm="l2", smooth_idf=True)
    matriz = vet.fit_transform(documentos)
    termos = vet.get_feature_names_out()
    medias = matriz.mean(axis=0).A1
    df = (matriz > 0).sum(axis=0).A1
    ordem = sorted(range(len(termos)), key=lambda i: (-float(medias[i]), termos[i]))
    if len(ordem) < 200:
        raise ValueError(f"Vocabulário insuficiente: {len(ordem)} termos elegíveis.")
    ranking = [{"posicao": p, "palavra": termos[i], "tfidf_medio": float(medias[i]),
                "frequencia": frequencias[termos[i]], "questoes_com_palavra": int(df[i]),
                "formas_observadas": " | ".join(x for x, _ in formas[termos[i]].most_common(5)),
                "ids_exemplo": " | ".join(contextos[termos[i]])}
               for p, i in enumerate(ordem[:200], 1)]
    palavras = [r["palavra"] for r in ranking]
    random.Random(semente).shuffle(palavras)
    pares = [{"id_par": f"P{i+1:03}", "palavra_1": palavras[2*i], "palavra_2": palavras[2*i+1]} for i in range(100)]
    saida.mkdir(parents=True, exist_ok=True)
    salvar_csv(saida / "palavras_similaridade.csv", ranking, list(ranking[0]))
    salvar_csv(saida / "pares_similaridade.csv", pares, list(pares[0]))
    print(f"{len(questoes)} questões -> 200 palavras -> 100 pares. Saída: {saida}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--origem", type=Path, default=ORIGEM_CORPUS)
    p.add_argument("--saida", type=Path, default=CORPUS)
    p.add_argument("--semente", type=int, default=42)
    args = p.parse_args()
    try:
        preparar(args.origem, args.saida, args.semente)
    except (ValueError, OSError) as e:
        p.exit(1, f"Erro: {e}\n")
