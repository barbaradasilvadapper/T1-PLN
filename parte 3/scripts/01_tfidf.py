"""Parte 3a: classificação de questões por subárea com Bag-of-Words + TF-IDF.

Segue o notebook da professora (ExemploClassificação_representacaoBoW): split estratificado 80/20 com
random_state=42, TfidfVectorizer com sublinear_tf, relatório por classe e matriz de confusão.
Saída: parte 3/resultados/split.json (mesmo split p/ os outros modelos) e resultados_tfidf.json.
"""
import json
from pathlib import Path

import numpy as np
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline

RAIZ = Path(__file__).resolve().parents[2]
OUT = RAIZ / "parte 3" / "resultados"
OUT.mkdir(exist_ok=True)

qs = json.load(open(RAIZ / "parte 1/corpus/corpus.json"))["questoes"]
# lemas sem stopwords gerados na parte 2 (spaCy: tokeniza, lematiza, remove stopwords)
lemas = {}
for linha in open(RAIZ / "parte 2/dados/intermediario/questoes_lematizadas.jsonl"):
    d = json.loads(linha)
    lemas[d["id"]] = " ".join(d["lemas"])

ids = [q["id"] for q in qs]
y = np.array([q["subarea"] for q in qs])
X_cru = [q["enunciado"] + " " + " ".join(a["texto"] for a in q["alternativas"]) for q in qs]
X_lem = [lemas[i] for i in ids]

# Split 80/20 estratificado, fixo: todos os modelos (TF-IDF, spaCy, BERT) usam o mesmo teste.
i_tr, i_te = train_test_split(range(len(qs)), test_size=0.2, stratify=y, random_state=42)
json.dump({"treino": [ids[i] for i in i_tr], "teste": [ids[i] for i in i_te]}, open(OUT / "split.json", "w"))
ytr, yte = y[i_tr], y[i_te]
cortar = lambda X, idx: [X[i] for i in idx]

cv = StratifiedKFold(5, shuffle=True, random_state=42)
STOP = list(spacy.blank("pt").Defaults.stop_words)  # stopwords do spaCy, como no notebook


def pipe(clf=None, **tfidf):
    return make_pipeline(
        TfidfVectorizer(lowercase=True, sublinear_tf=True, **tfidf),
        clf or LogisticRegression(max_iter=2000, class_weight="balanced"),
    )


def cv_f1(X, clf=None, **tfidf):
    # seleção só no treino (CV); o teste não é tocado até o fim
    return cross_val_score(pipe(clf, **tfidf), cortar(X, i_tr), ytr, cv=cv, scoring="f1_macro").mean()


# 1) comprimento da BoW (max_features), texto cru, unigramas
print("max_features -> F1-macro (CV 5-fold no treino)")
res_mf = {}
for mf in [200, 500, 1000, 2000, 5000, 10000, None]:
    res_mf[str(mf)] = cv_f1(X_cru, max_features=mf)
    print(f"  {str(mf):>6}: {res_mf[str(mf)]:.4f}")
melhor_mf = max(res_mf, key=res_mf.get)
mf = None if melhor_mf == "None" else int(melhor_mf)

# 2) n-gramas e min_df
print(f"\nmelhor max_features = {melhor_mf}; testando ngram/min_df")
res_cfg = {}
for ng in [(1, 1), (1, 2)]:
    for md in [1, 2, 5]:
        k = f"ngram={ng},min_df={md}"
        res_cfg[k] = cv_f1(X_cru, max_features=mf, ngram_range=ng, min_df=md)
        print(f"  {k}: {res_cfg[k]:.4f}")
melhor = max(res_cfg, key=res_cfg.get)
ng = (1, 2) if "(1, 2)" in melhor else (1, 1)
md = int(melhor.split("min_df=")[1])
base = {"max_features": mf, "ngram_range": ng, "min_df": md}

# 3) pré-processamento (stopwords, max_df, lemas) e classificador (LogReg vs k-NN do notebook)
print("\npré-processamento / classificador")
variantes = {
    "LogReg, texto cru": (X_cru, None, {}),
    "LogReg, cru + stopwords spaCy": (X_cru, None, {"stop_words": STOP}),
    "LogReg, cru + stopwords + max_df=0.8": (X_cru, None, {"stop_words": STOP, "max_df": 0.8}),
    "LogReg, lemas sem stopwords (parte 2)": (X_lem, None, {}),
    "k-NN(k=3), texto cru": (X_cru, KNeighborsClassifier(3), {}),
    "k-NN(k=3), lemas sem stopwords": (X_lem, KNeighborsClassifier(3), {}),
}
res_extra = {}
for nome, (X, clf, kw) in variantes.items():
    res_extra[nome] = cv_f1(X, clf, **base, **kw)
    print(f"  {nome}: {res_extra[nome]:.4f}")

# modelo final: melhor variante de LogReg pelo CV (empate → a mais simples, que vem primeiro)
nome_final = max((n for n in res_extra if n.startswith("LogReg")), key=res_extra.get)
Xf, _, kwf = variantes[nome_final]
final = pipe(**base, **kwf).fit(cortar(Xf, i_tr), ytr)
pred = final.predict(cortar(Xf, i_te))
print(f"\nmodelo final: {nome_final} | {base}")
print(classification_report(yte, pred, digits=3))

json.dump({
    "cv_max_features": res_mf, "cv_config": res_cfg, "cv_extra": res_extra,
    "modelo_final": nome_final,
    "config_final": {**base, "sublinear_tf": True, **{k: ("lista" if k == "stop_words" else v) for k, v in kwf.items()}},
    "teste_f1_macro": f1_score(yte, pred, average="macro"),
    "teste_acuracia": float((pred == yte).mean()),
    "relatorio": classification_report(yte, pred, output_dict=True),
    "matriz_confusao": {"classes": list(final.classes_),
                        "valores": confusion_matrix(yte, pred, labels=final.classes_).tolist()},
    "predicoes_teste": dict(zip(cortar(ids, i_te), pred.tolist())),
}, open(OUT / "resultados_tfidf.json", "w"), indent=1, ensure_ascii=False)

# termos mais pesados por classe (interpretabilidade)
nomes = np.array(final[0].get_feature_names_out())
for c, coef in zip(final[1].classes_, final[1].coef_):
    print(f"{c}: {', '.join(nomes[np.argsort(coef)[-8:][::-1]])}")
