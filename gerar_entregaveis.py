"""Copia para a pasta entregaveis/ os arquivos finais pedidos no enunciado.

Rodar depois de atualizar qualquer parte: python3 gerar_entregaveis.py
Os notebooks em entregaveis/ são cópias já executadas; para rodar de novo, use os das pastas "parte N".
"""
import shutil
from pathlib import Path

RAIZ = Path(__file__).parent
DESTINO = RAIZ / "entregaveis"

ARQUIVOS = {
    "1_corpus_questoes": [
        "parte 1/corpus/corpus.json",
        "parte 1/corpus/corpus.csv",
        "parte 1/corpus/por_subarea",
        "parte 1/corpus/descartadas.json",
        "parte 1/estatisticas.ipynb",
        "parte 1/dataset_card.xlsx",
    ],
    "2_corpus_similaridade": [
        "parte 2/corpus/corpus_similaridade.csv",
        "parte 2/corpus/concordancia.json",
        "parte 2/dados/anotacoes_similaridade/anotador_luiza.csv",
        "parte 2/dados/anotacoes_similaridade/anotador_rafaela.csv",
        "parte 2/dataset_card.xlsx",
    ],
    "3_classificador_questoes": [
        "parte 3/classificacao.ipynb",
        "parte 3/resultados/comparacao.csv",
        "parte 3/resultados/comprimento_bow.png",
        "parte 3/resultados/matrizes_confusao.png",
    ],
    "4_analisador_similaridade": [
        "parte 4/similaridade.ipynb",
        "parte 4/resultados/correlacoes.csv",
        "parte 4/resultados/dispersao.png",
        "parte 4/dados/notas_llm_nosso.csv",
        "parte 4/dados/notas_llm_aula.csv",
    ],
}

shutil.rmtree(DESTINO, ignore_errors=True)
for pasta, arquivos in ARQUIVOS.items():
    (DESTINO / pasta).mkdir(parents=True)
    for arquivo in arquivos:
        origem = RAIZ / arquivo
        if origem.is_dir():
            shutil.copytree(origem, DESTINO / pasta / origem.name)
        else:
            shutil.copy2(origem, DESTINO / pasta / origem.name)
    print(f"{pasta}: {len(arquivos)} itens")
(DESTINO / "5_apresentacao").mkdir()
print("5_apresentacao: colocar aqui os slides")
