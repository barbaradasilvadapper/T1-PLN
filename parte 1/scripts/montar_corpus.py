"""Monta o corpus final a partir das questões extraídas (dados/intermediario/questoes_brutas.jsonl).

Descarta as questões que não são de computação, que tiveram problema na conversão, que não têm gabarito
ou que são repetidas, define a subárea de cada uma e grava em corpus/:
  corpus.json        corpus final (metadados + lista de questões)
  corpus.csv         uma linha por questão
  por_subarea/       as mesmas questões separadas por subárea e agrupadas por ano
  questoes/          um .txt por questão, em pastas de subárea e ano
  descartadas.json   as questões removidas e o motivo
"""
import csv
import difflib
import shutil
import json
import re
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from comum import CORPUS, DADOS, INTERMEDIARIO, norm
from subareas import SUBAREAS, eh_de_computacao, refinar

VERSAO = "1.1"

# Seções de outras matérias. A questão dessas seções é descartada, a não ser que o título da seção fale de
# TI ou que a questão tenha muitos termos de TI (8 pontos ou mais; acontece quando o título da seção não
# foi extraído direito do PDF).
SECAO_NAO_COMP = re.compile(
    r"portugu|ingl|direito|legisla|racioc|matem|atualidad|hist[oó]ria|geografia|[ée]tica|sustentab|"
    r"administra[cç][aã]o p[uú]blica|administra[cç][aã]o financeira|contab|auditoria governamental|controle externo|"
    r"banc[aá]rio|sus\b|normas espec|organiza[cç][aã]o do minist|filosofia|estat[ií]stica|"
    r"conhecimentos gerais|conhecimentos b[aá]sicos|CONHECIMENTOS (GERAIS|B[AÁ]SICOS)|C ONHECIMENTOS (G|B)", re.I)
SECAO_COMP = re.compile(r"inform[aá]|tecnolog|\bTI\b|T\. ?I\.|seguran[cç]a da informa|dados|sistemas de informa|governan[cç]a", re.I)
SECAO_LINGUA = re.compile(r"l[íi]ngua|portugu|ingl|L[ÍI]NGUA|PORTUGU|INGL", re.I)   # sempre descartada
SECAO_ESPECIFICA = re.compile(r"espec[ií]fic|ESPEC", re.I)

# problemas marcados pelo extrair_questoes.py que fazem a questão ser descartada
PROBLEMAS_QUE_DESCARTAM = {
    "simbolo_nao_convertido", "fragmento_solto", "alternativas_incompletas", "questoes_mescladas",
    "alternativa_vazia", "espaco_de_simbolo_perdido", "caracteres_estranhos", "enunciado_curto",
    "depende_de_imagem", "depende_de_texto_de_outra_questao", "alternativa_com_texto_extra",
    "sem_gabarito", "questao_anulada",
}

NOMES_SUBAREAS = {
    "engenharia_de_software_e_programacao": "Engenharia de Software e Programação",
    "banco_de_dados_e_ciencia_de_dados": "Banco de Dados e Ciência de Dados",
    "redes_e_infraestrutura": "Redes, Sistemas Operacionais e Infraestrutura",
    "seguranca_da_informacao": "Segurança da Informação",
    "governanca_e_gestao_de_ti": "Governança e Gestão de TI",
}


def _n(t):
    return re.sub(r"\W+", "", norm(t))


class Deduplicador:
    """Acha questões repetidas: a mesma questão aparece em provas diferentes do mesmo concurso, às vezes
    com uma frase a mais ou a menos. Comparamos só as questões com o mesmo começo de enunciado ou as mesmas
    alternativas, e consideramos repetida quando o texto inteiro é pelo menos 90% igual (difflib)."""

    def __init__(self):
        self.por_chave = {}

    def verificar(self, r):
        texto = _n(r["enunciado"] + " ".join(r["alternativas"].values()))
        chaves = [("e", _n(r["enunciado"])[:150]), ("a", _n("|".join(r["alternativas"].values())))]
        for k in chaves:
            for texto_ant, q_ant in self.por_chave.get(k, []):
                if difflib.SequenceMatcher(None, texto, texto_ant, autojunk=False).ratio() >= 0.9:
                    return q_ant
        return None

    def registrar(self, r, q):
        texto = _n(r["enunciado"] + " ".join(r["alternativas"].values()))
        for k in [("e", _n(r["enunciado"])[:150]), ("a", _n("|".join(r["alternativas"].values())))]:
            self.por_chave.setdefault(k, []).append((texto, q))


def validar(questoes):
    """Mostra o acerto da subárea nas questões conferidas à mão (dados/validacao_rotulos.csv).
    Esse arquivo só serve para medir; nenhum rótulo do corpus vem dele."""
    subarea = {q["id"]: q["subarea"] for q in questoes}
    with open(DADOS / "validacao_rotulos.csv", encoding="utf-8") as f:
        conferidas = list(csv.DictReader(f))
    for conjunto in ["amostra_aleatoria", "questoes_dificeis"]:
        linhas = [l for l in conferidas if l["conjunto"] == conjunto]
        acertos = sum(subarea.get(l["id"]) == l["subarea_correta"] for l in linhas)
        print(f"validação ({conjunto}): {acertos}/{len(linhas)} = {acertos / len(linhas):.1%}")


def cargo_orgao(slug):
    return re.sub(r"-fgv-\d{4}(-\d+)?$", "", slug).replace("-", " ")


def main():
    brutas = [json.loads(l) for l in open(INTERMEDIARIO / "questoes_brutas.jsonl", encoding="utf-8")]
    boas, descartadas, dedup = [], [], Deduplicador()
    for r in brutas:
        sec = r["secao"] or ""
        texto = r["enunciado"] + " " + " ".join(r["alternativas"].values())
        secao_de_ti = bool(SECAO_COMP.search(sec) or SECAO_ESPECIFICA.search(sec))
        computacao, pont = eh_de_computacao(texto, secao_de_ti)
        motivos = [p for p in r["problemas"] if p in PROBLEMAS_QUE_DESCARTAM]
        if SECAO_LINGUA.search(sec) or (SECAO_NAO_COMP.search(sec) and not SECAO_COMP.search(sec) and max(pont.values()) < 8):
            motivos.append("fora_de_computacao_secao")
        elif not computacao:
            motivos.append("fora_de_computacao_sem_termos_de_TI")
        original = dedup.verificar(r) if not motivos else None
        if original is not None:
            motivos.append("duplicada")
            original["tambem_em"].append(r["id"])
        if motivos:
            descartadas.append({"id": r["id"], "prova": r["prova"], "numero": r["numero"], "secao": r["secao"],
                                "motivos": motivos, "enunciado": r["enunciado"], "alternativas": r["alternativas"],
                                "gabarito": r["gabarito"], "pontuacao_subareas": pont})
            continue
        slug = r["prova"][3:]
        q = {"id": r["id"], "subarea": None, "origem_subarea": None, "ano": r["ano"], "banca": r["banca"], "cargo_orgao": cargo_orgao(slug),
             "prova": r["prova"], "url_prova": r["url"], "numero_na_prova": r["numero"], "secao_na_prova": r["secao"],
             "enunciado": r["enunciado"],
             "alternativas": [{"letra": l, "texto": t} for l, t in r["alternativas"].items()],
             "gabarito": r["gabarito"], "resposta_correta": r["alternativas"][r["gabarito"]],
             "tambem_em": [], "pontuacao_subareas": pont}
        dedup.registrar(r, q)
        boas.append(q)

    subareas, origens = refinar(boas)
    for q, subarea, origem in zip(boas, subareas, origens):
        q["subarea"] = subarea
        q["origem_subarea"] = origem
    validar(boas)

    boas.sort(key=lambda q: (q["subarea"], q["ano"], q["id"]))
    CORPUS.mkdir(exist_ok=True)
    por_area = defaultdict(lambda: defaultdict(list))
    for q in boas:
        por_area[q["subarea"]][q["ano"]].append(q)

    metadados = {
        "nome": "QuestõesTI-FGV", "versao": VERSAO, "data": datetime.now(ZoneInfo("America/Sao_Paulo")).date().isoformat(),
        "descricao": "Questões de múltipla escolha de concursos públicos de TI (banca FGV, 2021-2026), "
                     "com enunciado, alternativas, gabarito e subárea.",
        "fonte": "https://www.pciconcursos.com.br/provas/ti/", "idioma": "pt-BR",
        "total_questoes": len(boas),
        "subareas": {a: {"nome": NOMES_SUBAREAS[a], "questoes": sum(len(v) for v in por_area[a].values())}
                     for a in SUBAREAS},
        "campos": {
            "id": "NN-QQQ: NN = nº da pasta da prova em dados/pdfs, QQQ = nº da questão na prova",
            "subarea": "classe atribuída por scripts/subareas.py (palavras-chave + k-NN treinado nas sementes)",
            "origem_subarea": "palavras_chave (margem >= 4) ou knn (questão ambígua)",
            "ano": "ano de aplicação da prova", "banca": "banca organizadora",
            "cargo_orgao": "cargo e órgão do concurso", "prova": "pasta da prova em dados/pdfs",
            "url_prova": "página da prova no PCI Concursos", "numero_na_prova": "número da questão no caderno",
            "secao_na_prova": "título da seção do caderno onde a questão aparece",
            "enunciado": "texto do enunciado (sem as alternativas)",
            "alternativas": "lista de {letra, texto}", "gabarito": "letra correta (gabarito oficial FGV, Tipo 1)",
            "resposta_correta": "texto da alternativa correta",
            "tambem_em": "ids de questões idênticas em outras provas (removidas como duplicatas)",
            "pontuacao_subareas": "pontuação do classificador para cada subárea"},
    }
    with open(CORPUS / "corpus.json", "w", encoding="utf-8") as f:
        json.dump({"metadados": metadados, "questoes": boas}, f, ensure_ascii=False, indent=2)

    # apaga as pastas antes, para não sobrar arquivo de uma execução anterior
    for pasta in ("por_subarea", "questoes"):
        shutil.rmtree(CORPUS / pasta, ignore_errors=True)
    (CORPUS / "por_subarea").mkdir(exist_ok=True)
    for a, anos in por_area.items():
        with open(CORPUS / "por_subarea" / f"{a}.json", "w", encoding="utf-8") as f:
            json.dump({"subarea": a, "nome": NOMES_SUBAREAS[a], "total": sum(len(v) for v in anos.values()),
                       "anos": {str(y): anos[y] for y in sorted(anos)}}, f, ensure_ascii=False, indent=2)
        for y, qs in anos.items():
            d = CORPUS / "questoes" / a / str(y)
            d.mkdir(parents=True, exist_ok=True)
            for q in qs:
                alts = "\n".join(f"({x['letra']}) {x['texto']}" for x in q["alternativas"])
                (d / f"{q['id']}.txt").write_text(
                    f"ID: {q['id']}\nANO: {q['ano']}\nBANCA: {q['banca']}\nCARGO/ÓRGÃO: {q['cargo_orgao']}\n"
                    f"SUBÁREA: {NOMES_SUBAREAS[a]}\n\n[ENUNCIADO]\n{q['enunciado']}\n\n[ALTERNATIVAS]\n{alts}\n\n"
                    f"[GABARITO]\n{q['gabarito']}\n", encoding="utf-8")

    campos = ["id", "subarea", "ano", "banca", "cargo_orgao", "numero_na_prova", "enunciado", "A", "B", "C", "D", "E",
              "gabarito", "url_prova"]
    with open(CORPUS / "corpus.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for q in boas:
            alts = {x["letra"]: x["texto"] for x in q["alternativas"]}
            w.writerow({**{c: q.get(c, "") for c in campos if c not in "ABCDE"}, **{l: alts.get(l, "") for l in "ABCDE"}})

    with open(CORPUS / "descartadas.json", "w", encoding="utf-8") as f:
        json.dump(descartadas, f, ensure_ascii=False, indent=2)

    print(f"{len(brutas)} extraídas | {len(boas)} no corpus | {len(descartadas)} descartadas")
    for a in SUBAREAS:
        print(f"  {a}: {sum(len(v) for v in por_area[a].values())}")


if __name__ == "__main__":
    main()
