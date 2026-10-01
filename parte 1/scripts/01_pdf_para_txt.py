"""Etapa 1 (item c): converte os PDFs em texto.

- Provas: `pdftotext -bbox-layout` (poppler) devolve os blocos de texto com coordenadas. Em cada
  página os blocos são ordenados por coluna (esquerda -> direita) e, dentro da coluna, de cima para
  baixo; blocos de largura total (cabeçalho) vêm antes. Sem isso, o texto das provas em duas colunas
  sai embaralhado. Quebras de página são marcadas com \\f.
- Gabaritos: `pdftotext -layout`, que preserva o alinhamento da tabela número/resposta.
- Gabaritos escaneados (imagem) não têm texto: ficam em dados/gabaritos_manuais/NN.txt (transcrição).

Entrada: dados/pdfs/NN_slug/*.pdf      Saída: dados/txt/NN_slug/{prova.txt, gabarito.txt}
"""
import html
import re
import subprocess
import xml.etree.ElementTree as ET

from comum import PDFS, TXT, pastas_de_provas

NS = "{http://www.w3.org/1999/xhtml}"
RUIDO = re.compile(r"^(pcimarkpci\b.*|www\.pciconcursos\.com\.br|FGV Conhecimento|Página \d+( de \d+)?)$", re.I)


def linhas_ordenadas(page):
    meio = float(page.get("width")) / 2
    blocos = []
    for b in page.iter(NS + "block"):
        x0, y0, x1 = float(b.get("xMin")), float(b.get("yMin")), float(b.get("xMax"))
        linhas = [" ".join(w.text or "" for w in ln.iter(NS + "word")) for ln in b.iter(NS + "line")]
        col = 1 if x1 <= meio + 15 else (2 if x0 >= meio - 15 else 0)
        blocos.append((col, y0, x0, linhas))
    topo_colunas = min((b[1] for b in blocos if b[0] > 0), default=1e9)

    def chave(b):
        col, y, x, _ = b
        if col == 0:                       # largura total: antes (cabeçalho) ou depois (rodapé) das colunas
            return (0 if y < topo_colunas else 3, y, x)
        return (col, y, x)
    return [l for b in sorted(blocos, key=chave) for l in b[3]]


def prova_para_txt(pdf):
    xml = subprocess.run(["pdftotext", "-bbox-layout", str(pdf), "-"], capture_output=True).stdout.decode("utf-8", "replace")
    xml = re.sub(r"<!DOCTYPE[^>]*>", "", xml)
    xml = re.sub(r"&(?!(amp|lt|gt|quot|apos|#\d+);)", "&amp;", xml)
    paginas = []
    for page in ET.fromstring(xml).iter(NS + "page"):
        linhas = [html.unescape(l).strip() for l in linhas_ordenadas(page)]
        paginas.append("\n".join(l for l in linhas if l and not RUIDO.match(l)))
    return "\n\f\n".join(paginas)


def main():
    for d in pastas_de_provas(PDFS):
        dst = TXT / d.name
        dst.mkdir(parents=True, exist_ok=True)
        for pdf in d.glob("*.pdf"):
            if "gabarito" in pdf.name.lower():
                subprocess.run(["pdftotext", "-layout", str(pdf), str(dst / "gabarito.txt")], check=True)
            else:
                (dst / "prova.txt").write_text(prova_para_txt(pdf), encoding="utf-8")
        print("ok", d.name)


if __name__ == "__main__":
    main()
