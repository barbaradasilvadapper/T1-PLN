"""Escolhe as 200 palavras mais representativas: os lemas com maior TF-IDF médio nas questões (item 2a.ii).

Saída: corpus/palavras.csv, com o TF-IDF médio, a frequência, as formas que apareceram no texto e algumas
questões de exemplo de cada palavra.
"""
import json
from collections import Counter, defaultdict

from sklearn.feature_extraction.text import TfidfVectorizer

from comum import CORPUS, QUESTOES_LEMATIZADAS, salvar_csv

with open(QUESTOES_LEMATIZADAS, encoding="utf-8") as f:
    questoes = [json.loads(linha) for linha in f]

documentos = []
frequencia = Counter()
formas = defaultdict(Counter)
exemplos = defaultdict(list)
for q in questoes:
    documentos.append(" ".join(q["lemas"]))
    frequencia.update(q["lemas"])
    for lema, forma in zip(q["lemas"], q["formas"]):
        formas[lema][forma] += 1
    for lema in sorted(set(q["lemas"])):
        if len(exemplos[lema]) < 3:
            exemplos[lema].append(q["id"])

# os textos já estão lematizados, então cada palavra separada por espaço é um termo
vectorizer = TfidfVectorizer(tokenizer=str.split, token_pattern=None, lowercase=False,
                             min_df=5, max_df=0.8, sublinear_tf=True, norm="l2", smooth_idf=True)
matriz = vectorizer.fit_transform(documentos)
termos = vectorizer.get_feature_names_out()
media = matriz.mean(axis=0).A1
questoes_com_termo = (matriz > 0).sum(axis=0).A1

# maior TF-IDF médio primeiro; no empate, ordem alfabética
ordem = sorted(range(len(termos)), key=lambda i: (-float(media[i]), termos[i]))[:200]
palavras = []
for posicao, i in enumerate(ordem, 1):
    termo = termos[i]
    palavras.append({
        "posicao": posicao,
        "palavra": termo,
        "tfidf_medio": float(media[i]),
        "frequencia": frequencia[termo],
        "questoes_com_palavra": int(questoes_com_termo[i]),
        "formas_observadas": " | ".join(forma for forma, _ in formas[termo].most_common(5)),
        "ids_exemplo": " | ".join(exemplos[termo]),
    })

salvar_csv(CORPUS / "palavras.csv", palavras)
print("200 palavras salvas em corpus/palavras.csv")
