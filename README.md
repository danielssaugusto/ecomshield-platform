# E-ComShield Platform

Plataforma de e-commerce voltada a reembolsos, risco e atendimento. Este repositório contém uma API FastAPI e um pipeline reprodutível para transformar avaliações públicas de e-commerce em uma base de temas e intenções de atendimento.

> **Estado atual do dataset:** `b2w-reviews01-intents-v4`. A fonte não possui rótulos humanos de intenção; temas e sentimentos são inferências fracas, determinísticas e rastreáveis. Eles não são verdade de referência para avaliar um modelo.

## Sumário

- [Fonte, licença e escopo](#fonte-licença-e-escopo)
- [Como reproduzir](#como-reproduzir-o-dataset)
- [Limpeza](#limpeza-e-proteção-de-dados)
- [Método de classificação](#método-de-classificação)
- [Taxonomia](#taxonomia-e-escolhas-de-categorização)
- [Resultado](#resultado-da-versão-atual)
- [Formato de saída](#formato-do-dataset-processado)
- [Limitações](#limitações-e-uso-responsável)
- [API local](#executando-a-api)

## Fonte, licença e escopo

A fonte é o [B2W-Reviews01 no Hugging Face](https://huggingface.co/datasets/fgops05/b2w-reviews01): 132.373 avaliações públicas em português, coletadas na Americanas.com entre janeiro e maio de 2018. O corpus foi criado para análise de avaliações, não para classificação de intenções de suporte.

### Justificativa da escolha

O B2W-Reviews01 foi escolhido para o domínio de atendimento de e-commerce porque:

- excede amplamente o mínimo de 500 amostras exigido (132.373 na fonte e 131.307 após limpeza);
- contém texto livre em português (`review_title` e `review_text`), representando a voz do consumidor;
- contém nota de 1 a 5 e contexto de produto, úteis para explorar satisfação e problemas recorrentes;
- possui licença pública e referência acadêmica, o que permite documentar procedência e reprodução;
- traz reclamações reais de logística, produto, pagamento e atendimento, compatíveis com o escopo do E-ComShield.

Como não há uma coluna de intenção original, o projeto cria `intent` e `intent_matches` por regras transparentes. Essa escolha é explicitada para não confundir categorias derivadas com anotações humanas.

| Item | Escolha | Motivo |
| --- | --- | --- |
| Fonte fixada | Commit `4639429ec698d7821fc99a0bc665fa213d9fcd5a` | Evita que o resultado mude se a origem for atualizada. |
| Arquivo | `B2W-Reviews01.csv` | É o arquivo referenciado pelo carregador oficial do dataset. |
| Integridade | SHA-256 `821fb0bf9f7230b0fba4e4f9fadd75a66d1a9ff0b1657810791d33007eb2ab38` | O pipeline interrompe a execução se o arquivo não for exatamente o esperado. |
| Licença | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Atribuição à fonte é necessária ao usar ou redistribuir o material. |
| Dados no Git | Não versionados | O CSV bruto tem cerca de 47 MB e o Parquet gerado cerca de 14 MB; ambos ficam fora do Git por tamanho e licença. |

Referência: Real, L.; Oshiro, M.; Mafra, A. *B2W-Reviews01: an open product reviews corpus* (STIL, 2019).

## Como reproduzir o dataset

Para executar a EDA, use Python 3.10+ com um ambiente virtual próprio. A instalação abaixo é propositalmente independente da API: ela instala somente as bibliotecas necessárias para o dataset e evita conflitos com a configuração de runtime da aplicação.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pandas pyarrow matplotlib seaborn jupyter ipykernel

mkdir -p data/raw/b2w-reviews01
curl -L -o data/raw/b2w-reviews01/B2W-Reviews01.csv \
  https://raw.githubusercontent.com/americanas-tech/b2w-reviews01/4639429ec698d7821fc99a0bc665fa213d9fcd5a/B2W-Reviews01.csv

python3 scripts/build_b2w_intent_dataset.py \
  --input data/raw/b2w-reviews01/B2W-Reviews01.csv \
  --output data/processed/b2w_reviews_intents.parquet \
  --report data/processed/b2w_reviews_intents_report.json
```

O script cria localmente:

- `data/processed/b2w_reviews_intents.parquet`: base limpa e rotulada;
- `data/processed/b2w_reviews_intents_report.json`: checksum, contagens e metadados da execução.

Os arquivos brutos e gerados estão no `.gitignore`: isso evita publicar cópias do dataset e preserva a reprodutibilidade pelo código.

Para abrir a análise já executada ou executá-la novamente, use:

```bash
jupyter notebook notebooks/03_b2w_intent_eda.ipynb
```

O notebook já é versionado com as saídas e os seis gráficos incorporados. Ao abrir o arquivo, as evidências ficam visíveis mesmo antes de clicar em **Run All**.

## Limpeza e proteção de dados

O pipeline em [scripts/build_b2w_intent_dataset.py](scripts/build_b2w_intent_dataset.py) executa estas etapas:

| Etapa | O que é feito | Escolha e justificativa |
| --- | --- | --- |
| 1. Leitura estável | Lê `product_id` como texto e cria `source_row_id`. | Evita perda de formato do identificador e permite auditoria até a linha de origem. |
| 2. Minimização | Não leva ao resultado `reviewer_id`, ano de nascimento, gênero, estado, marca ou nome do produto. | Não são necessários para a inferência e alguns caracterizam o consumidor. |
| 3. Normalização | Unicode NFC, remoção de espaços externos e contração de espaços/tabs/quebras repetidos. | Reduz variações de formatação sem mudar o conteúdo. |
| 4. Mascaramento | E-mails, CPFs e telefones viram `[EMAIL]`, `[CPF]` e `[TELEFONE]`. | Diminui exposição acidental de PII comum no texto de análise. Não garante remoção de toda PII livre. |
| 5. Texto unificado | Concatena `review_title` e `review_text` em `text`. | O título frequentemente contém o problema central; avaliações sem corpo ainda podem ser úteis. |
| 6. Sem conteúdo | Remove apenas registros cujo título **e** corpo ficam vazios. | Preserva títulos informativos, mesmo sem texto longo. |
| 7. Duplicação exata | Remove linhas iguais em todos os campos de origem, exceto `source_row_id`. | Elimina repetição acidental sem apagar textos semelhantes que podem ser avaliações legítimas. |
| 8. Tipagem | Converte data, nota e identificadores para tipos consistentes e grava Parquet. | Parquet é compacto, preserva tipos e funciona bem para análise. |

### Resultado da limpeza

| Métrica | Linhas |
| --- | ---: |
| Fonte bruta | 132.373 |
| Removidas por título e corpo vazios | 112 |
| Removidas por duplicação exata | 954 |
| Dataset processado | **131.307** |

Não há deduplicação semântica, correção automática de português, tradução ou alteração de notas: essas operações poderiam modificar o sentido ou apagar registros válidos.

## Método de classificação

Como a fonte não possui intenções, o pipeline usa **weak labeling** com expressões regulares explícitas.

1. O texto é normalizado para minúsculas e sem acentos para a busca (`“não chegou”` e `“nao chegou”` ativam a mesma regra).
2. Cada **tema** tem termos rastreáveis no dicionário `INTENT_PATTERNS`.
3. Uma avaliação pode acionar vários temas; todos ficam em `intent_matches`, separados por `|`.
4. `intent` recebe o primeiro tema na ordem da taxonomia. Questões financeiras e de pedido têm prioridade sobre comentários de produto porque são mais acionáveis no atendimento.
5. Quando não há tema específico no texto, `intent` recebe `avaliacao_geral`. Isso evita inventar uma intenção operacional a partir da nota.
6. `sentiment` é calculado separadamente como `positivo`, `neutro`, `negativo` ou `misto`. Quando palavras positivas e negativas coexistem, o resultado é `misto`; sem sinal lexical, a nota é usada apenas como fallback de sentimento.

| `label_source` | Significado |
| --- | --- |
| `keyword_heuristic_v4` | O tema veio de um sinal textual explícito. |
| `generic_topic_fallback_v1` | Não havia tema textual específico; `intent` recebeu `avaliacao_geral`. |

`sentiment_source` aplica a mesma transparência ao sentimento: `keyword_heuristic_v1` indica sinal lexical e `rating_fallback_v1` indica inferência exclusivamente pela nota.

Por que não preencher tudo com IA generativa? Sem um conjunto anotado por humanos, isso produziria rótulos difíceis de reproduzir e auditar. As regras são intencionalmente explicáveis: cada rótulo pode ser conferido no próprio texto e refinado em revisão humana.

## Taxonomia e escolhas de categorização

As categorias estão na ordem de prioridade. “Quando entra” mostra exemplos de sinais, não uma lista exaustiva.

| Categoria | Quando entra | Escolha e interpretação |
| --- | --- | --- |
| `estorno_reembolso` | estorno, reembolso, ressarcimento, dinheiro de volta | Maior prioridade por indicar resolução financeira explícita. |
| `cancelamento` | cancelar, cancelado, desistir da compra | Distingue encerramento do pedido de atraso ou devolução posterior. |
| `atraso_entrega` | atraso, demora, não chegou, não recebi, fora do prazo | Agrupa falhas de prazo e entrega não realizada. |
| `item_faltante` | faltou, veio sem, peça/acessório faltante | Pedido parcialmente entregue; “não veio” isolado não basta, pois pode indicar atraso. |
| `embalagem_danificada` | caixa/embalagem aberta, rasgada, amassada ou danificada | A embalagem pode estar comprometida mesmo com item íntegro. |
| `divergencia_anuncio` | propaganda enganosa, anúncio errado, diferente da foto | Descompasso entre a página da oferta e o produto/expectativa. |
| `troca_devolucao` | troca, devolução, coleta | Fluxo pós-compra, sem supor qual foi a causa. |
| `produto_defeituoso` | defeito, quebrado, não funciona, não liga, queimado | Falha de funcionamento do item. |
| `produto_incorreto` | produto/item errado, veio errado, diferente do pedido, voltagem errada | O item entregue não foi o solicitado. |
| `avaria_entrega` | avariado, amassado, produto rasgado/danificado | Dano material associado ao recebimento. |
| `suspeita_autenticidade` | falsificado, pirata, não é original, produto falso | Marca suspeita de falsificação; menções positivas a “original” não são tratadas como problema. |
| `cobranca_pagamento` | cobrança, cartão, pagamento, duplicidade, parcela | Problema financeiro distinto de estorno já solicitado. |
| `frete` | frete, taxa de entrega | Custo/taxa logística, e não prazo. |
| `atendimento` | atendimento, SAC, suporte, ninguém responde | Experiência com canais de contato. |
| `duvida_produto` | gostaria de saber, dimensões, compatibilidade, serve para | Perguntas sobre adequação do produto. |
| `informacao_anuncio` | sem descrição, falta de informação, foto/especificação | Insuficiência de dados na página do item. |
| `entrega_antecipada` | antes do prazo, chegou/entrega rápida | Feedback positivo específico sobre velocidade. |
| `entrega_no_prazo` | dentro/no prazo, prazo cumprido | Feedback positivo sobre cumprimento da promessa logística. |
| `custo_beneficio` | custo-benefício, vale a pena, caro, barato | Relação entre preço e utilidade; pode ser positiva ou negativa. |
| `tamanho_dimensoes` | tamanho, dimensões, pequeno, grande | Tema físico sem inferir sentimento. |
| `qualidade_produto` | qualidade, material, acabamento, resistência, fragilidade | Construção e durabilidade, independente do sentimento. |
| `uso_desempenho` | facilidade de uso, praticidade, desempenho, potência, velocidade, bateria | Experiência de uso e performance. |
| `avaliacao_geral` | nenhum tema textual específico | Categoria honesta de fallback para avaliações vagas; seu tom fica em `sentiment`. |

### Exemplo de múltiplos temas

Para “O pedido foi cancelado, atrasou muito e quero estorno”:

```text
intent_matches = estorno_reembolso|cancelamento|atraso_entrega
intent         = estorno_reembolso
sentiment      = negativo
label_source   = keyword_heuristic_v4
```

Use `intent_matches` quando for importante reconhecer todas as necessidades. `intent` existe para cenários de rótulo único, como dashboards ou classificadores single-label.

## Resultado da versão atual

| Origem do rótulo | Registros | Percentual |
| --- | ---: | ---: |
| Regra textual (`keyword_heuristic_v4`) | 76.375 | 58,17% |
| Tema geral sem sinal específico (`generic_topic_fallback_v1`) | 54.932 | 41,83% |
| **Total** | **131.307** | **100,00%** |

| Categoria | Registros |
| --- | ---: |
| `avaliacao_geral` | 54.932 |
| `qualidade_produto` | 14.094 |
| `atraso_entrega` | 12.141 |
| `entrega_antecipada` | 10.518 |
| `custo_beneficio` | 7.187 |
| `uso_desempenho` | 4.990 |
| `tamanho_dimensoes` | 4.874 |
| `produto_defeituoso` | 4.476 |
| `entrega_no_prazo` | 4.186 |
| `troca_devolucao` | 3.641 |
| `atendimento` | 2.053 |
| `estorno_reembolso` | 1.680 |
| `cancelamento` | 1.369 |
| `cobranca_pagamento` | 787 |
| `divergencia_anuncio` | 759 |
| `frete` | 755 |
| `duvida_produto` | 717 |
| `item_faltante` | 690 |
| `suspeita_autenticidade` | 475 |
| `avaria_entrega` | 443 |
| `produto_incorreto` | 280 |
| `informacao_anuncio` | 215 |
| `embalagem_danificada` | 45 |

Há 22.695 avaliações com mais de um **tema** detectado. Sentimento não entra em `intent_matches`, evitando coocorrências artificiais como “positivo + negativo”; esses casos são registrados como `sentiment=misto`.

### Evidências de EDA para a entrega

O notebook [03_b2w_intent_eda.ipynb](notebooks/03_b2w_intent_eda.ipynb) é a evidência principal da análise do dataset escolhido. Ele executa, com o Parquet presente em `data/processed/`:

- `shape`, tipos, `describe()` e amostra dos registros;
- contagem de valores ausentes, duplicatas e textos vazios;
- distribuição de categorias e proveniência dos rótulos;
- gráfico de barras, histograma, boxplot, heatmap, série temporal e distribuição de sentimento;
- quatro hipóteses sobre intenções e como validá-las posteriormente.

### Checklist de entrega — escopo de dados

| Evidência solicitada | Onde verificar |
| --- | --- |
| Dataset com texto e categoria, com mais de 500 amostras | [README — fonte e justificativa](#fonte-licença-e-escopo) e `intent` no Parquet (131.307 linhas). |
| Fonte, link, licença e motivo da escolha | [Fonte, licença e escopo](#fonte-licença-e-escopo). |
| Shape, tipos, `describe`, ausentes e duplicatas | [Notebook B2W](notebooks/03_b2w_intent_eda.ipynb), células de inspeção e qualidade. |
| Pelo menos três visualizações | Mesmo notebook: seis gráficos incorporados; o script de EDA também os exporta em PNG. |
| Três ou mais hipóteses sobre intenções | Mesmo notebook: seção “Hipóteses orientadas pelos dados”, com quatro hipóteses e formas de validação. |
| Decisões de limpeza | [Limpeza e proteção de dados](#limpeza-e-proteção-de-dados), com oito etapas e justificativas. |

## Formato do dataset processado

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `dataset_version` | texto | Versão das regras aplicadas. |
| `source_row_id` | inteiro | Posição da linha no CSV de origem, para auditoria local. |
| `submission_date` | data/hora | Data de submissão, quando conversível. |
| `product_id` | texto | Identificador do produto na fonte. |
| `product_category` / `product_subcategory` | texto | Categorias de navegação. |
| `overall_rating` | inteiro de 1 a 5 | Nota original do consumidor. |
| `recommend_to_a_friend` | texto | Resposta original Yes/No, quando disponível. |
| `text` | texto | Título e corpo normalizados, com PII comum mascarada. |
| `intent` | texto | Categoria principal pela ordem de prioridade. |
| `intent_matches` | texto nulo ou separado por `|` | Todas as regras textuais acionadas. |
| `label_source` | texto | Método que gerou a categoria. |
| `sentiment` | texto | Tom independente do tema: positivo, neutro, negativo ou misto. |
| `sentiment_source` | texto | Método que gerou o sentimento. |

## Análise exploratória e gráficos

Além do relatório de geração, o projeto oferece uma análise exploratória reproduzível. Ela valida integridade e cria seis gráficos profissionais em `reports/b2w_intents/`, sem versionar imagens ou dados.

```bash
python3 scripts/generate_b2w_eda.py \
  --input data/processed/b2w_reviews_intents.parquet \
  --output-dir reports/b2w_intents
```

| Artefato | Pergunta respondida |
| --- | --- |
| `01_cobertura_rotulos.png` | Qual proporção recebeu tema textual e qual permaneceu como avaliação geral? |
| `02_distribuicao_intencoes.png` | Quais categorias concentram mais avaliações? |
| `03_notas_por_intencao.png` | Como as notas de 1 a 5 se distribuem dentro das categorias mais frequentes? |
| `04_tamanho_texto_por_origem.png` | Textos sem tema explícito tendem a ser mais curtos? |
| `05_coocorrencias.png` | Quais necessidades aparecem juntas com maior frequência? |
| `06_evolucao_mensal.png` | Como as categorias mais recorrentes evoluem ao longo dos meses? |
| `07_distribuicao_sentimento.png` | Como o tom positivo, neutro, negativo ou misto se distribui sem contaminar os temas? |
| `relatorio.md` | Quais são as métricas, distribuições e coocorrências num formato consultável? |

Os gráficos não “validam” os rótulos: eles servem para identificar desequilíbrio, cobertura insuficiente, comportamento temporal e candidatos à revisão humana.

### Amostra para validação humana

O script abaixo cria uma amostra estratificada por tema e sentimento, já com texto mascarado e colunas para o revisor registrar o rótulo correto, a decisão e observações. O CSV resultante é local e não entra no Git.

```bash
python3 scripts/create_b2w_review_sample.py \
  --input data/processed/b2w_reviews_intents.parquet \
  --output data/processed/b2w_manual_review_sample.csv \
  --per-intent 25 \
  --per-sentiment 25
```

Essa amostra é o ponto de partida para calcular precisão por tema e sentimento antes de qualquer uso supervisionado.

## Limitações e uso responsável

- O dataset representa avaliações de 2018; não descreve automaticamente clientes atuais.
- Palavras-chave não entendem ironia, contexto complexo ou todos os erros ortográficos.
- `intent` é uma hipótese temática baseada em texto; quando não há tema, recebe `avaliacao_geral`. `sentiment` pode usar a nota como fallback e também não é anotação humana certificada.
- O mascaramento cobre padrões comuns, não todo dado pessoal livre. Trate o texto como potencialmente sensível.
- Não use essas classes como único critério para decisão financeira, cancelamento automático ou ação contra clientes/vendedores.

### Próximos passos recomendados

1. Revisar uma amostra estratificada por categoria, em especial as classes pequenas, `avaliacao_geral` e o sentimento derivado por nota.
2. Escrever guia de anotação com casos positivos, negativos e ambíguos.
3. Criar conjunto de validação anotado por pelo menos duas pessoas e medir concordância.
4. Só então treinar e avaliar um modelo supervisionado, preservando `label_source` para separar rótulos humanos dos fracos.

## Executando a API

```bash
uvicorn ecomshield.main:app --reload
```

- Health check: <http://127.0.0.1:8000/health>
- Swagger: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

## Arquivos relevantes

- [scripts/build_b2w_intent_dataset.py](scripts/build_b2w_intent_dataset.py): limpeza, classificação e relatório.
- [tests/test_b2w_intent_dataset.py](tests/test_b2w_intent_dataset.py): testes das regras principais.
