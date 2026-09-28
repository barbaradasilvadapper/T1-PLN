# T1 PLN – Parte 1: corpus de questões de concursos de TI (QuestõesTI-FGV)

Corpus de **2.506 questões de múltipla escolha de computação** de 95 provas da banca FGV (2021–2026),
coletadas do [PCI Concursos](https://www.pciconcursos.com.br/provas/ti/), com enunciado, alternativas,
gabarito oficial, ano e subárea.

| Subárea | Questões |
|---|---:|
| Engenharia de Software e Programação | 758 |
| Redes, Sistemas Operacionais e Infraestrutura | 664 |
| Segurança da Informação | 507 |
| Banco de Dados e Ciência de Dados | 459 |
| Governança e Gestão de TI | 118 |

Estatísticas completas em [`corpus/estatisticas/ESTATISTICAS.md`](corpus/estatisticas/ESTATISTICAS.md) e
documentação no formato da disciplina em [`DATASET_CARD.xlsx`](DATASET_CARD.xlsx) / [`DATASET_CARD.md`](DATASET_CARD.md).

## Como cada item do enunciado foi atendido

| Item | Onde / como |
|---|---|
| **a.** ≥ 3 subáreas, ≥ 500 questões cada | 3 subáreas com mais de 500 (Eng. Software 758, Redes 664, Segurança 507) e mais 2 menores (BD 459, Governança 118). A subárea é atribuída por questão (`scripts/subareas.py`). |
| **b.** concursos dos últimos 6 anos | Todas as provas são de 2021 a 2026. |
| **c.** PDF → TXT | `scripts/01_pdf_para_txt.py` → `dados/txt/NN_prova/prova.txt` e `gabarito.txt` |
| **d.** filtrar e pré-processar | `scripts/02_extrair_questoes.py` marca problemas de conversão; `scripts/03_filtrar_classificar_exportar.py` descarta (motivos em `corpus/descartadas.json`) |
| **e.** organizar por ano, questão e subárea | `corpus/questoes/<subárea>/<ano>/<id>.txt` (seções `[ENUNCIADO]`, `[ALTERNATIVAS]`, `[GABARITO]`) e `corpus/por_subarea/<subárea>.json` (agrupado por ano) |
| **f.** gabarito | Campo `gabarito` (letra) e `resposta_correta` (texto) em cada questão |
| **g.** estatísticas | `scripts/04_estatisticas.py` → `corpus/estatisticas/` (JSON, Markdown e 4 gráficos) |
| **h.** exportar para JSON | `corpus/corpus.json` (estrutura abaixo) |
| **i.** dataset card | `scripts/05_dataset_card.py` preenche o template da professora → `DATASET_CARD.xlsx` |

## Estrutura das pastas

```
T1/
├── rodar_tudo.sh                  # refaz todo o pipeline
├── DATASET_CARD.xlsx / .md        # item i
├── docs/templateDatasetCard.xlsx  # template da disciplina
├── dados/
│   ├── lista_provas.csv           # as 95 provas: nº, foco do cargo, ano, slug, URL
│   ├── pdfs/NN_slug/              # PDFs originais (prova + gabarito)
│   ├── gabaritos_manuais/48.txt   # gabarito transcrito (o PDF é imagem escaneada)
│   ├── txt/NN_slug/               # textos convertidos
│   └── intermediario/             # todas as questões extraídas + relatório por prova
├── corpus/
│   ├── corpus.json                # DATASET FINAL
│   ├── por_subarea/*.json
│   ├── questoes/<subárea>/<ano>/<id>.txt
│   ├── corpus.csv
│   ├── descartadas.json           # questões removidas e o motivo
│   ├── validacao_manual.json      # conferência da classificação numa amostra
│   ├── qualidade_lexica.json
│   └── estatisticas/
└── scripts/
```

## Estrutura do JSON (`corpus/corpus.json`)

```json
{
  "metadados": { "nome": "QuestõesTI-FGV", "versao": "1.0", "data": "...", "total_questoes": 2506,
                 "subareas": { "seguranca_da_informacao": { "nome": "Segurança da Informação", "questoes": 507 }, "...": {} },
                 "campos": { "...": "descrição de cada campo" } },
  "questoes": [
    {
      "id": "28-061",
      "subarea": "seguranca_da_informacao",
      "ano": 2023,
      "banca": "FGV",
      "cargo_orgao": "analista judiciario analise de sistemas redes tj se",
      "prova": "28_analista-judiciario-analise-de-sistemas-redes-tj-se-fgv-2023",
      "url_prova": "https://www.pciconcursos.com.br/provas/download/...",
      "numero_na_prova": 61,
      "secao_na_prova": "Conhecimentos Específicos",
      "enunciado": "O computador de Elias foi infectado por um rootkit que ...",
      "alternativas": [ { "letra": "A", "texto": "memória;" }, { "letra": "B", "texto": "kernel;" }, "..." ],
      "gabarito": "A",
      "resposta_correta": "memória;",
      "tambem_em": [],
      "pontuacao_subareas": { "seguranca_da_informacao": 4, "redes_e_infraestrutura": 3, "...": 0 }
    }
  ]
}
```

`id` = `NN-QQQ` (nº da prova em `lista_provas.csv` e nº da questão). `tambem_em` lista questões idênticas
de outras provas do mesmo concurso, que foram removidas como duplicatas.

## Pipeline

1. **Coleta.** Levantamento de todas as provas de TI do PCI Concursos (1.526 de 2021–2026). Foram
   escolhidas 95 da FGV com gabarito, priorizando cargos cuja prova é quase toda de TI e equilibrando os
   focos (desenvolvimento, dados, redes, segurança). O site exige uma verificação de segurança (captcha) por
   prova, então os PDFs foram baixados manualmente para `dados/pdfs/`. Usar uma única banca mantém o
   formato estável e o parser confiável.
2. **Conversão (c).** `pdftotext -bbox-layout` com reordenação dos blocos por coluna: as provas FGV são
   em duas colunas e a conversão direta embaralha as questões. Os gabaritos usam `pdftotext -layout`.
3. **Separação (d, e, f).**
   - Remoção de cabeçalhos e rodapés.
   - Detecção das seções da prova ("Língua Portuguesa", "Conhecimentos Específicos"…).
   - Início de cada questão pelo número sequencial seguido de "(A)"; separação do enunciado e das alternativas (A)–(E) ou (A)–(D).
   - Textos compartilhados ("Texto 1", "Considere o código… nas duas questões a seguir") vão para a questão seguinte.
   - Gabarito: o arquivo traz dezenas de cargos e tipos de prova. O bloco certo é escolhido pelo número de
     questões, Tipo 1 e similaridade com o nome do cargo, e todas as 95 escolhas foram conferidas
     (`dados/intermediario/relatorio_extracao.csv`).
4. **Filtro (d).** Uma questão é descartada se:
   - é de outra matéria (seção de português, direito, raciocínio lógico etc., ou sem termos de TI);
   - teve problema de conversão:
     - símbolo de fonte especial não convertido;
     - expoente, índice ou tabela quebrados em linhas soltas;
     - alternativas faltando ou vazias;
     - duas questões grudadas;
     - depende de figura;
     - cita um texto ou tabela que não está no enunciado;
   - não tem gabarito ou foi anulada;
   - é duplicata (similaridade ≥ 0,9) de questão já incluída.
5. **Classificação (a).** Dicionário de termos por subárea com pesos 2 (característicos) e 1 (genéricos, contados uma vez por questão).
   - A questão precisa de pelo menos um termo característico.
   - Nos empates apertados, segurança tem prioridade, porque costuma aparecer dentro de contextos de redes ou de software.
6. **Estatísticas (g), JSON (h) e dataset card (i).**

## Como rodar

```bash
cd T1
./rodar_tudo.sh
```

Requer Python 3, poppler (`pdftotext`), `matplotlib` e `openpyxl`. A medida de qualidade léxica
(`04b_qualidade_lexica.py`) precisa de `pip install pyspellchecker`. Sem esse pacote, o script é pulado e o
último `corpus/qualidade_lexica.json` é mantido.

## Validação e limitações

- **Classificação.** Numa amostra aleatória estratificada de 89 questões do corpus final, conferida manualmente
  com auxílio do Claude (IA), 89/89 são de computação e **83/89 (93%)** estão na subárea correta
  (`corpus/validacao_manual.json`). Os erros são sobretudo questões de protocolos de segurança (IPSec, SSL,
  DNSSEC, RADIUS) que ficaram em Redes. As fronteiras entre subáreas são naturalmente difusas (ex.: backup,
  servidores de aplicação).
- **Qualidade do texto.** 94,2% dos tokens alfabéticos são reconhecidos por dicionários de português ou
  inglês. É um limite inferior: os não reconhecidos são siglas e termos técnicos, além de palavras comuns
  ausentes do dicionário.
- **Provas sem contribuição.**
  - 53 (MP/RJ): o gabarito publicado no PCI é de outro cargo, então as questões ficaram sem gabarito.
  - 08 e 46 (CVM, manhã) e 49 (Câmara dos Deputados, manhã): são provas de conhecimentos gerais, sem questões de TI.
- **Gabarito da prova 48.** O PDF é uma imagem escaneada; o gabarito foi transcrito manualmente em
  `dados/gabaritos_manuais/48.txt`.
- **Banca única (FGV).** Isso dá consistência, mas limita a diversidade de estilo das questões.
