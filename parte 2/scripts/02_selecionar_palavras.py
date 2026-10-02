"""Passo 2 (item 2a.ii): selecionar os 200 lemas representativos por TF-IDF."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer

from comum import CORPUS, QUESTOES_LEMATIZADAS, salvar_csv


def selecionar(origem, saida):
    if saida.exists():
        raise ValueError("Ranking já existe. Use outra --saida para preservá-lo.")
    with origem.open(encoding="utf-8") as f:
        questoes = [json.loads(linha) for linha in f if linha.strip()]
    documentos = []
    frequencias, formas, contextos = Counter(), defaultdict(Counter), defaultdict(list)
    for q in questoes:
        lemas = q["lemas"]
        if len(lemas) != len(q["formas"]):
            raise ValueError(f"Questão {q['id']}: lemas e formas com tamanhos diferentes.")
        frequencias.update(lemas)
        for lema, forma in zip(lemas, q["formas"]):
            formas[lema][forma] += 1
        for lema in sorted(set(lemas)):
            if len(contextos[lema]) < 3:
                contextos[lema].append(q["id"])
        documentos.append(" ".join(lemas))
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
    saida.parent.mkdir(parents=True, exist_ok=True)
    salvar_csv(saida, ranking, list(ranking[0]))
    print(f"200 palavras selecionadas por TF-IDF. Saída: {saida}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--origem", type=Path, default=QUESTOES_LEMATIZADAS)
    p.add_argument("--saida", type=Path, default=CORPUS / "palavras_similaridade.csv")
    args = p.parse_args()
    try:
        selecionar(args.origem, args.saida)
    except (ValueError, OSError) as e:
        p.exit(1, f"Erro: {e}\n")
