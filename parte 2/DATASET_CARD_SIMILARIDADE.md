# Dataset Card — SimilaridadeTI-FGV

| Campo | Valor |
|---|---|
| Domínio e idioma | Computação/TI; português com termos técnicos em inglês |
| Fonte | `../parte 1/corpus/corpus.json`: 2.506 questões da FGV, 2021–2026 |
| Tarefa | Similaridade semântica entre palavras |
| Tamanho | 200 palavras distintas, 100 pares, duas avaliações por par |
| Formato | CSV UTF-8 |
| Corpus | `corpus/corpus_similaridade.csv` |
| Avaliações | `dados/anotacoes_similaridade/anotador_luiza.csv` e `anotador_rafaela.csv` |
| Estado e origem | Anotação manual concluída por Luiza e Rafaela |
| Escala | 1 nenhuma, 2 baixa, 3 moderada, 4 alta, 5 muito alta |

## Construção

Cada questão é um documento formado por enunciado e todas as alternativas, sem duplicar a resposta correta. `scripts/01_preprocessar_textos.py` faz tokenização e lematização com spaCy `pt_core_news_sm` e remove stopwords, termos de instrução e marcadores de prova. Mantemos tokens alfabéticos com pelo menos dois caracteres, lemas em minúsculas e siglas preservadas. A lista adicional de palavras removidas está nesse script. Os textos processados são gravados em `dados/intermediario/questoes_lematizadas.jsonl` para uso no passo seguinte.

`scripts/02_selecionar_palavras.py` seleciona os 200 lemas de maior média TF-IDF nas questões, com `min_df=5`, `max_df=0.8`, TF logarítmico, IDF suavizado e normalização L2. `scripts/03_gerar_pares.py` usa a semente 42 para embaralhar os lemas e formar 100 pares sem reposição.

## Anotação e resultados

Luiza e Rafaela anotaram os 100 pares conforme a escala de similaridade de 1 a 5. Os CSVs registram os nomes das anotadoras e as notas, com `tipo_anotacao=humana`.

As avaliações apresentaram **89% de concordância exata** e **kappa linear de 0,7940**; os 11 desacordos diferiram por um ponto. A maioria das notas ficou em 1 ou 2. `scripts/04_avaliar_concordancia.py` calcula a concordância e exporta o CSV consolidado e `corpus/estatisticas/concordancia_similaridade.json`.

O sorteio combinou palavras sem considerar sua proximidade semântica. Essa escolha ajuda a explicar a concentração de notas baixas: **95% das avaliações de Luiza e 94% das de Rafaela ficaram em 1 ou 2**. Embora as palavras pertençam ao domínio de TI, pertencer ao mesmo domínio não implica ter significados semelhantes. O resultado atende à combinação aleatória solicitada no enunciado, mas oferece poucos exemplos de alta similaridade, limitando a avaliação dos níveis 4 e 5. A concordância observada deve ser interpretada junto dessa distribuição, sem generalizá-la para um conjunto equilibrado entre todos os níveis da escala.

O corpus consolidado contém IDs e palavras, tipo de anotação, identificadores dos avaliadores, notas, média, mediana, amplitude e indicação de divergências de pelo menos dois pontos. A média resume notas independentes; não representa consenso.

## Limitações e uso de IA

Codex/OpenAI auxiliou na implementação e documentação do código. A anotação dos valores foi realizada por Luiza e Rafaela.

O ranking global favorece termos e subáreas frequentes. A lematização pode errar com termos técnicos e inglês; unigramas separam expressões compostas, e o filtro alfabético exclui C++, C# e IPv6. Palavras sem contexto podem ser ambíguas. Pares aleatórios concentrados em baixa similaridade limitam a avaliação dos níveis altos da escala.
