# TP3 — pergunta de classificação de intenção

**Pergunta:** dado o texto de uma solicitação de atendimento ao cliente, qual é
a intenção expressa pelo usuário? A entrada será apenas o texto da solicitação
(`text`); a saída, uma das 46 intenções nominais publicadas no campo `intent`
do Bitext Retail eCommerce. A categoria é uma taxonomia auxiliar, não um número
ordinal. Resposta de referência, tags e nota de avaliação não entram como
preditores do classificador.

## Dados e distribuição das classes

O corpus preparado tem **44.884 solicitações em inglês**, distribuídas em
**13 categorias e 46 intenções**. As classes têm de **721 a 1.000** exemplos
(razão máximo/mínimo ≈ 1,39). A tabela apresenta a frequência de cada classe
no corpus completo; a figura [distribuição por intenção](../bitext_retail_intents/02_distribuicao_intencoes.png)
permite compará-las visualmente.

| Intenção (n) | Intenção (n) | Intenção (n) |
| --- | --- | --- |
| `add_product` (957) | `open_account` (987) | `return_product_in_store` (994) |
| `availability` (972) | `order_history` (988) | `return_product_online` (993) |
| `availability_in_store` (756) | `pay` (990) | `sales_period` (995) |
| `availability_online` (993) | `payment_issue` (996) | `shipping_costs` (974) |
| `cancel_order` (996) | `payment_methods` (995) | `store_location` (924) |
| `change_account` (987) | `product_information` (987) | `store_opening_hours` (992) |
| `change_order` (961) | `product_issue` (992) | `submit_feedback` (991) |
| `close_account` (995) | `recover_password` (993) | `submit_product_feedback` (994) |
| `customer_service` (992) | `refund_policy` (994) | `submit_product_idea` (995) |
| `damaged_delivery` (992) | `refund_status` (999) | `technical_issue` (994) |
| `delivery_issue` (996) | `remove_product` (993) | `track_delivery` (996) |
| `delivery_time` (920) | `request_invoice` (1.000) | `track_order` (988) |
| `exchange_product` (988) | `request_refund` (957) | `use_app` (999) |
| `exchange_product_in_store` (991) | `request_right_to_rectification` (989) | `wrong_item` (996) |
| `human_agent` (994) | `return_policy` (994) | — |
| `missing_item` (721) | `return_product` (994) | — |

## Por que aprendizado supervisionado, não regressão linear

O Bitext oferece exemplos de texto com intenção já rotulada pela fonte.
Portanto, a tarefa é **classificação multiclasse supervisionada**: aprender
associações linguísticas a partir do treino e prever um rótulo válido para
novas solicitações. Codificar intenções como 0, 1, 2 etc. para usar regressão
linear introduziria distâncias e ordem inexistentes entre classes; as saídas
contínuas não seriam probabilidades nem rótulos válidos. R² e RMSE não medem o
erro de intenção. Para essa pergunta, usaremos métricas de classificação,
sobretudo Macro-F1, precisão, recall, suporte por intenção e matriz de confusão.

A regressão linear do [notebook TP3](../../notebooks/07_tp3_regressao_linear.ipynb)
tem outro alvo, numérico: comprimento da resposta de referência. Ela serve
como diagnóstico estatístico, **não** como classificador. O baseline
TF-IDF + regressão logística já existente é apenas evidência interna no
Bitext; seu Macro-F1 não pode ser extrapolado para português real.

## Limite da validação externa

O B2W-Reviews01 contém avaliações reais em português, mas **nota não é
intenção**. Uma amostra de 500 textos recebeu rótulos humanos; 422 registros
sem marca de incerteza são elegíveis para avaliação externa e permanecem fora
do treinamento. Essa amostra cobre apenas **20 das 46 intenções** e foi
estratificada por nota. Assim, a futura avaliação deverá apresentar suporte
por intenção e não alegar desempenho para classes ausentes ou para a
distribuição natural de chamados.

Fontes: [distribuição e proveniência do Bitext](../bitext_retail_intents/relatorio.md)
e [relatório da validação PT-BR](../ptbr_intent_validation/final_relatorio.md).
