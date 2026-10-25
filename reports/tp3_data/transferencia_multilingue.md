# TP3 — teste de transferência multilíngue sem ajuste no PT-BR

Um encoder multilíngue congelado representa textos ingleses do Bitext e reviews
portugueses do B2W. A regressão logística foi treinada em 9200 textos
Bitext (200 por intenção). O único hiperparâmetro escolhido, `C`, foi selecionado
por Macro-F1 em 2300 textos da validação Bitext (50 por intenção). Os 422
rótulos PT-BR foram lidos apenas após essa escolha. Não se usou tradução,
heurística de palavras-chave, nota B2W ou dados PT-BR para treino/seleção.

Modelo: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`; pesos ONNX da revisão `faf4aa4225822f3bc6376869cb1164e8e3feedd0` (SHA-256:
`634d0f66c29dc934c8fa72b8a4fe91dd4d420a22f1d82a241058d4316e659a99`). Semente: 20261024.
SHA-256 Bitext: `69860bec4afcb33875127542d99055839784f0a8aa4431cc38a4cefda882f771`; PT-BR:
`36ddba3b620d73a86802a3863be0eb93dabcc2607b14ee4225f9e9d28b8cb8f0`.

## Seleção no Bitext

| C | Macro-F1 validação | Acurácia validação |
| ---: | ---: | ---: |
| 0.1 | 0.9835 | 0.9835 |
| 1.0 | 0.9904 | 0.9904 |
| 10.0 | 0.9856 | 0.9857 |

Selecionado: `C=1.0`. Esses números não são estimativas de
desempenho em português ou atendimento real.

## Teste externo PT-BR

| Medida | Resultado |
| --- | ---: |
| Casos elegíveis | 422 |
| Acertos | 38 |
| Acurácia | 0.0900 |
| Macro-F1 nas 14 classes com suporte | 0.1318 |
| Previsão constante da classe majoritária, comparação descritiva | 0.6919 |
| Previsões fora das 14 classes com suporte | 273 |

### Por intenção real

| Intenção | Suporte | Recall | F1 |
| --- | ---: | ---: | ---: |
| `submit_product_feedback` | 292 | 0.051 | 0.096 |
| `product_issue` | 46 | 0.109 | 0.175 |
| `delivery_time` | 23 | 0.478 | 0.407 |
| `delivery_issue` | 17 | 0.000 | 0.000 |
| `product_information` | 11 | 0.000 | 0.000 |
| `damaged_delivery` | 6 | 0.167 | 0.100 |
| `missing_item` | 5 | 0.400 | 0.108 |
| `submit_feedback` | 5 | 0.000 | 0.000 |
| `wrong_item` | 5 | 0.400 | 0.308 |
| `shipping_costs` | 4 | 0.250 | 0.250 |
| `technical_issue` | 3 | 0.000 | 0.000 |
| `track_delivery` | 3 | 0.000 | 0.000 |
| `cancel_order` | 1 | 1.000 | 0.400 |
| `exchange_product` | 1 | 0.000 | 0.000 |

### Erros frequentes

| Rótulo humano | Previsão | Casos |
| --- | --- | ---: |
| `submit_product_feedback` | `availability` | 114 |
| `submit_product_feedback` | `submit_product_idea` | 24 |
| `submit_product_feedback` | `pay` | 23 |
| `submit_product_feedback` | `delivery_time` | 17 |
| `product_issue` | `availability` | 12 |
| `submit_product_feedback` | `return_product` | 11 |
| `delivery_issue` | `missing_item` | 10 |
| `submit_product_feedback` | `return_policy` | 8 |
| `delivery_time` | `missing_item` | 7 |
| `product_issue` | `damaged_delivery` | 6 |

## Interpretação

O teste separa parcialmente lacuna de idioma de lacuna de tarefa. O encoder
alinha idiomas, mas o Bitext rotula pedidos de ajuda ao atendimento. Exemplo:
`submit_product_feedback` no Bitext é a intenção de **enviar** uma avaliação;
um review B2W é a avaliação já **escrita**. Nenhum encoder resolve essa diferença
de definição sozinho. A amostra B2W foi estratificada por estrelas, e 292 de 422
casos têm o mesmo rótulo; por isso acurácia isolada é enganosa. Não há estimativa
para as 32 intenções ausentes. O [JSON](transferencia_multilingue.json) contém
predições por ID pseudônimo, sem texto bruto.

Como o mesmo teste externo já foi consultado em uma avaliação anterior, este
novo resultado é análise exploratória de transferência, **não** uma segunda
confirmação independente de desempenho. Para atingir uma meta de 60% de modo
crível em solicitações reais, é necessário coletar dados PT-BR de suporte,
definir rótulos coerentes e reservar uma nova avaliação humana cega.
