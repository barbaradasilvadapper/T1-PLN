"""Etapa 2 (itens d, e, f): separa as questões (enunciado x alternativas), identifica a seção da
prova, junta o gabarito e marca questões com problemas de conversão.

Entrada: dados/txt/NN_slug/{prova.txt, gabarito.txt}, dados/gabaritos_manuais/NN.txt
Saída  : dados/intermediario/questoes_brutas.jsonl  (todas as questões, com a lista de problemas)
         dados/intermediario/relatorio_extracao.csv (por prova: nº de questões, bloco de gabarito usado)
"""
import csv
import json
import re
from collections import Counter

from comum import GABARITOS_MANUAIS, INTERMEDIARIO, TXT, pastas_de_provas
from gabarito import blocos, escolher

# Provas cujo gabarito publicado no PCI é de OUTRO cargo (conferido manualmente) -> sem gabarito
GABARITO_INVALIDO = {"53": "o arquivo do PCI traz só o gabarito dos cargos de Técnico, não o de Analista de TI"}

ALT = re.compile(r"^\(([A-E])\)\s*(.*)$")

# Fontes Symbol/Wingdings viram caracteres da área de uso privado (U+F0xx) -> mapeia os inequívocos
SIMBOLOS = {"": " ", "": "•", "": "•", "": "▪", "": "→", "": "←",
            "": "≥", "": "≤", "": "≠", "": "×", "": "÷", "": "⇒",
            "": "⇔", "": "±", "": "∞", "": "√", "": "∑", "": "∈"}
PUA = re.compile(r"[-�□]")

TITULO = re.compile(
    r"^(M\s?[ÓO]DULO\b|C\s?ONHECIMENTOS\b|Conhecimentos\b|L[ÍI]NGUA\b|L[íi]ngua\b|Racioc[íi]nio|RACIOC|"
    r"Legisla[çc][ãa]o|LEGISLA|No[çc][õo]es|NO[ÇC][ÕO]ES|Direitos?\b|DIREITO|Hist[óo]ria|Matem[áa]tica|Atualidades|[ÉE]tica\b|"
    r"Governan[çc]a|Seguran[çc]a da Informa[çc][ãa]o|Arquitetura de Sistemas|Engenharia de Software|Banco de Dados|"
    r"Fundamentos de|Controle Externo|Auditoria|Administra[çc][ãa]o|Filosofia|Estat[íi]stica|Normas|Organiza[çc][ãa]o do|"
    r"T\. ?I\. ?-|Processos de Neg|Desenvolvimento de Sistemas|Infraestrutura|Redes de Computadores|Ci[êe]ncia de Dados)")


# início de um texto/tabela/código compartilhado por várias questões (vem antes da próxima questão e,
# na conversão, fica grudado na última alternativa da questão anterior)
CONTEXTO = re.compile(r"^(READ THE TEXT|Read the text|Leia o texto|Texto\s+(\d+|[IVX]+)\b|Tabela\s+\d+\b|"
                      r"Considere .{0,80}\b(nas|para as|às) (duas|tr[êe]s|quatro|pr[óo]ximas) quest|"
                      r"As quest[õo]es \d+|Utilize .{0,60}quest|Com base no texto a seguir|Atenção:)")
# enunciado que se refere a um texto/tabela que não está nele
REF_EXTERNA = re.compile(r"descrit[oa]s? anteriormente|apresentad[oa]s? anteriormente|(no|do|pelo) texto \d|"
                         r"(na|da|pela) tabela \d|situação descrita no texto|quest[ãa]o anterior|mesmo cen[áa]rio", re.I)


def mapear_simbolos(t):
    for k, v in SIMBOLOS.items():
        t = t.replace(k, v)
    return t


def limpar_cabecalhos(linhas):
    """Remove cabeçalhos/rodapés de página (nome do órgão/cargo repetido, 'Tipo 1 Branca – Página 8')."""
    freq = Counter(l for l in linhas if not ALT.match(l) and not l.isdigit())
    out = []
    for l in linhas:
        if l == "\f":
            out.append(l)
            continue
        if re.search(r"(Tipo|Prova)\s*\d.*P[áa]gina\s*\d+|^P[áa]gina\s*\d+|TIPO .*P[ÁA]GINA \d+|^Realização$", l, re.I):
            continue
        if freq[l] >= 4 and len(l) > 15:
            continue
        out.append(l)
    return out


def eh_cabecalho_de_secao(l, anterior):
    return (bool(TITULO.match(l)) and len(l) <= 70 and not re.search(r"[.:;?,)(]", l) and len(l.split()) <= 8
            and not re.search(r"\s(é|são|que|foi|pelo|pela|utilizado|utilizada|publicado|podem|pode)\b", l)
            and (anterior is None or anterior == "\f"
                 or re.search(r"[.;:!?)”\"]$|^\d+$|^\(E\)|P[ÁA]GINA|Página|^[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9 ()/–-]+$", anterior)))


def separar(texto):
    brutas = []
    for l in texto.split("\n"):
        if "\f" in l:
            brutas.append("\f")
            l = l.replace("\f", "")
        l = l.strip()
        if l and not re.fullmatch(r"[-\s]+", l):     # ícones de rodapé (Wingdings)
            brutas.append(l)
    linhas = limpar_cabecalhos(brutas)
    total_A = sum(1 for l in linhas if l.startswith("(A)"))

    # número colado no fim da linha anterior ("...réus.8") -> separa
    sep = []
    for l in linhas:
        m = re.match(r"^(.*[.;:)”\"?!])(\d{1,3})$", l)
        if m and len(m.group(1)) > 3:
            sep += [m.group(1), m.group(2)]
        else:
            sep.append(l)
    linhas = sep

    # títulos de seção (cada questão herda o último título anterior a ela)
    titulos, linhas_de_titulo = {}, set()
    for i, l in enumerate(linhas):
        if eh_cabecalho_de_secao(l, linhas[i - 1] if i else None):
            t, prox = l, (linhas[i + 1] if i + 1 < len(linhas) else "")
            if (re.search(r"\s(e|de|do|da|dos|das|em)$", l, re.I) or prox[:1].islower()) and len(prox) < 60 \
                    and not re.search(r"[.:;?]$", prox):
                t += " " + prox                               # título quebrado em duas linhas
                linhas_de_titulo.add(i + 1)
            titulos[i] = t
            linhas_de_titulo.add(i)
    pos_tit = sorted(titulos)

    # início de questão: linha só com o número esperado (tolera até 2 números ausentes)
    # e com um "(A)" antes do próximo número
    inicios, esperado = [], 1
    for i, l in enumerate(linhas):
        if not l.isdigit():
            continue
        k = int(l)
        if not (esperado <= k <= esperado + 2):
            continue
        for j in range(i + 1, min(i + 400, len(linhas))):
            if linhas[j].isdigit() and int(linhas[j]) == k + 1:
                break
            if linhas[j].startswith("(A)"):
                inicios.append((k, i))
                esperado = k + 1
                break

    questoes, contexto_pendente = [], []
    for idx, (num, i) in enumerate(inicios):
        fim = inicios[idx + 1][1] if idx + 1 < len(inicios) else len(linhas)
        corpo = [linhas[k] for k in range(i + 1, fim) if linhas[k] != "\f" and k not in linhas_de_titulo]
        anteriores = [k for k in pos_tit if k < i]
        secao = titulos[anteriores[-1]] if anteriores else None
        enun, alts, atual, mesclada = [], {}, None, False
        for l in corpo:
            m = ALT.match(l)
            if m and ((atual is None and m.group(1) == "A") or (atual and ord(m.group(1)) == ord(atual) + 1)):
                atual = m.group(1)
                alts[atual] = [m.group(2)] if m.group(2) else []
            elif atual:
                if m:
                    mesclada = True
                alts[atual].append(l)
            else:
                enun.append(l)
        # texto compartilhado grudado na última alternativa -> vai para o enunciado da próxima questão
        contexto_proxima = []
        if atual:
            for k, l in enumerate(alts[atual]):
                if CONTEXTO.match(l):
                    contexto_proxima = alts[atual][k:]
                    alts[atual] = alts[atual][:k]
                    break
        recebeu_contexto = bool(contexto_pendente)
        enun = contexto_pendente + enun
        contexto_pendente = contexto_proxima
        # título de subseção grudado no fim da última alternativa (ex.: "...serviço." + "Serviços de Nuvem")
        if atual and len(alts[atual]) >= 2:
            ult, penult = alts[atual][-1], alts[atual][-2]
            if (re.search(r"[.;]$", penult) and ult[:1].isupper() and not re.search(r"[.;:?!,)]$", ult)
                    and len(ult.split()) <= 7 and re.fullmatch(r"[A-Za-zÀ-ÿ0-9 &/–-]+", ult)):
                alts[atual].pop()
        # símbolos soltos no fim (marcadores de lista, restos de fórmula)
        for k in alts:
            while alts[k] and re.fullmatch(r"[•▪±·\s]+", alts[k][-1]):
                alts[k].pop()
        questoes.append({"numero": num, "secao": secao, "enunciado_linhas": enun,
                         "alternativas_linhas": alts, "mesclada": mesclada,
                         "recebeu_contexto": recebeu_contexto})
    return questoes, total_A


def juntar(ls):
    s = ""
    for l in ls:
        if s.endswith("-") and not s.endswith(" -") and l[:1].islower():
            s = s[:-1] + l                                   # hifenização de fim de linha
        else:
            s = (s + " " + l) if s else l
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"(\s*[±•▪]\s*)*\bTipo\s*\d\s*[–-]\s*Branca\b.*$", "", s)   # rodapé de página grudado
    return re.sub(r"(\s[•▪±·])+$", "", s)


def problemas(q, n_alt):
    p = []
    enun, alts = q["enunciado_linhas"], q["alternativas_linhas"]
    if sorted(alts) != list("ABCDE"[:n_alt]):
        p.append("alternativas_incompletas")
    if q["mesclada"]:
        p.append("questoes_mescladas")
    if REF_EXTERNA.search(" ".join(enun)) and not q.get("recebeu_contexto"):
        p.append("depende_de_texto_de_outra_questao")
    tam = sorted(len(juntar(v)) for v in alts.values())
    if tam and tam[-1] > 250 and tam[-1] > 4 * max(tam[len(tam) // 2], 20):
        p.append("alternativa_com_texto_extra")
    todas = enun + [l for v in alts.values() for l in v]
    txt = " ".join(todas)
    if PUA.search(txt):
        p.append("simbolo_nao_convertido")
    # linhas só com 1-2 dígitos/símbolos: expoentes, índices, frações ou células de tabela soltos
    if any(re.fullmatch(r"[\d()+\-*/^=−]{1,2}", l) for l in todas):
        p.append("fragmento_solto")
    if re.search(r"\w {2,}\w", txt):
        p.append("espaco_de_simbolo_perdido")
    if len(juntar(enun)) < 25:
        p.append("enunciado_curto")
    if any(not juntar(v) for v in alts.values()):
        p.append("alternativa_vazia")
    if re.search(r"\b(figura|imagem|ilustra[çc][ãa]o|gr[áa]fico|diagrama|esquema|charge|tirinha|cartum|fotografia|"
                 r"captura de tela)\b(\s+\w+){0,3}\s+(a seguir|abaixo|acima|seguinte|apresentad|mostrad|exibid|ilustrad)",
                 txt, re.I) or re.search(r"(observe|analise|considere)\s+(a|o)\s+(figura|imagem|gr[áa]fico|diagrama|esquema)",
                                         txt, re.I):
        p.append("depende_de_imagem")
    ruido = sum(1 for c in txt if not (c.isalnum() or c.isspace() or c in ".,;:!?()[]{}'\"“”‘’-–—/\\%$#@&*+=<>_|^~`°ºª§•▪→←≥≤≠×÷⇒⇔±∞√∑∈"))
    if txt and ruido / len(txt) > 0.03:
        p.append("caracteres_estranhos")
    return p


def main():
    INTERMEDIARIO.mkdir(parents=True, exist_ok=True)
    relatorio, todas = [], []
    for d in pastas_de_provas(TXT):
        n, slug = d.name[:2], d.name[3:]
        ano = int(re.search(r"-(\d{4})(-\d+)?$", slug).group(1))   # o ano está no fim do nome da pasta
        url = "https://www.pciconcursos.com.br/provas/download/" + slug
        texto = mapear_simbolos((d / "prova.txt").read_text(encoding="utf-8"))
        qs, total_A = separar(texto)

        manual = GABARITOS_MANUAIS / f"{n}.txt"
        gtxt = (manual if manual.exists() else d / "gabarito.txt").read_text(encoding="utf-8")
        cabeca = re.sub(r"\s", "", texto[:3000]).upper()
        tp = re.search(r"TIPO(\d)", cabeca)
        tp = int(tp.group(1)) if tp else 1
        turno = "manha" if "manha" in slug else ("tarde" if "tarde" in slug else None)
        titulo = re.sub(r"-fgv-\d{4}(-\d+)?$", "", slug).replace("-", " ")
        bloco, score = escolher(blocos(gtxt), titulo, total_A, turno, tp)
        gab_ok = bloco is not None and n not in GABARITO_INVALIDO
        n_alt = Counter(len(q["alternativas_linhas"]) for q in qs).most_common(1)[0][0] if qs else 5

        relatorio.append({"prova": d.name, "ano": ano, "alternativas_por_questao": n_alt,
                          "questoes_no_pdf": total_A, "questoes_separadas": len(qs),
                          "bloco_gabarito": bloco["cab"] if bloco else "", "similaridade": round(score, 2),
                          "gabarito_usado": gab_ok, "obs": GABARITO_INVALIDO.get(n, "manual" if manual.exists() else "")})
        for q in qs:
            resp = bloco["resp"].get(q["numero"]) if gab_ok else None
            rec = {"id": f"{n}-{q['numero']:03d}", "prova": d.name, "ano": ano, "banca": "FGV",
                   "url": url, "numero": q["numero"],
                   "secao": q["secao"], "enunciado": juntar(q["enunciado_linhas"]),
                   "alternativas": {k: juntar(v) for k, v in q["alternativas_linhas"].items()},
                   "gabarito": resp, "problemas": problemas(q, n_alt)}
            if resp is None:
                rec["problemas"].append("sem_gabarito")
            elif resp == "ANULADA":
                rec["problemas"].append("questao_anulada")
            todas.append(rec)

    with open(INTERMEDIARIO / "questoes_brutas.jsonl", "w", encoding="utf-8") as f:
        for r in todas:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(INTERMEDIARIO / "relatorio_extracao.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(relatorio[0]))
        w.writeheader()
        w.writerows(relatorio)
    print(len(todas), "questões brutas")
    print(Counter(p for r in todas for p in r["problemas"]).most_common())
    for r in relatorio:
        if r["questoes_no_pdf"] != r["questoes_separadas"] or not r["gabarito_usado"]:
            print("ATENÇÃO", r)


if __name__ == "__main__":
    main()
