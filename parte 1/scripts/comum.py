"""Caminhos e funções usados pelos scripts da parte 1."""
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"
PDFS = DADOS / "pdfs"                      # entrada: dados/pdfs/NN_slug/{prova.pdf, gabarito.pdf}
TXT = DADOS / "txt"                        # textos gerados pelo converter_pdfs.py
GABARITOS_MANUAIS = DADOS / "gabaritos_manuais"   # gabaritos transcritos à mão (PDF escaneado)
INTERMEDIARIO = DADOS / "intermediario"
CORPUS = RAIZ / "corpus"


def norm(s: str) -> str:
    """minúsculas e sem acento (para comparação)."""
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def pastas_de_provas(base: Path):
    return sorted(p for p in base.iterdir() if p.is_dir() and re.match(r"^\d{2}_", p.name))
