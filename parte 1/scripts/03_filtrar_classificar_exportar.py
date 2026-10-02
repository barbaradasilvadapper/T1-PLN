"""Etapa 3 (itens a, d, e, h): filtra, remove duplicatas, classifica por subárea, organiza e exporta.

Entrada: dados/intermediario/questoes_brutas.jsonl
Saídas (pasta corpus/):
  corpus.json                         -> dataset final (metadados + lista de questões)       [item h]
  por_subarea/<subarea>.json          -> mesmas questões agrupadas por subárea e ano           [item e]
  questoes/<subarea>/<ano>/<id>.txt   -> uma questão por arquivo: [ENUNCIADO] [ALTERNATIVAS] [GABARITO]
  corpus.csv                          -> uma linha por questão (para planilha)
  descartadas.json                    -> questões removidas e o motivo                          [item d]
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
from subareas import SUBAREAS, classificar

VERSAO = "1.1"

# Seções de outras matérias. A questão é descartada se estiver numa dessas seções, a menos que a seção
# cite TI/dados/segurança ou que a questão seja claramente de TI (pontuação >= 8, cobre títulos de seção
# que não puderam ser extraídos do PDF).
SECAO_NAO_COMP = re.compile(
    r"portugu|ingl|direito|legisla|racioc|matem|atualidad|hist[oó]ria|geografia|[ée]tica|sustentab|"
    r"administra[cç][aã]o p[uú]blica|administra[cç][aã]o financeira|contab|auditoria governamental|controle externo|"
    r"banc[aá]rio|sus\b|normas espec|organiza[cç][aã]o do minist|filosofia|estat[ií]stica|"
    r"conhecimentos gerais|conhecimentos b[aá]sicos|CONHECIMENTOS (GERAIS|B[AÁ]SICOS)|C ONHECIMENTOS (G|B)", re.I)
SECAO_COMP = re.compile(r"inform[aá]|tecnolog|\bTI\b|T\. ?I\.|seguran[cç]a da informa|dados|sistemas de informa|governan[cç]a", re.I)
SECAO_LINGUA = re.compile(r"l[íi]ngua|portugu|ingl|L[ÍI]NGUA|PORTUGU|INGL", re.I)   # nunca é de TI (sem exceção)
SECAO_ESPECIFICA = re.compile(r"espec[ií]fic|ESPEC", re.I)

PROBLEMAS_QUE_DESCARTAM = {
    "simbolo_nao_convertido": "símbolo de fonte especial não convertido",
    "fragmento_solto": "expoente/índice/tabela quebrados na conversão",
    "alternativas_incompletas": "alternativas faltando",
    "questoes_mescladas": "duas questões grudadas na conversão",
    "alternativa_vazia": "alternativa sem texto",
    "espaco_de_simbolo_perdido": "símbolo perdido (espaço duplo)",
    "caracteres_estranhos": "excesso de caracteres estranhos",
    "enunciado_curto": "enunciado curto/incompleto",
    "depende_de_imagem": "depende de figura/imagem",
    "depende_de_texto_de_outra_questao": "cita texto/tabela que não está no enunciado",
    "alternativa_com_texto_extra": "alternativa com texto de outra questão grudado",
    "sem_gabarito": "sem gabarito",
    "questao_anulada": "questão anulada",
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
    """Quase-duplicatas: mesma questão em provas diferentes do mesmo concurso, às vezes com uma frase
    a mais ou a menos. Candidatas = mesmo início de enunciado OU mesmas alternativas; confirmadas se o
    texto completo tiver similaridade >= 0.9 (difflib)."""

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


def ler_revisao():
    """Rótulos corrigidos à mão (dados/revisao_rotulos.csv). Valem por cima do classificador."""
    with open(DADOS / "revisao_rotulos.csv", encoding="utf-8") as f:
        return {l["id"]: l["subarea_revisada"] for l in csv.DictReader(f)}


def cargo_orgao(slug):
    return re.sub(r"-fgv-\d{4}(-\d+)?$", "", slug).replace("-", " ")


def main():
    brutas = [json.loads(l) for l in open(INTERMEDIARIO / "questoes_brutas.jsonl", encoding="utf-8")]
    boas, descartadas, dedup = [], [], Deduplicador()
    revisao = ler_revisao()
    for r in brutas:
        sec = r["secao"] or ""
        texto = r["enunciado"] + " " + " ".join(r["alternativas"].values())
        secao_de_ti = bool(SECAO_COMP.search(sec) or SECAO_ESPECIFICA.search(sec))
        area, pont = classificar(texto, secao_de_ti)
        origem = "palavras_chave"
        if r["id"] in revisao:
            area, origem = revisao[r["id"]], "revisao_manual"
        motivos = [p for p in r["problemas"] if p in PROBLEMAS_QUE_DESCARTAM]
        if SECAO_LINGUA.search(sec) or (SECAO_NAO_COMP.search(sec) and not SECAO_COMP.search(sec) and max(pont.values()) < 8):
            motivos.append("fora_de_computacao_secao")
        elif area == "fora_de_computacao":
            motivos.append("fora_de_computacao_revisao_manual")
        elif area is None:
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
        q = {"id": r["id"], "subarea": area, "origem_subarea": origem, "ano": r["ano"], "banca": r["banca"], "cargo_orgao": cargo_orgao(slug),
             "prova": r["prova"], "url_prova": r["url"], "numero_na_prova": r["numero"], "secao_na_prova": r["secao"],
             "enunciado": r["enunciado"],
             "alternativas": [{"letra": l, "texto": t} for l, t in r["alternativas"].items()],
             "gabarito": r["gabarito"], "resposta_correta": r["alternativas"][r["gabarito"]],
             "tambem_em": [], "pontuacao_subareas": pont}
        dedup.registrar(r, q)
        boas.append(q)

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
            "subarea": "classe atribuída pelo classificador de palavras-chave (scripts/subareas.py) ou pela revisão manual",
            "origem_subarea": "palavras_chave ou revisao_manual (dados/revisao_rotulos.csv)",
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

    # recria as pastas de saída do zero (evita arquivos de execuções anteriores)
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
