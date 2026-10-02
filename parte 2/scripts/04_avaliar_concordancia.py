"""Itens 2d/e: validação das notas, concordância e CSV final."""
import argparse
import csv
import json
import math
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr
from sklearn.exceptions import UndefinedMetricWarning
from sklearn.metrics import cohen_kappa_score, confusion_matrix

from comum import CORPUS, DADOS, salvar_csv


def ler_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def ler_anotacao(path, pares):
    linhas = ler_csv(path)
    if len(linhas) != 100 or {r.get("id_par") for r in linhas} != set(pares):
        raise ValueError(f"{path.name}: deve conter os 100 IDs, sem repetições.")
    campo_nome = "anotador" if "anotador" in linhas[0] else "aluno"
    if any(r.get("tipo_anotacao", "humana") != "humana" for r in linhas):
        raise ValueError(f"{path.name}: tipo de anotação deve ser humana.")
    nomes = {r.get(campo_nome, "").strip() for r in linhas}
    if len(nomes) != 1 or not next(iter(nomes)):
        raise ValueError(f"{path.name}: preencha {campo_nome} com o mesmo nome/identificador nas 100 linhas.")
    notas = {}
    for r in linhas:
        pid = r["id_par"]
        if (r.get("palavra_1"), r.get("palavra_2")) != (pares[pid]["palavra_1"], pares[pid]["palavra_2"]):
            raise ValueError(f"{path.name}/{pid}: palavras alteradas.")
        nota = r.get("nota", "").strip()
        if nota not in {"1", "2", "3", "4", "5"}:
            raise ValueError(f"{path.name}/{pid}: nota pendente ou inválida; use inteiro de 1 a 5.")
        notas[pid] = int(nota)
    return next(iter(nomes)), notas


def numero_finito(x):
    return float(x) if math.isfinite(float(x)) else None


def concordancia(a, b):
    a, b = np.array(a), np.array(b)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        warnings.simplefilter("ignore", UndefinedMetricWarning)
        kappas = {nome: numero_finito(cohen_kappa_score(a, b, labels=[1, 2, 3, 4, 5], weights=peso))
                  for nome, peso in [("kappa_linear", "linear"), ("kappa_quadratico", "quadratic"), ("kappa_sem_pesos", None)]}
        rho = None if len(set(a)) == 1 or len(set(b)) == 1 else numero_finito(spearmanr(a, b).statistic)
    return dict(kappas, n=len(a), concordancia_exata=float(np.mean(a == b)),
                diferenca_ate_1=float(np.mean(np.abs(a-b) <= 1)),
                diferenca_absoluta_media=float(np.mean(np.abs(a-b))), spearman=rho,
                matriz_confusao=confusion_matrix(a, b, labels=[1, 2, 3, 4, 5]).tolist())


def avaliar(pasta, arquivos):
    if len(arquivos) < 2:
        raise ValueError("São necessários pelo menos dois arquivos de anotadores distintos.")
    lista = ler_csv(pasta / "pares_similaridade.csv")
    pares = {r["id_par"]: r for r in lista}
    if len(lista) != 100 or len(pares) != 100:
        raise ValueError("O arquivo de pares deve conter 100 pares distintos.")
    alunos = [ler_anotacao(path, pares) for path in arquivos]
    if len({nome for nome, _ in alunos}) != len(alunos):
        raise ValueError("Use identificadores diferentes para anotadores distintos.")
    prefixo = "anotador"
    ids = [r["id_par"] for r in lista]
    comparacoes = []
    for (n1, a), (n2, b) in combinations(alunos, 2):
        comparacoes.append({f"{prefixo}_1": n1, f"{prefixo}_2": n2,
                            **concordancia([a[i] for i in ids], [b[i] for i in ids])})
    resultado = []
    for pid in ids:
        r = dict(pares[pid], tipo_anotacao="humana")
        notas = []
        for n, (nome, valores) in enumerate(alunos, 1):
            r.update({f"{prefixo}_{n}": nome, f"nota_{n}": valores[pid]})
            notas.append(valores[pid])
        r.update(similaridade_media=sum(notas)/len(notas), similaridade_mediana=float(np.median(notas)),
                 amplitude=max(notas)-min(notas), revisar="sim" if max(notas)-min(notas) >= 2 else "nao")
        resultado.append(r)
    relatorio = {"status": "anotado",
                 "tipo_anotacao": "humana", "anotadores": len(alunos), "pares": len(ids),
                 "distribuicao_notas": {nome: {str(n): list(notas.values()).count(n) for n in range(1, 6)}
                                        for nome, notas in alunos},
                 "escala": [1, 2, 3, 4, 5], "comparacoes": comparacoes,
                 "pares_para_revisao": [r["id_par"] for r in resultado if r["revisar"] == "sim"],
                 "nota": "null indica estatística indefinida, por exemplo notas constantes; não equivale a zero. "
                         "A concordância usa notas independentes originais, antes de discutir divergências."}
    salvar_csv(pasta / "corpus_similaridade.csv", resultado, list(resultado[0]))
    estatisticas = pasta / "estatisticas"
    estatisticas.mkdir(exist_ok=True)
    (estatisticas / "concordancia_similaridade.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(comparacoes, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pasta", type=Path, default=CORPUS)
    p.add_argument("--anotacoes", nargs="+", type=Path)
    args = p.parse_args()
    arquivos = args.anotacoes or sorted((DADOS / "anotacoes_similaridade").glob("anotador_*.csv"))
    try:
        avaliar(args.pasta, arquivos)
    except (ValueError, OSError) as e:
        p.exit(1, f"Erro: {e}\n")
