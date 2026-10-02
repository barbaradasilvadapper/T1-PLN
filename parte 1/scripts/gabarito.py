"""Leitura dos gabaritos da FGV.

Cada arquivo de gabarito tem vários blocos, um por cargo e tipo de prova: um cabeçalho com o nome do
cargo, uma linha com os números das questões e outra com as respostas (A a E; * ou X quando foi anulada).
blocos() lê todos os blocos e escolher() acha o da nossa prova: mesmo número de questões, prova Tipo 1
(a que está no site) e cabeçalho mais parecido com o nome do cargo.
"""
import re

from comum import norm

def tokens(s):
    return set(re.sub(r"[^a-z0-9 ]", " ", norm(s)).split())


RESP = re.compile(r"^([A-EX*]|NULA|ANULADA)$", re.I)
STOP = set("de da do das dos e em a o fgv prova tipo".split())


def eh_ruido(s):
    return (not s or s.startswith("pcimark") or "pciconcursos" in s
            or re.match(r"^\(?\*|^P[áa]gina|^\(?[A-Z]?\)?\s*[–-]?\s*Quest", s)
            or re.search(r"GABARITO|CONCURSO|EDITAL|APLICAD|PROVIMENTO|QUADRO DE PESSOAL|^\d{2}/\d{2}/\d{4}$", s, re.I))


def blocos(texto):
    """[{'cab': cabeçalho, 'turno': 'manha'|'tarde'|None, 'resp': {n: 'A'..'E'|'ANULADA'}}]"""
    L = texto.splitlines()
    out, buf, ult_txt, turno, atual, i = [], [], -99, None, None, 0
    while i < len(L):
        s = L[i].strip()
        toks = s.split()
        if re.search(r"\bMANH[AÃ]\b", s, re.I) and "turno" not in s.lower():
            turno = "manha"
        if re.search(r"\bTARDE\b", s, re.I) and "turno" not in s.lower():
            turno = "tarde"
        if toks and all(t.isdigit() for t in toks):
            nums = [int(t) for t in toks]
            j = i + 1
            while j < len(L) and not L[j].strip():
                j += 1
            resp = L[j].split() if j < len(L) else []
            if resp and all(RESP.match(r) for r in resp) and len(resp) == len(nums):
                if buf:                                  # apareceu um cabeçalho novo: começa outro bloco
                    atual = {"cab": " ".join(buf), "turno": turno, "resp": {}}
                    out.append(atual)
                    buf = []
                if atual is not None:
                    for n, r in zip(nums, resp):
                        r = r.upper()
                        atual["resp"][n] = r if r in "ABCDE" else "ANULADA"
                i = j + 1
                continue
        if s and not eh_ruido(s) and len(s) > 3:
            if i - ult_txt > 1:                          # linhas consecutivas = mesmo cabeçalho
                buf = []
            buf.append(s)
            ult_txt = i
        i += 1
    return out


def tipo_do_cabecalho(cab):
    c = re.sub(r"[^a-z0-9 ]", " ", norm(cab))
    m = re.search(r"(?:tipo|prova)\s*(\d)", c) or re.search(r"\s(\d)\s+turno", c)
    if m:
        return int(m.group(1))
    return 1 if "branca" in c else None


def escolher(blocos_, titulo, n_questoes, turno=None, tipo=1):
    alvo = tokens(titulo) - STOP
    melhor, score_m = None, -1.0
    for b in blocos_:
        if tipo_do_cabecalho(b["cab"]) not in (None, tipo):
            continue
        if len(b["resp"]) != n_questoes:
            continue
        cab = tokens(b["cab"]) - STOP - {str(d) for d in range(10)} - {"manha", "tarde", "turno", "branca"}
        if not cab:
            continue
        score = len(alvo & cab) / len(alvo | cab)        # Jaccard entre o nome do cargo e o cabeçalho
        if turno and b["turno"] == turno:
            score += 0.05
        if score > score_m:
            melhor, score_m = b, score
    return melhor, score_m
