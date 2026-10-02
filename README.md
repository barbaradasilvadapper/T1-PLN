# T1 PLN - Corpus de questões de concursos de TI e similaridade de palavras

Grupo: Ana Carolina Poletto, Bárbara Dapper, João Pedro Martins, Luiza Pasini e Rafaela Remião.

| Parte | Pasta | O que tem |
|---|---|---|
| 1. Corpus de questões | [`parte 1/`](parte%201/) | 2.504 questões da FGV com gabarito e subárea, estatísticas e dataset card |
| 2. Corpus de similaridade | [`parte 2/`](parte%202/README.md) | 100 pares de palavras anotados por duas pessoas, concordância e dataset card |
| 3. Classificação | [`parte 3/`](parte%203/) | TF-IDF, spaCy e BERT classificando as questões por subárea |
| 4. Similaridade de palavras | [`parte 4/`](parte%204/) | spaCy, BERT e LLM comparados com as notas humanas |

Para instalar tudo:

```bash
pip install -r requirements.txt
```

A parte 1 também precisa do `pdftotext` (pacote poppler) só se for refazer a conversão dos PDFs.

## Parte 1: corpus de questões

Corpus com 2.504 questões de múltipla escolha de computação, tiradas de 95 provas da FGV (2021 a 2026)
disponíveis no [PCI Concursos](https://www.pciconcursos.com.br/provas/ti/). Cada questão tem enunciado,
alternativas, gabarito oficial, ano e subárea.

| Subárea | Questões |
|---|---:|
| Engenharia de Software e Programação | 720 |
| Redes e Infraestrutura | 651 |
| Segurança da Informação | 517 |
| Banco de Dados e Ciência de Dados | 465 |
| Governança e Gestão de TI | 151 |

O dataset card é o `parte 1/DATASET_CARD.xlsx` (template da disciplina) e as estatísticas estão em
`parte 1/estatisticas.ipynb`.

### Organização

```
parte 1/
  dados/
    pdfs/NN_nome-da-prova/     PDFs da prova e do gabarito (baixados do PCI Concursos)
    txt/NN_nome-da-prova/      texto extraído dos PDFs
    gabaritos_manuais/48.txt   gabarito da prova 48 digitado à mão (o PDF é uma imagem)
    revisao_rotulos.csv        subáreas corrigidas à mão (ver "Revisão dos rótulos")
    intermediario/             todas as questões extraídas, antes do filtro
  corpus/
    corpus.json                dataset final
    por_subarea/*.json         as mesmas questões separadas por subárea e agrupadas por ano
    questoes/<subárea>/<ano>/  um arquivo .txt por questão ([ENUNCIADO], [ALTERNATIVAS], [GABARITO])
    corpus.csv                 uma linha por questão
    descartadas.json           questões removidas e o motivo
    validacao_manual.json      conferência de uma amostra de 100 questões
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
questões iguais de outras provas do mesmo concurso, que foram removidas como duplicadas. `origem_subarea` diz se
a subárea veio do classificador de palavras-chave ou da revisão manual.

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

   Das 6.777 questões extraídas, ficaram 2.504. Os motivos de cada descarte estão em `corpus/descartadas.json`.
5. **Classificação:** a subárea é definida por uma lista de palavras-chave com pesos (`parte 1/scripts/subareas.py`)
   e depois revisada (abaixo).

### Revisão dos rótulos (versão 1.1)

Na parte 3 percebemos que parte dos erros dos classificadores eram, na verdade, rótulos errados: a lista de
palavras-chave mandava para Engenharia de Software ou Redes questões de COBIT, ITIL, BPMN, OAuth, IPSec,
forense etc. Para achar esses casos sem ler as 2.506 questões, treinamos um TF-IDF + regressão logística com
validação cruzada (10 partes) e listamos as 236 questões em que a previsão discordava do rótulo. Cada uma foi lida e:

- 122 mudaram de subárea;
- 2 saíram do corpus por não serem de computação (contratações sustentáveis e editor de texto), mais a cópia
  de uma delas que existia em outra prova;
- as outras ficaram como estavam (o rótulo estava certo e o modelo errou).

Depois foi conferida uma amostra aleatória de 100 questões, 20 por subárea. 97 estavam certas, e os 3 erros
também foram corrigidos. Todas as correções estão em `dados/revisao_rotulos.csv` com o assunto da questão, e o
script 03 aplica esse arquivo por cima do classificador, então o corpus continua reproduzível.

Uma ressalva: como só revisamos as questões em que o TF-IDF discordava, os erros que o TF-IDF e as
palavras-chave cometem juntos continuam no corpus. A amostra de 100 dá uma ideia de quantos sobraram (~3%).

### Como rodar

```bash
cd "parte 1/scripts"
python3 01_pdf_para_txt.py
python3 02_extrair_questoes.py
python3 03_filtrar_classificar_exportar.py
```

Depois, abra o `parte 1/estatisticas.ipynb`.

### Limitações

- Mesmo depois da revisão, sobram casos de fronteira (protocolos de segurança × redes, estatística × BD).
- Governança tem só 151 questões; as outras quatro subáreas têm entre 465 e 720.
- A prova 53 (MP/RJ) ficou sem questões, porque o gabarito disponível no site é de outro cargo.
- As provas 08 e 46 (CVM, manhã) e 49 (Câmara dos Deputados, manhã) só têm conhecimentos gerais, então não
  contribuíram com questões.
- Usar só a FGV deixa o formato uniforme, mas limita a variedade de estilos de questão.

## Parte 2: corpus de similaridade de palavras

Os scripts, as anotações, o corpus e o dataset card da parte 2 estão em [`parte 2/`](parte%202/README.md).
A escala de anotação, a metodologia e os comandos estão no README dessa pasta.

A parte 2 foi gerada a partir da versão 1.0 do corpus (2.506 questões). A revisão da versão 1.1 tirou só 3
questões, o que não muda as 200 palavras escolhidas de forma relevante, então mantivemos os pares já anotados.

## Parte 3: classificação das questões por subárea

Todos os modelos usam o mesmo texto (enunciado + alternativas) e a mesma divisão: 80% treino e 20% teste,
estratificada, com `random_state=42` (igual ao notebook de exemplo da disciplina). Os parâmetros foram
escolhidos com validação cruzada de 5 partes só no treino; o teste foi usado uma vez, no fim. Como as classes
são desbalanceadas, a métrica principal é o F1-macro.

```bash
python3 "parte 3/scripts/01_tfidf.py"        # 3a: BoW + TF-IDF
python3 "parte 3/scripts/02_embeddings.py"   # 3b: spaCy e BERT
python3 "parte 3/scripts/03_analise.py"      # 3c: comparação e matrizes de confusão
```

As saídas ficam em `parte 3/classificacao/`.

### 3a. BoW + TF-IDF

`TfidfVectorizer` com minúsculas e TF logarítmico (`sublinear_tf=True`), e regressão logística com
`class_weight="balanced"` por causa de Governança. Testamos, nessa ordem:

| Tamanho da BoW (`max_features`) | 200 | 500 | 1.000 | 2.000 | 5.000 | 10.000 | todas |
|---|---:|---:|---:|---:|---:|---:|---:|
| F1-macro (CV) | 0,776 | 0,854 | 0,890 | 0,914 | **0,921** | 0,921 | 0,920 |

Até umas 2.000 palavras o resultado sobe rápido; depois de 5.000 não muda mais. Ficamos com 5.000 porque dá o
mesmo resultado com metade do vocabulário (o corpus tem ~17 mil types).

| Variação (com 5.000 termos) | F1-macro (CV) |
|---|---:|
| unigramas, `min_df=1` | 0,921 |
| unigramas + bigramas | 0,914 |
| `min_df=5` | 0,918 |
| stopwords do spaCy | **0,927** |
| stopwords do spaCy + `max_df=0.8` | 0,927 |
| lemas sem stopwords (pré-processamento da parte 2) | 0,916 |
| k-NN (k=3) no lugar da regressão logística | 0,884 |

Bigramas e lematização não ajudaram: com ~2 mil questões, os bigramas ficam raros demais, e o lematizador do
spaCy erra bastante termo técnico. As stopwords ajudaram um pouco. O `max_df=0.8` não mudou nada porque
nenhuma palavra que sobra depois das stopwords aparece em 80% das questões. O k-NN do notebook da disciplina
ficou 4 pontos atrás: em vetores com milhares de dimensões, a distância entre duas questões diz pouco.

Modelo final: 5.000 termos, unigramas, stopwords do spaCy, regressão logística. As palavras com mais peso
em cada classe fazem sentido (BD: dados, banco, sql, tabela; Redes: rede, nuvem, linux, ip; Segurança:
segurança, autenticação, criptografia, ataque; Governança: itil, processos, projetos, governança).

### 3b. Word embeddings

Cada questão vira um vetor, e o vetor vai para a mesma regressão logística (com padronização). Os modelos
não foram ajustados (sem fine-tuning), só usados para gerar os vetores.

- **Estático, spaCy `pt_core_news_lg`:** vetor de 300 dimensões, média dos vetores das palavras da questão.
- **Transformer, BERTimbau (`neuralmind/bert-base-portuguese-cased`):** usamos a versão em português do BERT
  em vez do `bert-base-uncased`, que é treinado em inglês. Vetor de 768 dimensões, média dos tokens da
  última camada (ignorando o padding), com o texto cortado em 512 tokens.

### 3c. Resultados no teste (501 questões)

| Modelo | F1-macro | Acurácia | BD | Eng. Software | Governança | Redes | Segurança |
|---|---:|---:|---:|---:|---:|---:|---:|
| TF-IDF + regressão logística | **0,944** | **0,948** | 0,97 | 0,96 | 0,92 | 0,95 | 0,91 |
| BERTimbau | 0,862 | 0,868 | 0,88 | 0,88 | 0,83 | 0,85 | 0,87 |
| spaCy `pt_core_news_lg` | 0,840 | 0,862 | 0,84 | 0,88 | 0,73 | 0,89 | 0,86 |

(colunas por subárea = F1 de cada classe; matrizes de confusão em `parte 3/classificacao/matrizes_confusao.png`)

O TF-IDF ganhou com folga, e achamos que por três motivos:

1. **Vocabulário técnico decide a classe.** Uma questão com "SELECT" ou "ITIL" quase não deixa dúvida. O
   TF-IDF dá peso direto a esses termos raros. Nos embeddings, a média de todas as palavras dilui esses termos
   no meio de palavras comuns ("analise", "afirmativas", "correto").
2. **Os rótulos favorecem o TF-IDF.** A subárea veio de uma lista de palavras-chave, e a revisão só olhou as
   questões em que o TF-IDF discordava. Ou seja, o TF-IDF aprende quase a mesma regra que gerou os rótulos. Os
   três modelos melhoraram com a revisão (TF-IDF 0,887 → 0,944, BERT 0,816 → 0,862, spaCy 0,813 → 0,840), mas
   o TF-IDF ganhou mais.
3. **O BERT não foi ajustado.** Sem fine-tuning, ele só dá um vetor genérico do texto. Mesmo assim ficou um
   pouco acima do spaCy, principalmente em Governança (0,83 × 0,73), onde o contexto ajuda mais que palavras
   soltas.

Governança é a classe mais difícil para todos: é a menor e divide vocabulário com Engenharia de Software
(projeto, processo, requisito). Das 501 questões de teste, 389 foram acertadas pelos três modelos e só 11
foram erradas pelos três. Lendo essas 11 (`parte 3/classificacao/COMPARACAO.md`), a maioria é caso de
fronteira de verdade: firewall no Linux, VPN, SELinux, continuidade de negócios. Algumas, como uma de funções
hash rotulada como Engenharia de Software, parecem ser rótulos que ainda estão errados.

## Parte 4: similaridade de palavras

Usamos os 100 pares da parte 2 e comparamos a similaridade dada por cada modelo com a média das notas da Luiza
e da Rafaela, pela correlação de Spearman (que compara ordens e não exige que as escalas sejam iguais).

```bash
export ANTHROPIC_API_KEY=...                     # chave da API da Anthropic
python3 "parte 4/scripts/01_notas_llm.py"        # notas do LLM
python3 "parte 4/scripts/02_similaridade.py"     # spaCy, BERT e comparação
```

| Modelo | Como calculamos a similaridade |
|---|---|
| spaCy `pt_core_news_lg` | cosseno entre os vetores das duas palavras (`token.similarity`, como no notebook da aula) |
| BERTimbau | cosseno entre os vetores de cada palavra isolada (média dos subtokens da última camada) |
| LLM (Claude Opus 5.5) | o modelo recebe a mesma escala de 1 a 5 e as mesmas instruções que as anotadoras e dá uma nota |

| Modelo | Spearman com a média | com a Luiza | com a Rafaela |
|---|---:|---:|---:|
| spaCy | 0,30 | 0,33 | 0,28 |
| BERTimbau | 0,23 | 0,28 | 0,21 |
| LLM | *rodar o 01_notas_llm.py* | | |
| Luiza × Rafaela (referência) | 0,83 | | |

- **spaCy e BERT ficaram bem longe das pessoas.** O spaCy mede se as palavras aparecem em contextos parecidos
  em textos gerais (notícias, web), não no domínio de TI. Por isso "tcp" e "ordem" ficam longe para ele, mas
  as anotadoras lembraram que o TCP garante a ordem dos pacotes.
- **O BERT foi ainda pior.** Ele foi feito para gerar vetores de palavras dentro de frases. Com a palavra
  sozinha, quase todos os pares ficam com cosseno alto e parecido (metade deles entre 0,55 e 0,69), então
  sobra pouca diferença entre um par e outro.
- **A distribuição das notas atrapalha.** 66 dos 100 pares tiveram nota 1 das duas anotadoras (os pares foram sorteados), então há
  muitos empates e poucos pares com similaridade alta, o que baixa qualquer correlação.

O enunciado também pede o dataset de palavras feito em aula (os pares em que cada aluno deu uma nota e depois
a turma chegou a um acordo). Para incluir, salve como `parte 4/dados/dataset_aula.csv` com as colunas
`palavra_1, palavra_2, similaridade` e rode os dois scripts de novo.

## Uso de IA

Usamos o Claude (Anthropic), pelo Claude Code, como assistente de programação nas partes 1, 3 e 4: ele ajudou a
escrever e depurar os scripts, e fez a leitura das 236 questões suspeitas e da amostra de 100 que deram
origem às correções de subárea (`revisao_rotulos.csv`, `validacao_manual.json`). Na parte 2, o Codex (OpenAI) ajudou na implementação dos scripts; as notas dos 100 pares
foram dadas pela Luiza e pela Rafaela, sem IA. Na parte 4, o LLM avaliado é o Claude Opus 5.5, chamado pela API.
