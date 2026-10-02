# T1 PLN - Corpus de questões de concursos de TI e similaridade de palavras

Grupo: Ana Carolina Poletto, Bárbara Dapper, João Pedro Martins, Luiza Pasini e Rafaela Remião.

## Entregáveis

Todos os arquivos finais estão em `entregaveis/`:

| Entregável | Arquivos |
|---|---|
| Corpus de questões | `corpus_questoes.json`, `corpus_questoes.csv`, `estatisticas_questoes.ipynb`, `dataset_card_questoes.xlsx` |
| Corpus de similaridade | `corpus_similaridade.csv`, `dataset_card_similaridade.xlsx` |
| Classificador de questões | `classificador_questoes.ipynb` |
| Analisador de similaridade | `analisador_similaridade.ipynb` |
| Apresentação | `Trabalho1_PLN.key`, `Trabalho1_PLN.pptx`, `Trabalho1_PLN.pdf` |

As pastas `parte 1` a `parte 4` têm o código e os dados que geram esses arquivos.

## Como rodar

```bash
pip install -r requirements.txt
```

**Parte 1** (precisa do `pdftotext`: `brew install poppler`):

```bash
python3 "parte 1/scripts/converter_pdfs.py"
python3 "parte 1/scripts/extrair_questoes.py"
python3 "parte 1/scripts/montar_corpus.py"
```

**Parte 2:**

```bash
python3 "parte 2/scripts/preprocessar.py"
python3 "parte 2/scripts/escolher_palavras.py"
python3 "parte 2/scripts/sortear_pares.py"
python3 "parte 2/scripts/concordancia.py"
```

**Partes 3 e 4:** notebooks `parte 3/classificacao.ipynb` e `parte 4/similaridade.ipynb`. As notas do Gemini já
estão salvas em `parte 4/dados/`; para pedir de novo, apague os arquivos `notas_llm_*.csv` e defina
`GEMINI_API_KEY` (chave gratuita em https://aistudio.google.com).

## Parte 1: corpus de questões

2.506 questões de múltipla escolha de 95 provas de TI da FGV (2021 a 2026), baixadas do
[PCI Concursos](https://www.pciconcursos.com.br/provas/ti/), com enunciado, alternativas, gabarito, ano e subárea.
Das 6.777 questões extraídas dos PDFs, 4.271 foram descartadas (fora de computação, problema de conversão, sem
gabarito, anuladas ou repetidas).

| Subárea | Questões |
|---|---:|
| Engenharia de Software e Programação | 727 |
| Redes e Infraestrutura | 669 |
| Segurança da Informação | 502 |
| Banco de Dados e Ciência de Dados | 469 |
| Governança e Gestão de TI | 139 |

As três primeiras atendem ao mínimo de 500 questões; BD e Governança são subáreas extras.

A subárea é definida em duas etapas (`parte 1/scripts/subareas.py`): pontuação por palavras-chave, com o
enunciado valendo o dobro, e um TF-IDF + k-NN (k=3, como no notebook da aula) para as questões em que duas
subáreas ficam quase empatadas. Numa amostra aleatória de 100 questões conferidas, 97 estavam na subárea certa.

## Parte 2: corpus de similaridade

As questões foram tokenizadas, lematizadas e sem stopwords (spaCy). Os 200 lemas de maior TF-IDF médio foram
sorteados em 100 pares, e a Luiza e a Rafaela anotaram cada par de 1 a 5, sem ver as notas uma da outra
(1 nenhuma semelhança, 2 baixa, 3 moderada, 4 alta, 5 sinônimos; equivale a 0, 0,25, 0,5, 0,75 e 1 na escala
da aula). Concordância: kappa linear de 0,79 e Spearman de 0,83.

## Parte 3: classificação

Mesma divisão do notebook da aula (80/20, estratificada, `random_state=42`), com k-NN (k=3) e regressão
logística. Parâmetros do TF-IDF escolhidos com validação cruzada no treino: 10.000 termos, unigramas e
stopwords do spaCy.

| Representação | F1-macro (k-NN) | F1-macro (regressão logística) |
|---|---:|---:|
| TF-IDF | 0,881 | **0,910** |
| spaCy `pt_core_news_lg` | 0,426 | 0,832 |
| BERTimbau | 0,753 | 0,804 |

O TF-IDF ganha porque os termos técnicos ("SELECT", "ITIL") decidem a subárea, e a média dos embeddings dilui
esses termos.

## Parte 4: similaridade de palavras

Correlação de Spearman com as notas humanas, no nosso dataset e no feito em aula:

| Modelo | Nosso dataset | Dataset de aula |
|---|---:|---:|
| spaCy | 0,30 | 0,07 |
| BERTimbau | 0,23 | 0,11 |
| Gemini 3.5 Flash | **0,68** | **0,53** |
| Concordância entre as pessoas | 0,83 | 0,35 a 0,40 |

Só o Gemini usa o sentido das palavras em TI. O spaCy foi treinado em textos gerais e não conhece vários
termos técnicos, e o BERT não foi feito para palavras isoladas.

## Uso de IA

- revisão de parte do código (a classificação de subárea da
  parte 1, a simplificação dos scripts da parte 2 e os notebooks das partes 3 e 4), dos textos e 
- conferência das 336 questões usadas para medir o acerto da subárea.
- **Gemini:** é um dos modelos avaliados na parte 4.

