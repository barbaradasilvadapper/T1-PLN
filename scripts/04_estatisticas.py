"""Etapa 4 (item g): estatísticas do corpus.

Entrada: corpus/corpus.json, corpus/descartadas.json, dados/intermediario/questoes_brutas.jsonl
         corpus/qualidade_lexica.json (opcional, gerado por 04b_qualidade_lexica.py)
Saída  : corpus/estatisticas/estatisticas.json   (todos os números)
         corpus/estatisticas/ESTATISTICAS.md      (tabelas legíveis)
         corpus/estatisticas/*.png                (gráficos)

Tokenização: sequências de letras/dígitos, com hífen, ponto ou apóstrofo internos
("sub-rede", "802.11", "d'água" = 1 token). Pontuação não conta como token. Types = tokens distintos
em minúsculas. Texto de uma questão = enunciado + alternativas.
"""
import json
import re
import statistics as st
from collections import Counter, defaultdict

from comum import CORPUS, INTERMEDIARIO

TOKEN = re.compile(r"\w+(?:[-.'’]\w+)*")
STOPWORDS = set("""a à ao aos as às o os um uma uns umas de da das do dos em na nas no nos por pela pelas pelo pelos
para com sem sob sobre entre e ou que se é são foi ser está estão como mais menos não sua seu suas seus ele ela
eles elas isso este esta esse essa estes essas esses aquele aquela qual quais quando onde já também apenas cada
mesmo muito pode podem deve devem ter tem têm há seguir seguinte seguintes assinale opção afirmativa afirmativas
correta correto corretas corretos analise considere item itens i ii iii iv v f caso forma exemplo sendo
respectivamente acordo relação contexto termos todos todas ainda outro outra outros outras dessa desse deste desta
nessa nesse neste nesta ao lhe lo la""".split())
NOMES = {
    "engenharia_de_software_e_programacao": "Eng. Software e Programação",
    "banco_de_dados_e_ciencia_de_dados": "Banco de Dados e Ciência de Dados",
    "redes_e_infraestrutura": "Redes e Infraestrutura",
    "seguranca_da_informacao": "Segurança da Informação",
    "governanca_e_gestao_de_ti": "Governança e Gestão de TI",
}
AZUL, TEXTO, TEXTO2, FUNDO, GRADE = "#2a78d6", "#0b0b0b", "#52514e", "#fcfcfb", "#e4e3df"


def texto(q):
    return q["enunciado"] + " " + " ".join(a["texto"] for a in q["alternativas"])


def toks(t):
    return TOKEN.findall(t)


def resumo(valores):
    return {"media": round(st.mean(valores), 2), "mediana": st.median(valores), "desvio_padrao": round(st.pstdev(valores), 2),
            "minimo": min(valores), "maximo": max(valores)}


def estatisticas():
    corpus = json.load(open(CORPUS / "corpus.json", encoding="utf-8"))
    qs = corpus["questoes"]
    descartadas = json.load(open(CORPUS / "descartadas.json", encoding="utf-8"))
    brutas = [json.loads(l) for l in open(INTERMEDIARIO / "questoes_brutas.jsonl", encoding="utf-8")]

    tok_q = {q["id"]: toks(texto(q)) for q in qs}
    todos = [t for q in qs for t in tok_q[q["id"]]]
    types = Counter(t.lower() for t in todos)
    comp = [len(tok_q[q["id"]]) for q in qs]
    maior = max(qs, key=lambda q: len(tok_q[q["id"]]))
    menor = min(qs, key=lambda q: len(tok_q[q["id"]]))

    por_area = defaultdict(list)
    for q in qs:
        por_area[q["subarea"]].append(q)
    anos = sorted({q["ano"] for q in qs})
    areas = sorted(por_area, key=lambda a: -len(por_area[a]))

    E = {
        "geral": {
            "provas_utilizadas": len({q["prova"] for q in brutas}),
            "questoes_extraidas_dos_pdfs": len(brutas),
            "questoes_no_corpus": len(qs),
            "questoes_descartadas": len(descartadas),
            "total_tokens": len(todos),
            "total_types": len(types),
            "razao_type_token": round(len(types) / len(todos), 4),
            "tokens_por_questao": resumo(comp),
            "tokens_enunciado": resumo([len(toks(q["enunciado"])) for q in qs]),
            "tokens_por_alternativa": resumo([len(toks(a["texto"])) for q in qs for a in q["alternativas"]]),
            "maior_questao": {"id": maior["id"], "tokens": len(tok_q[maior["id"]])},
            "menor_questao": {"id": menor["id"], "tokens": len(tok_q[menor["id"]])},
            "questoes_com_4_alternativas": sum(1 for q in qs if len(q["alternativas"]) == 4),
            "questoes_com_5_alternativas": sum(1 for q in qs if len(q["alternativas"]) == 5),
            "questoes_repetidas_em_outras_provas": sum(1 for q in qs if q["tambem_em"]),
        },
        "por_subarea": {},
        "por_ano": {str(y): sum(1 for q in qs if q["ano"] == y) for y in anos},
        "subarea_x_ano": {a: {str(y): sum(1 for q in por_area[a] if q["ano"] == y) for y in anos} for a in areas},
        "gabarito": dict(sorted(Counter(q["gabarito"] for q in qs).items())),
        "motivos_de_descarte": dict(Counter(m for d in descartadas for m in d["motivos"]).most_common()),
        "questoes_por_prova": dict(sorted(Counter(q["prova"] for q in qs).items())),
    }
    for a in areas:
        t = [x for q in por_area[a] for x in tok_q[q["id"]]]
        c = [len(tok_q[q["id"]]) for q in por_area[a]]
        freq = Counter(x.lower() for x in t if x.lower() not in STOPWORDS and not x.isdigit() and len(x) > 2)
        E["por_subarea"][a] = {
            "nome": NOMES[a], "questoes": len(por_area[a]),
            "percentual": round(100 * len(por_area[a]) / len(qs), 1),
            "tokens": len(t), "types": len({x.lower() for x in t}), "tokens_por_questao": resumo(c),
            "termos_mais_frequentes": [w for w, _ in freq.most_common(15)],
        }
    qual = CORPUS / "qualidade_lexica.json"
    if qual.exists():
        E["qualidade_lexica"] = json.load(open(qual, encoding="utf-8"))
    return E


def graficos(E, pasta):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRADE, "axes.labelcolor": TEXTO2, "xtick.color": TEXTO2,
                         "ytick.color": TEXTO2, "figure.facecolor": FUNDO, "axes.facecolor": FUNDO,
                         "axes.spines.top": False, "axes.spines.right": False})

    # 1. questões por subárea (barras horizontais, rótulo direto, linha de referência em 500)
    areas = list(E["por_subarea"])
    vals = [E["por_subarea"][a]["questoes"] for a in areas]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    y = range(len(areas))[::-1]
    ax.barh(list(y), vals, color=AZUL, height=0.6)
    ax.axvline(500, color=TEXTO2, lw=1, ls="--")
    ax.text(503, len(areas) - 0.45, "mínimo exigido (500)", color=TEXTO2, fontsize=8, va="bottom")
    for yi, v in zip(y, vals):
        ax.text(v + 8, yi, str(v), va="center", color=TEXTO, fontsize=9)
    ax.set_yticks(list(y), [E["por_subarea"][a]["nome"] for a in areas])
    ax.set_xlabel("questões")
    ax.set_title("Questões por subárea", loc="left", color=TEXTO)
    ax.xaxis.grid(True, color=GRADE, lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(pasta / "questoes_por_subarea.png", dpi=150)
    plt.close(fig)

    # 2. mapa de calor subárea x ano (escala sequencial de azuis, valores anotados)
    anos = list(E["por_ano"])
    M = [[E["subarea_x_ano"][a][y] for y in anos] for a in areas]
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("azuis", ["#cde2fb", "#86b6ef", "#2a78d6", "#184f95"])
    fig, ax = plt.subplots(figsize=(8, 3.4))
    im = ax.imshow(M, cmap=cmap, aspect="auto")
    vmax = max(max(r) for r in M)
    for i, r in enumerate(M):
        for j, v in enumerate(r):
            ax.text(j, i, str(v), ha="center", va="center", fontsize=9, color="white" if v > 0.55 * vmax else TEXTO)
    ax.set_xticks(range(len(anos)), anos)
    ax.set_yticks(range(len(areas)), [E["por_subarea"][a]["nome"] for a in areas])
    ax.set_title("Questões por subárea e ano da prova", loc="left", color=TEXTO)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    fig.tight_layout()
    fig.savefig(pasta / "subarea_por_ano.png", dpi=150)
    plt.close(fig)

    # 3. histograma do tamanho das questões em tokens
    corpus = json.load(open(CORPUS / "corpus.json", encoding="utf-8"))["questoes"]
    comp = [len(toks(texto(q))) for q in corpus]
    fig, ax = plt.subplots(figsize=(8, 3.4))
    ax.hist(comp, bins=40, color=AZUL, edgecolor=FUNDO, linewidth=1)
    med = E["geral"]["tokens_por_questao"]["media"]
    ax.axvline(med, color=TEXTO2, lw=1, ls="--")
    ax.text(med + 5, ax.get_ylim()[1] * 0.92, f"média = {med:.0f} tokens", color=TEXTO2, fontsize=8)
    ax.set_xlabel("tokens por questão (enunciado + alternativas)")
    ax.set_ylabel("questões")
    ax.set_title("Distribuição do tamanho das questões", loc="left", color=TEXTO)
    ax.yaxis.grid(True, color=GRADE, lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(pasta / "tamanho_das_questoes.png", dpi=150)
    plt.close(fig)

    # 4. distribuição do gabarito
    g = E["gabarito"]
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar(list(g), list(g.values()), color=AZUL, width=0.6)
    for k, v in g.items():
        ax.text(k, v + 5, str(v), ha="center", color=TEXTO, fontsize=9)
    ax.set_title("Letra correta no gabarito", loc="left", color=TEXTO)
    ax.set_ylabel("questões")
    ax.yaxis.grid(True, color=GRADE, lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(pasta / "distribuicao_gabarito.png", dpi=150)
    plt.close(fig)


def markdown(E):
    g = E["geral"]
    L = ["# Estatísticas do corpus", "",
         "| Medida | Valor |", "|---|---:|",
         f"| Provas utilizadas | {g['provas_utilizadas']} |",
         f"| Questões extraídas dos PDFs | {g['questoes_extraidas_dos_pdfs']} |",
         f"| Questões no corpus | {g['questoes_no_corpus']} |",
         f"| Questões descartadas | {g['questoes_descartadas']} |",
         f"| Total de tokens | {g['total_tokens']:,} |".replace(",", "."),
         f"| Total de types | {g['total_types']:,} |".replace(",", "."),
         f"| Razão type/token | {g['razao_type_token']} |",
         f"| Tokens por questão (média ± dp) | {g['tokens_por_questao']['media']} ± {g['tokens_por_questao']['desvio_padrao']} |",
         f"| Tokens por questão (mediana) | {g['tokens_por_questao']['mediana']} |",
         f"| Maior questão | {g['maior_questao']['tokens']} tokens ({g['maior_questao']['id']}) |",
         f"| Menor questão | {g['menor_questao']['tokens']} tokens ({g['menor_questao']['id']}) |",
         f"| Tokens no enunciado (média) | {g['tokens_enunciado']['media']} |",
         f"| Tokens por alternativa (média) | {g['tokens_por_alternativa']['media']} |",
         f"| Questões com 5 / 4 alternativas | {g['questoes_com_5_alternativas']} / {g['questoes_com_4_alternativas']} |"]
    if "qualidade_lexica" in E:
        q = E["qualidade_lexica"]
        L.append(f"| Qualidade léxica (tokens reconhecidos em dicionário pt+en) | {q['proporcao_reconhecida']:.1%} |")
    L += ["", "## Por subárea", "", "| Subárea | Questões | % | Tokens | Types | Tokens/questão (média) |",
          "|---|---:|---:|---:|---:|---:|"]
    for a, s in E["por_subarea"].items():
        L.append(f"| {s['nome']} | {s['questoes']} | {s['percentual']} | {s['tokens']} | {s['types']} | "
                 f"{s['tokens_por_questao']['media']} |")
    anos = list(E["por_ano"])
    L += ["", "## Subárea × ano", "", "| Subárea | " + " | ".join(anos) + " | Total |", "|---|" + "---:|" * (len(anos) + 1)]
    for a, s in E["por_subarea"].items():
        L.append(f"| {s['nome']} | " + " | ".join(str(E['subarea_x_ano'][a][y]) for y in anos) + f" | {s['questoes']} |")
    L.append("| **Total** | " + " | ".join(str(E["por_ano"][y]) for y in anos) + f" | {g['questoes_no_corpus']} |")
    L += ["", "## Termos mais frequentes por subárea (sem stopwords)", ""]
    for a, s in E["por_subarea"].items():
        L.append(f"- **{s['nome']}**: {', '.join(s['termos_mais_frequentes'])}")
    L += ["", "## Distribuição do gabarito", "", "| " + " | ".join(E["gabarito"]) + " |",
          "|" + "---:|" * len(E["gabarito"]), "| " + " | ".join(str(v) for v in E["gabarito"].values()) + " |",
          "", "## Motivos de descarte (uma questão pode ter mais de um)", "", "| Motivo | Questões |", "|---|---:|"]
    L += [f"| {m} | {n} |" for m, n in E["motivos_de_descarte"].items()]
    L += ["", "## Gráficos", "", "![](questoes_por_subarea.png)", "", "![](subarea_por_ano.png)", "",
          "![](tamanho_das_questoes.png)", "", "![](distribuicao_gabarito.png)", ""]
    return "\n".join(L)


def main():
    pasta = CORPUS / "estatisticas"
    pasta.mkdir(parents=True, exist_ok=True)
    E = estatisticas()
    json.dump(E, open(pasta / "estatisticas.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    (pasta / "ESTATISTICAS.md").write_text(markdown(E), encoding="utf-8")
    graficos(E, pasta)
    g = E["geral"]
    print(f"{g['questoes_no_corpus']} questões | {g['total_tokens']} tokens | {g['total_types']} types")
    for a, s in E["por_subarea"].items():
        print(f"  {s['nome']}: {s['questoes']}")


if __name__ == "__main__":
    main()
