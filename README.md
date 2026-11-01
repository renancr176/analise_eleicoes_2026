# Eleições 2026 — Presidente: análise estatística 1º × 2º turno

Análise estatística, seção por seção, da eleição presidencial de 2026, comparada com 2014, 2018 e 2022, a partir dos dados abertos do TSE.

**[Abrir a análise (analise_eleicoes_2026.html)](analise_eleicoes_2026.html)**

> ### Conteúdo gerado por inteligência artificial
> Esta análise foi feita pela IA **Claude** (Anthropic), a pedido do autor do repositório. O Claude escreveu os scripts, processou os dados, fez os testes estatísticos e gerou a página de gráficos e os textos. Os números foram conferidos contra os totais oficiais do TSE, mas o conteúdo pode ter erros. Para auditar, use os scripts abaixo e refaça a análise.

## O que a análise contém

- Conferência dos totais com o resultado oficial do TSE.
- Fluxo de votos entre o 1º e o 2º turno (regressão ecológica de Goodman, com e sem efeito fixo de município).
- Resultados por estado e região, comparecimento e votos brancos e nulos.
- Testes de anomalias aplicados igualmente a 2014, 2018, 2022 e 2026:
  - seções atípicas (z-score robusto);
  - seções com 100% para um candidato;
  - "impressão digital" eleitoral (comparecimento × votos);
  - testes de dígitos (Benford e último dígito);
  - modelo de urna;
  - curva da apuração.
- Cruzamento por município entre eleições consecutivas.

**Importante:** "anomalia" aqui significa desvio estatístico em relação ao padrão, **não prova de fraude**. A regressão ecológica estima o comportamento de grupos de eleitores, não de pessoas.

## Fonte dos dados

Todos os arquivos vêm do Portal de Dados Abertos do TSE:

- https://dadosabertos.tse.jus.br/dataset/resultados-2014
- https://dadosabertos.tse.jus.br/dataset/resultados-2018
- https://dadosabertos.tse.jus.br/dataset/resultados-2022
- https://dadosabertos.tse.jus.br/dataset/resultados-2026

Os arquivos originais somam cerca de 12 GB e **não estão neste repositório**. Para refazer a análise, baixe-os do TSE (veja abaixo).

## Como regerar a análise

### Pré-requisitos

- **Python 3.11 ou mais novo.** A opção `-P` usada nos comandos não existe em versões anteriores. Foi testado com Python 3.12.
- **numpy.** Foi testado com a versão 2.5. Instale com:
  ```
  pip install numpy
  ```
- **Espaço em disco:** cerca de 6 GB para os zips usados e mais algumas centenas de MB para os arquivos intermediários.
- **Memória:** 8 GB de RAM são suficientes.

### Arquivos a baixar do TSE

Coloque estes arquivos, **sem descompactar**, numa pasta chamada `dados/`:

| Arquivo | Onde encontrar |
|---|---|
| `votacao_secao_2014_BR.zip`, `votacao_secao_2018_BR.zip`, `votacao_secao_2022_BR.zip`, `votacao_secao_2026_BR.zip` | "Votação por seção eleitoral" de cada ano (arquivo BR) |
| `detalhe_votacao_secao_2014.zip`, `detalhe_votacao_secao_2018.zip`, `detalhe_votacao_secao_2022.zip`, `detalhe_votacao_secao_2026.zip` | "Detalhe da apuração por seção eleitoral" de cada ano |
| `Historico_Totalizacao_Presidente_BR_1T_2022.zip`, `Historico_Totalizacao_Presidente_BR_2T_2022.zip` | Dataset de 2022, "Histórico de totalização" (usado para validar a curva da apuração) |

### Script

Rode na pasta raiz do repositório, que contém `scripts/` e `dados/`. Os comandos abaixo funcionam no Windows (PowerShell), no Linux e no macOS. A extração dos dados leva vários minutos por ano.

```bash
mkdir trabalho

# 1) Extração: lê os zips do TSE e gera uma tabela por seção (1º e 2º turno) para cada ano
python -P scripts/extract.py   dados trabalho/secoes.npz
python -P scripts/extract_y.py dados trabalho/sec_2014.npz 2014 13 45 40
python -P scripts/extract_y.py dados trabalho/sec_2018.npz 2018 13 17 12
python -P scripts/extract_y.py dados trabalho/sec_2022.npz 2022 13 22 15

# 2) Análises estatísticas de cada ano
python -P scripts/analyze.py trabalho/secoes.npz   trabalho/res.json
python -P scripts/analyze.py trabalho/sec_2014.npz trabalho/res_2014.json
python -P scripts/analyze.py trabalho/sec_2018.npz trabalho/res_2018.json
python -P scripts/analyze.py trabalho/sec_2022.npz trabalho/res_2022.json

# 3) Cruzamento entre eleições e curva oficial de 2022
python -P scripts/cross.py  trabalho trabalho/cross.json
python -P scripts/hist22.py dados    trabalho/hist22.json

# 4) Teste de robustez de brancos/nulos e montagem do HTML (rodar de dentro de trabalho/)
cd trabalho
python -P ../scripts/bn_check.py
python -P ../scripts/build.py ../analise_eleicoes_2026.html
cd ..
```

O resultado é o arquivo `analise_eleicoes_2026.html`, autocontido, com todos os dados embutidos. Ele abre em qualquer navegador e só precisa de internet para carregar a biblioteca de gráficos (Chart.js).

Nos comandos de `extract_y.py`, os três números finais são os números de urna do candidato do PT, do adversário no 2º turno e do terceiro colocado de cada ano:

| Ano | PT | Adversário no 2º turno | Terceiro colocado |
|---|---|---|---|
| 2014 | 13 (Dilma) | 45 (Aécio) | 40 (Marina) |
| 2018 | 13 (Haddad) | 17 (Bolsonaro) | 12 (Ciro) |
| 2022 | 13 (Lula) | 22 (Bolsonaro) | 15 (Simone) |

### Estrutura

```
scripts/
  extract.py     extração 2026 (seção a seção, 1º e 2º turno)
  extract_y.py   extração genérica para 2014, 2018 e 2022
  analyze.py     estatísticas por ano (Goodman, outliers, impressão digital, dígitos, curva...)
  cross.py       cruzamento municipal entre eleições
  hist22.py      curva oficial de totalização de 2022
  bn_check.py    robustez do fluxo de brancos/nulos (efeito fixo de município)
  build.py       injeta os resultados no template e gera o HTML
  template.html  página com os gráficos (Chart.js)
analise_eleicoes_2026.html   resultado final
```
