#!/bin/bash
# Pipeline completo do corpus (parte 1 do T1). Requer python3 (+ matplotlib, openpyxl) e poppler (pdftotext).
set -e
cd "$(dirname "$0")/scripts"
python3 01_pdf_para_txt.py                   # c: PDF -> TXT
python3 02_extrair_questoes.py               # d/e/f: questões, alternativas, gabarito, problemas de conversão
python3 03_filtrar_classificar_exportar.py   # a/d/e/h: filtro, deduplicação, subárea, JSON
if python3 -c "import spellchecker" 2>/dev/null; then
  python3 04b_qualidade_lexica.py            # g: qualidade léxica (opcional: pip install pyspellchecker)
fi
python3 04_estatisticas.py                   # g: estatísticas e gráficos
python3 05_dataset_card.py                   # i: dataset card (planilha do template + markdown)
