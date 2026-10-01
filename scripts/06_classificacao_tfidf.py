"""Parte 3a: classificação de questões por subárea com Bag-of-Words + TF-IDF.

Saída: classificacao/resultados_tfidf.json e classificacao/split.json (mesmo split p/ os outros modelos).
"""
import json
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline

RAIZ = Path(__file__).resolve().parent.parent
OUT = RAIZ / "classificacao"
OUT.mkdir(exist_ok=True)

qs = json.load(open(RAIZ / "corpus/corpus.json"))["questoes"]


def texto(q):
    return q["enunciado"] + " " + " ".join(a["texto"] for a in q["alternativas"])


X = [texto(q) for q in qs]
y = np.array([q["subarea"] for q in qs])
ids = [q["id"] for q in qs]

# Split 80/20 estratificado, fixo: todos os modelos (TF-IDF, spaCy, BERT) usam o mesmo teste.
i_tr, i_te = train_test_split(range(len(qs)), test_size=0.2, stratify=y, random_state=42)
json.dump({"treino": [ids[i] for i in i_tr], "teste": [ids[i] for i in i_te]},
          open(OUT / "split.json", "w"))
Xtr, ytr = [X[i] for i in i_tr], y[i_tr]
Xte, yte = [X[i] for i in i_te], y[i_te]

cv = StratifiedKFold(5, shuffle=True, random_state=42)


def pipe(**tfidf):
    return make_pipeline(
        TfidfVectorizer(lowercase=True, sublinear_tf=True, **tfidf),
        LogisticRegression(max_iter=2000, class_weight="balanced"),
    )


def cv_f1(**tfidf):
    # seleção só no treino (CV); o teste não é tocado até o fim
    return cross_val_score(pipe(**tfidf), Xtr, ytr, cv=cv, scoring="f1_macro").mean()


# 1) comprimento da BoW (max_features), unigramas
print("max_features -> F1-macro (CV 5-fold no treino)")
res_mf = {}
for mf in [200, 500, 1000, 2000, 5000, 10000, None]:
    res_mf[str(mf)] = cv_f1(max_features=mf, ngram_range=(1, 1))
    print(f"  {str(mf):>6}: {res_mf[str(mf)]:.4f}")

# 2) n-gramas e min_df, fixando o melhor max_features
melhor_mf = max(res_mf, key=res_mf.get)
mf = None if melhor_mf == "None" else int(melhor_mf)
print(f"\nmelhor max_features = {melhor_mf}; testando ngram/min_df")
res_cfg = {}
for ng in [(1, 1), (1, 2)]:
    for md in [1, 2, 5]:
        k = f"ngram={ng},min_df={md}"
        res_cfg[k] = cv_f1(max_features=mf, ngram_range=ng, min_df=md)
        print(f"  {k}: {res_cfg[k]:.4f}")

melhor = max(res_cfg, key=res_cfg.get)
ng = (1, 2) if "(1, 2)" in melhor else (1, 1)
md = int(melhor.split("min_df=")[1])
final = pipe(max_features=mf, ngram_range=ng, min_df=md).fit(Xtr, ytr)
pred = final.predict(Xte)
print(f"\nconfig final: max_features={melhor_mf}, {melhor}")
print(classification_report(yte, pred, digits=3))

json.dump({
    "cv_max_features": res_mf, "cv_config": res_cfg,
    "config_final": {"max_features": mf, "ngram_range": ng, "min_df": md, "sublinear_tf": True},
    "teste_f1_macro": f1_score(yte, pred, average="macro"),
    "teste_acuracia": float((pred == yte).mean()),
    "relatorio": classification_report(yte, pred, output_dict=True),
}, open(OUT / "resultados_tfidf.json", "w"), indent=1, ensure_ascii=False)

# termos mais pesados por classe (interpretabilidade)
vec, clf = final[0], final[1]
nomes = np.array(vec.get_feature_names_out())
for c, coef in zip(clf.classes_, clf.coef_):
    print(f"{c}: {', '.join(nomes[np.argsort(coef)[-8:][::-1]])}")
