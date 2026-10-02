# T1 PLN - Corpus de questões de concursos de TI e similaridade de palavras

Grupo: Ana Carolina Poletto, Bárbara Dapper, João Pedro Martins, Luiza Pasini e Rafaela Remião.

## Organização do repositório

| Pasta | O que tem | Como roda |
|---|---|---|
| `parte 1/` | corpus de questões: PDFs, textos, scripts, corpus final, estatísticas e dataset card | scripts em `parte 1/scripts/` |
| `parte 2/` | corpus de similaridade: scripts, anotações, corpus final e dataset card | scripts em `parte 2/scripts/` |
| `parte 3/` | classificação das questões (`classificacao.ipynb`) e resultados | notebook |
| `parte 4/` | similaridade de palavras (`similaridade.ipynb`), dataset de aula, notas do LLM e resultados | notebook |
| `apresentacao/` | slides da apresentação (Keynote e PDF) | |
| `entregaveis/` | cópia do que o enunciado pede para entregar (ver abaixo) | gerada por `gerar_entregaveis.py` |

As partes 1 e 2 são pipelines de vários passos, por isso ficaram em scripts numerados. As partes 3 e 4 são
notebooks, no mesmo formato dos notebooks da disciplina, e já estão salvos com as saídas.

### Instalação

```bash
pip install -r requirements.txt
```

Testado com Python 3.13. A parte 1 também usa o `pdftotext` (no macOS: `brew install poppler`), mas só para
refazer a conversão dos PDFs.

### Entregáveis

A pasta `entregaveis/` junta o que o enunciado pede, em uma pasta por item. Ela é uma cópia: depois de mudar
alguma parte, rode `python3 gerar_entregaveis.py` para atualizar.

| Entregável | Pasta | Conteúdo |
|---|---|---|
| Corpus de questões | `entregaveis/corpus_questoes/` | `corpus.json`, `corpus.csv`, questões por subárea e ano, descartadas, estatísticas e dataset card |
| Corpus de similaridade | `entregaveis/corpus_similaridade/` | `corpus_similaridade.csv`, anotações das duas anotadoras, concordância e dataset card |
| Classificador de questões | `entregaveis/classificador_questoes/` | notebook executado, tabela de resultados e gráficos |
| Analisador de similaridade | `entregaveis/analisador_similaridade/` | notebook executado, correlações, gráfico e notas do LLM |
| Apresentação | `entregaveis/apresentacao/` | slides em Keynote e em PDF |

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
python3 "parte 1/scripts/converter_pdfs.py"     # PDF -> texto (precisa do poppler)
python3 "parte 1/scripts/extrair_questoes.py"   # separa as questões e junta o gabarito
python3 "parte 1/scripts/montar_corpus.py"      # filtra, define a subárea e gera o corpus
```

As estatísticas estão em `parte 1/estatisticas.ipynb` e o dataset card em `parte 1/dataset_card.xlsx`
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
    converter_pdfs.py          converte os PDFs em texto
    extrair_questoes.py        separa as questões, enunciado e alternativas, e junta o gabarito
    montar_corpus.py           filtra, remove duplicadas, define a subárea e gera o corpus
    gabarito.py, subareas.py, comum.py   funções usadas pelos scripts acima
  estatisticas.ipynb           estatísticas e gráficos do corpus
  dataset_card.xlsx            dataset card
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
   O arquivo de validação só serve para medir: o `montar_corpus.py` imprime o acerto, mas nenhum rótulo do corpus vem
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
python3 "parte 2/scripts/preprocessar.py"       # tokeniza, lematiza e tira stopwords
python3 "parte 2/scripts/escolher_palavras.py"  # 200 palavras de maior TF-IDF médio
python3 "parte 2/scripts/sortear_pares.py"      # 100 pares (semente 42)
python3 "parte 2/scripts/concordancia.py"       # junta as anotações e mede a concordância
```

Como o sorteio usa semente fixa, rodar de novo gera exatamente os mesmos pares que foram anotados.

| Passo | Script | O que faz | Saída |
|---|---|---|---|
| 2a.i | `preprocessar.py` | tokeniza, lematiza (spaCy `pt_core_news_sm`) e remove stopwords e termos de instrução ("assinale", "alternativa"...) | `dados/intermediario/questoes_lematizadas.jsonl` |
| 2a.ii | `escolher_palavras.py` | escolhe os 200 lemas de maior TF-IDF médio (`min_df=5`, `max_df=0.8`, TF logarítmico) | `corpus/palavras.csv` |
| 2a.iii | `sortear_pares.py` | embaralha as 200 palavras (semente 42) e forma 100 pares sem repetição | `corpus/pares.csv` |
| 2d/e | `concordancia.py` | junta as notas, calcula a concordância e gera o corpus final | `corpus/corpus_similaridade.csv` e `corpus/concordancia.json` |

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
receberam 1 das duas. O dataset card está em `parte 2/dataset_card.xlsx`, no mesmo template da parte 1.

A escala da parte 2 tem os mesmos cinco graus da planilha de anotação feita em aula, só que com outros números:
1 (nenhuma) = 0 (nada similar), 2 (baixa) = 0,25, 3 (moderada) = 0,5, 4 (alta) = 0,75 e 5 (muito alta) = 1
(sinônimos). Na parte 4 convertemos as notas para a escala da aula, para comparar os dois datasets do mesmo jeito.

## Parte 3: classificação das questões por subárea

Notebook: `parte 3/classificacao.ipynb`. Ele segue o notebook de exemplo da disciplina (*Exemplo de
Categorização de Texto usando k-nn e Bow com Tfidf*): mesma divisão treino/teste (80/20, estratificada,
`random_state=42`), `TfidfVectorizer` com as stopwords do spaCy e classificador k-NN com k=3. Para cada
representação testamos também a regressão logística, que costuma se sair melhor com vetores de muitas
dimensões. O texto de cada questão é o enunciado mais as alternativas.

Os parâmetros foram escolhidos com validação cruzada de 5 partes, só no treino; o teste foi usado uma vez, no
fim. A métrica principal é o F1-macro, porque as classes são desbalanceadas (Governança tem 139 questões).

### 3a. Bag of Words + TF-IDF

| `max_features` (comprimento da BoW) | 200 | 500 | 1.000 | 2.000 | 5.000 | 10.000 | todas |
|---|---:|---:|---:|---:|---:|---:|---:|
| k-NN (k=3) | 0,548 | 0,515 | 0,829 | 0,868 | 0,889 | **0,892** | 0,891 |
| Regressão logística | 0,791 | 0,849 | 0,890 | 0,910 | **0,915** | 0,914 | 0,913 |

Os dois classificadores melhoram até umas 5.000 palavras e depois estabilizam. Ficamos com 10.000: é o
melhor valor do k-NN e praticamente o mesmo da regressão logística. As palavras que ficam de fora (o
vocabulário tem ~17 mil) aparecem uma ou duas vezes no corpus e não ajudam a separar as subáreas. Com uma BoW
muito pequena o k-NN vai mal, porque muitas questões ficam com o vetor quase vazio.

| Variação (10.000 termos) | k-NN | Regressão logística |
|---|---:|---:|
| sem stopwords | 0,888 | 0,909 |
| stopwords do spaCy | **0,892** | 0,914 |
| stopwords + bigramas | 0,876 | **0,918** |
| stopwords + `max_df=0.8` | 0,892 | 0,914 |

As stopwords ajudam um pouco. O `max_df=0.8` do notebook da aula não muda nada, porque depois de tirar as
stopwords nenhuma palavra aparece em 80% das questões. Os bigramas melhoram um pouco a regressão logística,
mas pioram o k-NN e deixam o vocabulário bem maior; ficamos com unigramas.

Vetorizador final: `max_features=10000`, unigramas, stopwords do spaCy, `sublinear_tf=True` e normalização L2.
As palavras de maior peso em cada classe na regressão logística fazem sentido (BD: dados, banco, sql;
Eng. Software: código, desenvolvimento, scrum; Governança: itil, cobit, bpmn; Redes: rede, nuvem, linux;
Segurança: segurança, autenticação, criptografia).

### 3b. Word embeddings

Cada questão vira um único vetor, que vai para os mesmos classificadores. Os modelos não foram ajustados
(sem fine-tuning); só geram os vetores.

- **Estático, spaCy `pt_core_news_lg`:** `doc.vector`, a média dos vetores de 300 dimensões das palavras.
- **Transformer, BERTimbau (`neuralmind/bert-base-portuguese-cased`):** usamos o BERT treinado em português em
  vez do `bert-base-uncased`, que é em inglês. Vetor de 768 dimensões, média dos tokens da última camada, com
  o texto cortado em 512 tokens.

### 3c. Resultados no teste (502 questões)

| Representação | k-NN (F1-macro) | Regressão logística (F1-macro) | Regressão logística (acurácia) |
|---|---:|---:|---:|
| TF-IDF | 0,881 | **0,910** | **0,912** |
| spaCy | 0,426 | 0,832 | 0,851 |
| BERTimbau | 0,753 | 0,804 | 0,813 |

Os relatórios por classe e as matrizes de confusão estão no notebook e em `parte 3/resultados/`.

- **O TF-IDF ganhou com folga, com os dois classificadores.** Termos técnicos decidem a subárea: uma questão
  com "SELECT" ou "ITIL" quase não deixa dúvida, e o TF-IDF dá peso direto a esses termos raros. Nos
  embeddings, a média de todas as palavras dilui esses termos no meio de palavras comuns de prova ("analise",
  "afirmativas", "correto").
- **O rótulo também vem de palavras.** A subárea do corpus foi definida por palavras-chave e, nas questões
  ambíguas, por um TF-IDF com k-NN. O TF-IDF daqui aprende quase a mesma regra que gerou os rótulos, o que
  favorece ele na comparação.
- **O k-NN depende muito da representação.** Com TF-IDF, que já vem normalizado, ele fica perto da regressão
  logística. Com os vetores do spaCy ele desaba (0,43): a média dos vetores das palavras deixa todas as
  questões muito parecidas, e a distância entre elas acaba medindo mais o tamanho do texto que o assunto. A
  regressão logística aprende quais dimensões importam e não sofre com isso.
- **O BERT não foi ajustado.** Sem fine-tuning, ele dá um vetor genérico da frase, que não foi treinado para
  separar assuntos de TI. Com regressão logística ficou um pouco abaixo do spaCy; com k-NN, bem acima.

Governança é a classe mais difícil: é a menor e divide vocabulário com Engenharia de Software (projeto,
processo, requisito). No teste, 26 questões foram erradas pelos três modelos com regressão logística. Lendo
essas questões no fim do notebook, várias são rótulos errados do corpus, não erros dos modelos: uma sobre
COBIT marcada como Engenharia de Software, uma sobre Ajax marcada como Banco de Dados, uma sobre o LibreOffice
Writer, que nem é de computação. Ou seja, os modelos apontam onde o rótulo automático da parte 1 falha.

## Parte 4: similaridade de palavras

Notebook: `parte 4/similaridade.ipynb`. Testamos três modelos nos dois datasets: o nosso (100 pares da parte 2)
e o feito em aula (80 pares, planilha `parte 4/dados/dataset_aula.xlsx`, aba `AmostraParaAnotar`, coluna
"Anotação Final").

| Modelo | Como calculamos a similaridade |
|---|---|
| spaCy `pt_core_news_lg` | cosseno entre os vetores das duas palavras (`similarity`, como no notebook *similaridadeEntreTokens* da aula); termo composto vira a média dos vetores |
| BERTimbau | cosseno entre os vetores de cada palavra isolada (média dos subtokens da última camada) |
| LLM (Gemini 3.5 Flash) | recebe os graus e os exemplos da planilha da aula e dá um grau para cada par |

Os dois datasets ficam na escala da aula (0 a 1): as nossas notas de 1 a 5 viram `(nota - 1) / 4`. A
comparação com as pessoas usa a correlação de Spearman, que compara a ordem dos pares e por isso funciona
mesmo com escalas diferentes (cosseno de -1 a 1 e graus de 0 a 1). A referência humana é a média da Luiza e
da Rafaela no nosso dataset e a anotação final da turma no de aula.

| Modelo | Nosso dataset (Spearman) | Dataset de aula (Spearman) |
|---|---:|---:|
| spaCy | 0,30 | 0,07 |
| BERTimbau | 0,23 | 0,11 |
| Gemini | **0,68** | **0,53** |
| Concordância entre as pessoas (referência) | 0,83 (Luiza × Rafaela) | 0,35 a 0,40 (entre as três alunas) |

- **O LLM ficou muito mais perto das pessoas nos dois datasets.** No nosso, deu a mesma nota da Luiza em 65
  pares e da Rafaela em 68, e sabe que, em TI, "tcp" e "ordem" têm relação (o TCP garante a ordem dos
  pacotes). Foi um pouco mais generoso que as anotadoras (média 0,16 × 0,09): deu 0,5 para pares como
  teste/programação e risco/gestão, que elas avaliaram como 0,25.
- **O spaCy mede outra coisa.** Os vetores dele vêm de textos gerais (notícias, web), não de TI, e medem se as
  palavras aparecem em contextos parecidos. "Operação" e "ti" ficam com similaridade negativa. No dataset de
  aula ainda falta vocabulário: "deployar", "comitar", "parsear", "tokenizar" e "desalocar" não têm vetor
  (contam como similaridade 0), e por isso deployar/publicar, que a turma marcou como sinônimos, sai como
  nada similar.
- **O BERT foi o pior no nosso dataset.** Ele foi feito para representar palavras dentro de frases. Com a
  palavra sozinha, quase todos os pares têm cosseno alto e parecido (metade entre 0,55 e 0,69), então sobra
  pouca diferença entre um par e outro. Ele também confunde palavras do mesmo assunto com sinônimos: dá 0,78
  para vetor/matriz, que a turma marcou como nada similar.
- **Os dois datasets são bem diferentes.** O nosso foi sorteado, então quase todos os pares são pouco
  similares (66 pares com nota 0 das duas). O de aula foi montado com pares escolhidos, quase todos parecidos
  (média 0,69, só 5 pares abaixo de 0,5). Com notas tão concentradas no alto, separar 0,5 de 0,75 ou de 1 é
  difícil até para as pessoas: entre as três alunas o Spearman ficou entre 0,35 e 0,40. O Gemini (0,53)
  concorda mais com a anotação final do que as alunas concordam entre si, enquanto spaCy e BERT ficam perto
  de zero.

### Gemini

As notas do Gemini já estão salvas em `parte 4/dados/notas_llm_nosso.csv` e `notas_llm_aula.csv`, então o
notebook roda sem chamar a API. Para pedir as notas de novo, apague esses arquivos e defina a chave antes de
abrir o notebook:

```bash
export GEMINI_API_KEY="..."
```

A chave é grátis: entre em https://aistudio.google.com, clique em **Get API key** e depois em
**Create API key**. Não coloque a chave em nenhum arquivo do repositório. O plano gratuito permite 20 pedidos
por dia em cada modelo, por isso o notebook manda 25 pares por pedido.

## O que usamos além dos notebooks da disciplina

Seguimos os notebooks da aula sempre que eles cobriam a tarefa: `TfidfVectorizer` com os mesmos parâmetros,
stopwords do spaCy, divisão treino/teste e k-NN do exemplo de classificação, lematização e stopwords com spaCy,
e `similarity` do spaCy para a similaridade entre palavras. O que foi além:

- **Regressão logística (parte 3):** testada ao lado do k-NN, porque costuma ir melhor com TF-IDF e embeddings.
- **Validação cruzada (partes 1 e 3):** para escolher os parâmetros sem usar o conjunto de teste.
- **BERTimbau e Gemini (partes 3 e 4):** pedidos pelo enunciado; os notebooks da aula não tinham exemplo.
- **Kappa de Cohen e correlação de Spearman (partes 2 e 4):** para medir a concordância entre anotadores e
  entre modelos e pessoas.

## Uso de IA

- **Partes 1, 3 e 4:** usamos o Claude (Anthropic), pelo Claude Code, como assistente de programação, para
  escrever e depurar os scripts e os notebooks e para revisar o texto deste README. A conferência das 336
  questões de `parte 1/dados/validacao_rotulos.csv`, usada para medir o acerto da subárea e escolher o
  método de classificação, foi feita com o Claude. Nenhum rótulo do corpus vem dessa conferência.
- **Parte 2:** o Codex (OpenAI) ajudou a implementar e documentar os scripts. As notas dos 100 pares foram
  dadas pela Luiza e pela Rafaela, sem IA.
- **Parte 4:** o LLM avaliado é o Gemini 3.5 Flash, chamado pela API. As notas do dataset de aula foram dadas
  pelas alunas, em aula, sem IA.
