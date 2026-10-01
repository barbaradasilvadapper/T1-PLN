# Parte 2 — corpus de similaridade de palavras

`scripts/06_preparar_similaridade.py` tokeniza e lematiza enunciados e alternativas com spaCy, remove stopwords e seleciona os 200 lemas com maior média TF-IDF nas questões (`min_df=5`, `max_df=0.8`, TF logarítmico e normalização L2). O sorteio com semente 42 forma 100 pares sem repetição de palavras. Os resultados estão em `corpus/palavras_similaridade.csv` e `corpus/pares_similaridade.csv`.

As avaliações manuais de Luiza e Rafaela estão em `dados/anotacoes_similaridade/`; o resultado consolidado está em `corpus/corpus_similaridade.csv`. A documentação exigida pelo item 2f está em `DATASET_CARD_SIMILARIDADE.md`.

### Escala de anotação

Avalie semelhança de significado no domínio de TI, não apenas associação temática. Cada avaliador usa a escala independentemente, sem consultar as notas do outro, e registra sua interpretação quando o termo é ambíguo.

| Nota | Critério |
|---|---|
| 1 | Nenhuma semelhança relevante de significado |
| 2 | Baixa: ligação principalmente temática ou funcional |
| 3 | Moderada: propriedades em comum, conceitos distintos |
| 4 | Alta: significados próximos, com diferenças importantes |
| 5 | Muito alta: sinônimos ou praticamente equivalentes |

### Executar a parte 2

Execute os comandos abaixo a partir da raiz do projeto:

```bash
.venv/bin/python -m pip install -r parte2/requirements.txt
.venv/bin/python parte2/scripts/06_preparar_similaridade.py --saida /tmp/t1-pln-similaridade
.venv/bin/python parte2/scripts/07_avaliar_concordancia.py
```

O primeiro script recusa sobrescrever palavras e pares existentes. O segundo lê os arquivos `anotador_*.csv` de `dados/anotacoes_similaridade/`, valida as 100 notas de cada avaliador, atualiza o corpus consolidado e grava as medidas em `corpus/estatisticas/concordancia_similaridade.json`. Os CSVs usam `tipo_anotacao=humana` e identificam a anotadora na coluna `anotador`.

O cálculo inclui kappa de Cohen linear (principal), kappa quadrático, concordância exata, diferença absoluta média e matriz de confusão. As notas individuais são preservadas; a média não é uma nota consensual. O script `../rodar_tudo.sh` executa apenas a parte 1.
