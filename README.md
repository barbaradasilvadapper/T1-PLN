# T1 PLN - Corpus de questões de concursos de TI e similaridade de palavras

Grupo: Ana Carolina Poletto, Bárbara Dapper, João Pedro Martins, Luiza Pasini e Rafaela Remião.

| Parte | Pasta | Entregável |
|---|---|---|
| 1. Corpus de questões | `parte 1/` | 2.506 questões da FGV com gabarito e subárea, estatísticas e dataset card |
| 2. Corpus de similaridade | `parte 2/` | 100 pares de palavras anotados por duas pessoas, concordância e dataset card |
| 3. Classificação | `parte 3/` | classificador de questões por subárea (TF-IDF, spaCy e BERT) |
| 4. Similaridade de palavras | `parte 4/` | analisador de similaridade (spaCy, BERT e LLM) comparado com as notas humanas |

Todas as partes seguem a mesma estrutura: `scripts/` com os scripts numerados na ordem em que rodam, e as
saídas em `corpus/` (partes 1 e 2) ou `resultados/` (partes 3 e 4). Os comandos abaixo rodam a partir da raiz
do repositório.

```bash
pip install -r requirements.txt
```

## Parte 1: corpus de questões

Corpus com 2.506 questões de múltipla escolha de computação, tiradas de 95 provas da FGV (2021 a 2026)
disponíveis no [PCI Concursos](https://www.pciconcursos.com.br/provas/ti/). Cada questão tem enunciado,
alternativas, gabarito oficial, ano e subárea.

| Subárea | Questões |
|---|---:|
| Engenharia de Software e Programação | 727 |
| Redes e Infraestrutura | 669 |
| Segurança da Informação | 502 |
| Banco de Dados e Ciência de Dados | 469 |
| Governança e Gestão de TI | 139 |

O enunciado pede pelo menos 3 subáreas com pelo menos 500 questões cada. As três primeiras atendem;
Banco de Dados e Governança ficaram como subáreas extras, porque tirar essas questões deixaria o corpus menor
e o classificador da parte 3 com menos classes.

```bash
python3 "parte 1/scripts/01_pdf_para_txt.py"                  # precisa do poppler (pdftotext)
python3 "parte 1/scripts/02_extrair_questoes.py"
python3 "parte 1/scripts/03_filtrar_classificar_exportar.py"
```

As estatísticas estão em `parte 1/estatisticas.ipynb` e o dataset card em `parte 1/DATASET_CARD.xlsx`
(template da disciplina).

### Organização

```
parte 1/
  dados/
    pdfs/NN_nome-da-prova/     PDFs da prova e do gabarito (baixados do PCI Concursos)
    txt/NN_nome-da-prova/      texto extraído dos PDFs
    gabaritos_manuais/48.txt   gabarito da prova 48 digitado à mão (o PDF é uma imagem)
    validacao_rotulos.csv      questões conferidas à mão, usadas só para medir o acerto da subárea
  corpus/
    corpus.json                dataset final
    por_subarea/*.json         as mesmas questões separadas por subárea e agrupadas por ano
    questoes/<subárea>/<ano>/  um arquivo .txt por questão ([ENUNCIADO], [ALTERNATIVAS], [GABARITO])
    corpus.csv                 uma linha por questão
    descartadas.json           questões removidas e o motivo
  scripts/
    01_pdf_para_txt.py         converte os PDFs em texto
    02_extrair_questoes.py     separa as questões, enunciado e alternativas, e junta o gabarito
    03_filtrar_classificar_exportar.py   filtra, remove duplicadas, classifica e gera o corpus
    gabarito.py, subareas.py, comum.py   funções usadas pelos scripts acima
  estatisticas.ipynb           estatísticas e gráficos do corpus
  DATASET_CARD.xlsx            dataset card
```

### Formato do JSON

`corpus.json` tem um bloco `metadados` e a lista `questoes`. Exemplo de uma questão:

```json
{
  "id": "28-061",
  "subarea": "seguranca_da_informacao",
  "origem_subarea": "palavras_chave",
  "ano": 2023,
  "banca": "FGV",
  "cargo_orgao": "analista judiciario analise de sistemas redes tj se",
  "prova": "28_analista-judiciario-analise-de-sistemas-redes-tj-se-fgv-2023",
  "url_prova": "https://www.pciconcursos.com.br/provas/download/analista-judiciario-analise-de-sistemas-redes-tj-se-fgv-2023",
  "numero_na_prova": 61,
  "secao_na_prova": "Conhecimentos Específicos",
  "enunciado": "O computador de Elias foi infectado por um rootkit que ...",
  "alternativas": [{"letra": "A", "texto": "memória;"}, {"letra": "B", "texto": "kernel;"}, ...],
  "gabarito": "A",
  "resposta_correta": "memória;",
  "tambem_em": [],
  "pontuacao_subareas": {"seguranca_da_informacao": 4, "redes_e_infraestrutura": 3, ...}
}
```

O `id` é o número da pasta da prova em `parte 1/dados/pdfs` mais o número da questão na prova. `tambem_em` lista
questões iguais de outras provas do mesmo concurso, que foram removidas como duplicadas. `origem_subarea` diz
qual etapa da classificação decidiu a subárea (ver abaixo).

### Como foi feito

1. **Coleta:** escolhemos 95 provas de TI da FGV entre 2021 e 2026, todas com gabarito. Os PDFs foram
   baixados manualmente, porque o site pede uma verificação de segurança em cada prova.
2. **Conversão:** as provas da FGV são em duas colunas, então o texto é extraído com
   `pdftotext -bbox-layout` e os blocos são reordenados por coluna. Os gabaritos usam `pdftotext -layout`.
3. **Separação:**
   - Tiramos cabeçalhos e rodapés.
   - Identificamos a seção de cada questão (Língua Portuguesa, Conhecimentos Específicos etc.).
   - Separamos o enunciado das alternativas.
   - Cada arquivo de gabarito tem vários cargos. O bloco certo é escolhido pelo número de questões, pelo
     tipo de prova (Tipo 1) e pelo nome do cargo.
4. **Filtragem:** são descartadas as questões que:
   - não são de computação (português, direito, raciocínio lógico etc.);
   - tiveram problema na conversão (símbolos perdidos, fórmulas ou tabelas quebradas, alternativa
     faltando, dependência de figura, texto de apoio que ficou em outra questão);
   - não têm gabarito ou foram anuladas;
   - são repetidas.

   Das 6.777 questões extraídas, ficaram 2.506. O motivo de cada descarte está em `corpus/descartadas.json`.
5. **Classificação por subárea** (`scripts/subareas.py`), em duas etapas:
   - **Palavras-chave:** cada subárea tem uma lista de termos com peso 2 (característicos, como "cobit",
     "ipsec", "select") ou 1 (genéricos, como "dados", "projeto"). A pontuação de cada subárea soma os termos
     encontrados, e os do enunciado valem o dobro, porque o assunto da questão está no enunciado; as
     alternativas costumam citar termos de outras áreas.
   - **Questões ambíguas:** quando a diferença entre as duas subáreas mais pontuadas é menor que 4 pontos
     (11% das questões), o rótulo por palavras-chave não é confiável. As outras 89% servem de treino para um
     TF-IDF + k-NN (k=3, o mesmo do notebook de classificação da disciplina), e é ele que decide a subárea
     das ambíguas.

   Para escolher essa forma, conferimos à mão 336 questões (`dados/validacao_rotulos.csv`): uma amostra
   aleatória de 100 (20 por subárea) e 236 questões difíceis, aquelas em que um classificador discordava das
   palavras-chave. Testamos variações e ficamos com a que mais acertava:

   | Classificação | Amostra aleatória | Questões difíceis |
   |---|---:|---:|
   | só palavras-chave | 92% | 47% |
   | palavras-chave + stemming (RSLP) | 83-87% | piorou |
   | palavras-chave com enunciado valendo 2x | 92% | 53% |
   | enunciado 2x + regressão logística nas ambíguas | 95% | 66% |
   | **enunciado 2x + k-NN nas ambíguas (usada)** | **97%** | **69%** |

   O stemming piorou porque, reduzindo as palavras ao radical, termos de áreas diferentes passam a coincidir.
   O arquivo de validação só serve para medir: o script 03 imprime o acerto, mas nenhum rótulo do corpus vem
   dele.

### Limitações

- Cerca de 3% das questões continuam com a subárea errada, principalmente em fronteiras como protocolos de
  segurança × redes, estatística × BD e gestão de projetos × engenharia de software.
- Governança tem só 139 questões; as outras quatro subáreas têm entre 469 e 727.
- A prova 53 (MP/RJ) ficou sem questões, porque o gabarito disponível no site é de outro cargo.
- As provas 08 e 46 (CVM, manhã) e 49 (Câmara dos Deputados, manhã) só têm conhecimentos gerais, então não
  contribuíram com questões.
- Usar só a FGV deixa o formato uniforme, mas limita a variedade de estilos de questão.

## Parte 2: corpus de similaridade de palavras

```bash
python3 "parte 2/scripts/01_preprocessar_textos.py" --saida /tmp/passo1.jsonl
python3 "parte 2/scripts/02_selecionar_palavras.py" --origem /tmp/passo1.jsonl --saida /tmp/passo2.csv
python3 "parte 2/scripts/03_gerar_pares.py" --origem /tmp/passo2.csv --saida /tmp/passo3.csv
python3 "parte 2/scripts/04_avaliar_concordancia.py"
```

Os três primeiros scripts não sobrescrevem as saídas que já estão no repositório (por isso o `--saida`).
Sem esses argumentos, usam os caminhos padrão da tabela.

| Passo | Script | O que faz | Saída |
|---|---|---|---|
| 2a.i | `01_preprocessar_textos.py` | tokeniza, lematiza (spaCy `pt_core_news_sm`) e remove stopwords e termos de instrução ("assinale", "alternativa"...) | `dados/intermediario/questoes_lematizadas.jsonl` |
| 2a.ii | `02_selecionar_palavras.py` | escolhe os 200 lemas de maior TF-IDF médio (`min_df=5`, `max_df=0.8`, TF logarítmico) | `corpus/palavras_similaridade.csv` |
| 2a.iii | `03_gerar_pares.py` | embaralha as 200 palavras (semente 42) e forma 100 pares sem repetição | `corpus/pares_similaridade.csv` |
| 2d/e | `04_avaliar_concordancia.py` | valida as notas, calcula a concordância e gera o corpus final | `corpus/corpus_similaridade.csv` |

A escala de anotação (2b) mede semelhança de significado no domínio de TI, não só associação de tema:

| Nota | Critério |
|---|---|
| 1 | nenhuma semelhança relevante de significado |
| 2 | baixa: ligação principalmente temática ou funcional |
| 3 | moderada: propriedades em comum, conceitos distintos |
| 4 | alta: significados próximos, com diferenças importantes |
| 5 | muito alta: sinônimos ou praticamente equivalentes |

A Luiza e a Rafaela anotaram os 100 pares separadamente (`dados/anotacoes_similaridade/`). Elas deram a mesma
nota em 89 pares e, nos outros 11, a diferença foi de um ponto. O kappa de Cohen linear foi 0,79 (quadrático
0,85) e o Spearman entre as duas, 0,83. Como os pares foram sorteados, a maioria das notas ficou baixa: 66 pares
receberam 1 das duas. O dataset card está em `parte 2/DATASET_CARD_SIMILARIDADE.md`.


A escala da parte 2 tem os mesmos cinco graus da planilha de anotação feita em aula, só que com outros números:
1 (nenhuma) = 0 (nada similar), 2 (baixa) = 0,25, 3 (moderada) = 0,5, 4 (alta) = 0,75 e 5 (muito alta) = 1
(sinônimos). Na parte 4 convertemos as notas para a escala da aula, para comparar os dois datasets do mesmo jeito.

## Parte 3: classificação das questões por subárea

```bash
python3 "parte 3/scripts/01_tfidf.py"        # 3a: BoW + TF-IDF
python3 "parte 3/scripts/02_embeddings.py"   # 3b: spaCy e BERT
python3 "parte 3/scripts/03_analise.py"      # 3c: comparação e matrizes de confusão
```

Todos os modelos usam o mesmo texto (enunciado + alternativas) e a mesma divisão: 80% treino e 20% teste,
estratificada, com `random_state=42`, como no notebook de exemplo da disciplina. Os parâmetros foram
escolhidos com validação cruzada de 5 partes só no treino, e o teste foi usado uma vez, no fim. Como as
classes são desbalanceadas, a métrica principal é o F1-macro. As saídas ficam em `parte 3/resultados/`.

### 3a. BoW + TF-IDF

`TfidfVectorizer` com minúsculas e TF logarítmico (`sublinear_tf=True`), e regressão logística com
`class_weight="balanced"` por causa de Governança.

| Tamanho da BoW (`max_features`) | 200 | 500 | 1.000 | 2.000 | 5.000 | 10.000 | todas |
|---|---:|---:|---:|---:|---:|---:|---:|
| F1-macro (validação cruzada) | 0,754 | 0,837 | 0,876 | 0,896 | 0,908 | **0,909** | 0,909 |

O resultado sobe rápido até umas 2.000 palavras e quase não muda depois de 5.000. Ficamos com 10.000, o melhor
valor, que corresponde a uns 60% do vocabulário (~17 mil types): as palavras que ficam de fora aparecem uma
ou duas vezes no corpus e não ajudam a separar as subáreas.

| Variação (com 10.000 termos) | F1-macro (validação cruzada) |
|---|---:|
| unigramas, `min_df=1` | 0,909 |
| unigramas + bigramas | 0,901 |
| stopwords do spaCy | **0,914** |
| stopwords do spaCy + `max_df=0.8` | 0,914 |
| lemas sem stopwords (pré-processamento da parte 2) | 0,909 |
| k-NN (k=3) no lugar da regressão logística | 0,885 |

Bigramas e lematização não ajudaram: com 2 mil questões de treino os bigramas ficam raros, e o lematizador do
spaCy erra muito termo técnico. As stopwords ajudaram um pouco. O `max_df=0.8` não mudou nada, porque depois
de tirar as stopwords nenhuma palavra aparece em 80% das questões. O k-NN do notebook da disciplina ficou
2 a 3 pontos atrás: em vetores com milhares de dimensões, a distância entre duas questões diz pouco, e a
regressão logística aprende quais palavras importam para cada classe.

Modelo final: 10.000 termos, unigramas, stopwords do spaCy e regressão logística. As palavras de maior peso
em cada classe fazem sentido (BD: dados, banco, sql, tabela; Redes: rede, nuvem, linux, ip; Segurança:
segurança, autenticação, criptografia, ataque; Governança: itil, processos, projetos, governança).

### 3b. Word embeddings

Cada questão vira um vetor, que vai para a mesma regressão logística (com padronização). Os modelos não foram
ajustados (sem fine-tuning); só geram os vetores.

- **Estático, spaCy `pt_core_news_lg`:** média dos vetores de 300 dimensões das palavras da questão.
- **Transformer, BERTimbau (`neuralmind/bert-base-portuguese-cased`):** usamos o BERT treinado em português em
  vez do `bert-base-uncased`, que é em inglês. Média dos vetores de 768 dimensões dos tokens da última camada
  (sem o padding), com o texto cortado em 512 tokens.

### 3c. Resultados no teste (502 questões)

| Modelo | F1-macro | Acurácia | BD | Eng. Software | Governança | Redes | Segurança |
|---|---:|---:|---:|---:|---:|---:|---:|
| TF-IDF + regressão logística | **0,910** | **0,912** | 0,91 | 0,92 | 0,89 | 0,90 | 0,93 |
| spaCy `pt_core_news_lg` | 0,832 | 0,851 | 0,81 | 0,86 | 0,73 | 0,87 | 0,89 |
| BERTimbau | 0,804 | 0,813 | 0,77 | 0,83 | 0,76 | 0,80 | 0,86 |

As colunas por subárea são o F1 de cada classe. As matrizes de confusão estão em
`parte 3/resultados/matrizes_confusao.png`.

O TF-IDF ganhou com folga, e vemos três motivos:

1. **Termos técnicos decidem a subárea.** Uma questão com "SELECT" ou "ITIL" quase não deixa dúvida, e o
   TF-IDF dá peso direto a esses termos raros. Nos embeddings, a média de todas as palavras dilui esses termos
   no meio de palavras comuns de prova ("analise", "afirmativas", "correto").
2. **O rótulo também vem de palavras.** A subárea foi definida por palavras-chave e, nas questões ambíguas,
   por um TF-IDF com k-NN. O TF-IDF da parte 3 aprende praticamente a mesma regra que gerou os rótulos, o que
   favorece ele na comparação.
3. **O BERT não foi ajustado.** Sem fine-tuning, ele dá um vetor genérico da frase, que não foi treinado para
   separar assuntos de TI. Ficou abaixo do spaCy em quase tudo e só ganhou em Governança (0,76 × 0,73), onde o
   contexto da frase pesa mais que palavras isoladas.

Governança é a classe mais difícil para os embeddings: é a menor e divide vocabulário com Engenharia de
Software (projeto, processo, requisito). Das 502 questões de teste, 370 foram acertadas pelos três modelos e
26 foram erradas pelos três (`parte 3/resultados/COMPARACAO.md`). Lendo essas 26, várias são rótulos errados
do corpus, não erros dos modelos: uma questão sobre COBIT marcada como Engenharia de Software, uma sobre Ajax
marcada como Banco de Dados, uma sobre o LibreOffice Writer, que nem é de computação. Ou seja, os modelos
apontam onde o rótulo automático da parte 1 falha.

## Parte 4: similaridade de palavras

```bash
export GEMINI_API_KEY="..."                      # ver "Como pegar a chave do Gemini" abaixo
python3 "parte 4/scripts/01_notas_llm.py"        # notas do LLM
python3 "parte 4/scripts/02_similaridade.py"     # spaCy, BERT e comparação com as notas humanas
```

Os dois datasets ficam na escala da aula (0 a 1). As notas da parte 2 são convertidas como explicado acima
(`parte 4/scripts/comum.py`). Comparamos a similaridade de cada modelo com a média das notas da Luiza e da
Rafaela usando a correlação de Spearman, que compara a ordem dos pares e por isso funciona mesmo quando as
escalas são diferentes (cosseno de -1 a 1 × grau de 0 a 1).

| Modelo | Como calculamos a similaridade |
|---|---|
| spaCy `pt_core_news_lg` | cosseno entre os vetores das duas palavras (`token.similarity`, como no notebook da aula) |
| BERTimbau | cosseno entre os vetores de cada palavra isolada (média dos subtokens da última camada) |
| LLM (Gemini 3.5 Flash) | recebe os graus e os exemplos da planilha da aula e dá um grau para cada par, em lotes de 25 |

| Modelo | Spearman com a média | com a Luiza | com a Rafaela |
|---|---:|---:|---:|
| spaCy | 0,30 | 0,33 | 0,28 |
| BERTimbau | 0,23 | 0,28 | 0,21 |
| Gemini | **0,68** | 0,67 | 0,65 |
| Luiza × Rafaela (referência) | 0,83 | | |

- **O LLM ficou muito mais perto das pessoas.** Ele deu exatamente a mesma nota da Luiza em 65 pares e da
  Rafaela em 68, e sabe que, em TI, "tcp" e "ordem" têm relação (o TCP garante a ordem dos pacotes). Ele foi um
  pouco mais generoso que as anotadoras (média 0,16 × 0,09): deu 0,5 para pares como teste/programação e
  risco/gestão, que elas avaliaram como 0,25. Mesmo assim, não chega à concordância entre as duas (0,83).
- **O spaCy mede outra coisa.** Os vetores dele vêm de textos gerais (notícias, web), não de TI, e medem se
  as palavras aparecem em contextos parecidos. Por isso "operação" e "ti" ficam com similaridade negativa.
- **O BERT foi o pior.** Ele foi feito para representar palavras dentro de frases. Com a palavra sozinha,
  quase todos os pares têm cosseno alto e parecido (metade entre 0,55 e 0,69), então sobra pouca diferença entre
  um par e outro.
- **A distribuição das notas atrapalha todos.** Como 66 pares têm nota 0 das duas anotadoras, há muitos
  empates e poucos pares com similaridade alta, o que baixa qualquer correlação.

O item 4a também pede o dataset feito em aula. Para incluir, salve a planilha da aula com a coluna
"Anotação Final" preenchida como `parte 4/dados/dataset_aula.xlsx` e rode os dois scripts de novo. Eles leem a
aba `AmostraParaAnotar` e calculam tudo também para esse dataset.

### Como pegar a chave do Gemini

1. Entre em https://aistudio.google.com com uma conta Google.
2. Clique em **Get API key** e depois em **Create API key**. É grátis, sem cartão.
3. No terminal, antes de rodar o script: `export GEMINI_API_KEY="..."`. Não coloque a chave em nenhum arquivo
   do repositório.

O plano gratuito permite 20 pedidos por dia em cada modelo. Por isso o script manda 25 pares por pedido (4
pedidos para o nosso dataset) e, se for interrompido, continua de onde parou na próxima vez que rodar.

## Uso de IA

- **Partes 1, 3 e 4:** usamos o Claude (Anthropic), pelo Claude Code, como assistente de programação, para
  escrever e depurar os scripts e revisar o texto deste README. A conferência das 336 questões de
  `validacao_rotulos.csv`, usada para medir o acerto da subárea e escolher o método de classificação, foi
  feita com o Claude. Nenhum rótulo do corpus vem dessa conferência.
- **Parte 2:** o Codex (OpenAI) ajudou a implementar e documentar os scripts. As notas dos 100 pares foram dadas
  pela Luiza e pela Rafaela, sem IA.
- **Parte 4:** o LLM avaliado é o Gemini 3.5 Flash, chamado pela API.
