# Parte 2 — corpus de similaridade de palavras

O processamento está dividido em scripts, seguindo os três passos do item 2a do enunciado:

| Passo | Script | O que faz | Saída |
|---|---|---|---|
| 1 — pré-processamento (2a.i) | `scripts/01_preprocessar_textos.py` | Tokeniza, lematiza e remove stopwords dos enunciados e alternativas | `dados/intermediario/questoes_lematizadas.jsonl` |
| 2 — seleção de palavras (2a.ii) | `scripts/02_selecionar_palavras.py` | Seleciona os 200 lemas de maior média TF-IDF | `corpus/palavras_similaridade.csv` |
| 3 — sorteio dos pares (2a.iii) | `scripts/03_gerar_pares.py` | Embaralha as 200 palavras com semente 42 e forma 100 pares sem reposição | `corpus/pares_similaridade.csv` |
| 4 — concordância (2d/e) | `scripts/04_avaliar_concordancia.py` | Valida as notas, calcula concordância e exporta o corpus consolidado | `corpus/corpus_similaridade.csv` e `corpus/estatisticas/concordancia_similaridade.json` |

O arquivo intermediário liga os passos 1 e 2: cada linha contém o ID da questão, seus lemas e as formas originais correspondentes. O TF-IDF usa `min_df=5`, `max_df=0.8`, TF logarítmico e normalização L2.

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

Execute os comandos abaixo a partir da raiz do projeto. Os arquivos de saída já estão incluídos. Para reproduzir os três primeiros passos sem sobrescrevê-los, use saídas temporárias:

```bash
.venv/bin/python -m pip install -r "parte 2/requirements.txt"
.venv/bin/python "parte 2/scripts/01_preprocessar_textos.py" --saida /tmp/t1-pln-step1.jsonl
.venv/bin/python "parte 2/scripts/02_selecionar_palavras.py" --origem /tmp/t1-pln-step1.jsonl --saida /tmp/t1-pln-step2.csv
.venv/bin/python "parte 2/scripts/03_gerar_pares.py" --origem /tmp/t1-pln-step2.csv --saida /tmp/t1-pln-step3.csv
.venv/bin/python "parte 2/scripts/04_avaliar_concordancia.py"
```

Sem `--origem` e `--saida`, os scripts usam as entradas e saídas da tabela. Os três primeiros recusam sobrescrever arquivos existentes. O quarto lê os arquivos `anotador_*.csv` de `dados/anotacoes_similaridade/`, valida as 100 notas de cada avaliador, atualiza o corpus consolidado e grava as medidas em `corpus/estatisticas/concordancia_similaridade.json`. Os CSVs usam `tipo_anotacao=humana` e identificam a anotadora na coluna `anotador`.

O cálculo inclui kappa de Cohen linear (principal), kappa quadrático, concordância exata, diferença absoluta média e matriz de confusão. As notas individuais são preservadas; a média não é uma nota consensual.
