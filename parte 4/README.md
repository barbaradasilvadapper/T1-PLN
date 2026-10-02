# Parte 4 — similaridade de palavras (spaCy × BERT × LLM)

`python "parte 4/scripts/01_similaridade.py"` compara, nos 100 pares da parte 2, a similaridade de três modelos com a anotação humana (média de Luiza e Rafaela, escala 1–5).

| Modelo | Como a similaridade é calculada |
|---|---|
| spaCy `pt_core_news_lg` (estático) | cosseno entre os vetores de 300d das duas palavras (`token.similarity`) |
| BERTimbau `neuralmind/bert-base-portuguese-cased` | cosseno entre o vetor de cada palavra isolada (média dos subtokens, última camada) |
| LLM (Claude) | nota 1–5 dada ao par, com os critérios da escala da parte 2 (`dados/notas_llm_claude.csv`) |

Métrica: correlação de Spearman (principal) e Pearson com a média humana; saída em `resultados/`.

**Uso de IA (declarar na apresentação):** as notas do LLM foram dadas pelo Claude dentro da sessão de trabalho, sem chamada de API, vendo apenas os pares de palavras. O Claude já tinha visto as estatísticas gerais das notas humanas (média ≈ 1,4; a maioria dos pares com nota 1) e as notas dos 4 primeiros pares; isso pode ter influenciado a distribuição das notas.
Os scripts e a análise também foram escritos com apoio do Claude Code.

**Pendente:** o dataset de palavras "feito em aula" não está no repositório. Para incluí-lo, basta um CSV com `palavra_1, palavra_2, similaridade`.
