"""Parte 3b: classificação com embeddings (spaCy estático e BERT), mesmo split do TF-IDF.

Cada questão vira um vetor (média dos vetores das palavras / dos tokens) e entra numa
Regressão Logística. Os modelos não são re-treinados (só extração de features).
"""
import json
from pathlib import Path

import numpy as np
import spacy
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from transformers import AutoModel, AutoTokenizer

RAIZ = Path(__file__).resolve().parents[2]
OUT = RAIZ / "parte 3" / "classificacao"
qs = {q["id"]: q for q in json.load(open(RAIZ / "parte 1/corpus/corpus.json"))["questoes"]}
split = json.load(open(OUT / "split.json"))


def texto(q):
    return q["enunciado"] + " " + " ".join(a["texto"] for a in q["alternativas"])


def dados(chave):
    return [texto(qs[i]) for i in split[chave]], np.array([qs[i]["subarea"] for i in split[chave]])


Xtr, ytr = dados("treino")
Xte, yte = dados("teste")


def spacy_vecs(textos):
    nlp = spacy.load("pt_core_news_lg", disable=["parser", "ner"])
    return np.array([d.vector for d in nlp.pipe(textos, batch_size=64)])  # média dos vetores de palavra (300d)


def bert_vecs(textos, nome="neuralmind/bert-base-portuguese-cased"):
    tok, mod = AutoTokenizer.from_pretrained(nome), AutoModel.from_pretrained(nome).eval()
    saida = []
    with torch.no_grad():
        for i in range(0, len(textos), 16):
            b = tok(textos[i:i + 16], padding=True, truncation=True, max_length=512, return_tensors="pt")
            h = mod(**b).last_hidden_state
            m = b["attention_mask"].unsqueeze(-1)
            saida.append(((h * m).sum(1) / m.sum(1)).numpy())  # mean pooling ignorando padding (768d)
    return np.vstack(saida)


resultados = {}
for nome, f in [("spacy_pt_core_news_lg", spacy_vecs), ("bert_base_portuguese_cased", bert_vecs)]:
    print(f"\n=== {nome}")
    Vtr, Vte = f(Xtr), f(Xte)
    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, class_weight="balanced", C=0.1)).fit(Vtr, ytr)
    pred = clf.predict(Vte)
    print(classification_report(yte, pred, digits=3))
    resultados[nome] = {
        "teste_f1_macro": f1_score(yte, pred, average="macro"),
        "teste_acuracia": float((pred == yte).mean()),
        "relatorio": classification_report(yte, pred, output_dict=True),
        "matriz_confusao": {"classes": list(clf.classes_),
                            "valores": confusion_matrix(yte, pred, labels=clf.classes_).tolist()},
        "predicoes_teste": dict(zip(split["teste"], pred.tolist())),
    }

json.dump(resultados, open(OUT / "resultados_embeddings.json", "w"), indent=1, ensure_ascii=False)
