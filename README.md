# T1 PLN - Parte 1: corpus de questões de concursos de TI

Corpus com 2.506 questões de múltipla escolha de computação, tiradas de 95 provas da FGV (2021 a 2026)
disponíveis no [PCI Concursos](https://www.pciconcursos.com.br/provas/ti/). Cada questão tem enunciado,
alternativas, gabarito oficial, ano e subárea.

| Subárea | Questões |
|---|---:|
| Engenharia de Software e Programação | 758 |
| Redes e Infraestrutura | 664 |
| Segurança da Informação | 507 |
| Banco de Dados e Ciência de Dados | 459 |
| Governança e Gestão de TI | 118 |

Tudo da parte 1 está na pasta `parte 1/`. O dataset card é o `parte 1/DATASET_CARD.xlsx`, e as
estatísticas estão em `parte 1/estatisticas.ipynb`.

## Organização

```
parte 1/
  dados/
    pdfs/NN_nome-da-prova/     PDFs da prova e do gabarito (baixados do PCI Concursos)
    txt/NN_nome-da-prova/      texto extraído dos PDFs
    gabaritos_manuais/48.txt   gabarito da prova 48 digitado à mão (o PDF é uma imagem)
  corpus/
    corpus.json                dataset final
    por_subarea/*.json         as mesmas questões separadas por subárea e agrupadas por ano
    questoes/<subárea>/<ano>/  um arquivo .txt por questão ([ENUNCIADO], [ALTERNATIVAS], [GABARITO])
    corpus.csv                 uma linha por questão
  scripts/
    01_pdf_para_txt.py         converte os PDFs em texto
    02_extrair_questoes.py     separa as questões, enunciado e alternativas, e junta o gabarito
    03_filtrar_classificar_exportar.py   filtra, remove duplicadas, classifica e gera o corpus
    gabarito.py, subareas.py, comum.py   funções usadas pelos scripts acima
  estatisticas.ipynb           estatísticas e gráficos do corpus
  DATASET_CARD.xlsx            dataset card
```

## Formato do JSON

`corpus.json` tem um bloco `metadados` e a lista `questoes`. Exemplo de uma questão:

```json
{
  "id": "28-061",
  "subarea": "seguranca_da_informacao",
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
questões iguais de outras provas do mesmo concurso, que foram removidas como duplicadas.

## Como foi feito

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

   Das 6.777 questões extraídas, ficaram 2.506.
5. **Classificação:** a subárea é definida por uma lista de palavras-chave com pesos (`parte 1/scripts/subareas.py`).

## Como rodar

Requer Python 3 e o poppler (`pdftotext`). A partir da raiz do repositório:

```bash
cd "parte 1/scripts"
python3 01_pdf_para_txt.py
python3 02_extrair_questoes.py
python3 03_filtrar_classificar_exportar.py
```

Depois, abra o `parte 1/estatisticas.ipynb` (precisa de `pandas`, `matplotlib` e `pyspellchecker`).

## Limitações

- A classificação por palavras-chave erra em alguns casos de fronteira. Por exemplo, questões de protocolos
  de segurança (IPSec, SSL) às vezes ficam em Redes.
- A prova 53 (MP/RJ) ficou sem questões, porque o gabarito disponível no site é de outro cargo.
- As provas 08 e 46 (CVM, manhã) e 49 (Câmara dos Deputados, manhã) só têm conhecimentos gerais, então não
  contribuíram com questões.
- Usar só a FGV deixa o formato uniforme, mas limita a variedade de estilos de questão.
