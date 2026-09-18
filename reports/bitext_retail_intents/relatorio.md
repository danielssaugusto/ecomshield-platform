# Relatório de dados — Bitext Retail eCommerce

## Finalidade

Este é o corpus rotulado usado para a tarefa de classificação de intenção.
Os campos `category` e `intent` são os rótulos publicados pela fonte; o
E-ComShield não cria rótulos por palavras-chave, nota ou heurística.

## Rastreabilidade

- Fonte: [`bitext/Bitext-retail-ecommerce-llm-chatbot-training-dataset`](https://huggingface.co/datasets/bitext/Bitext-retail-ecommerce-llm-chatbot-training-dataset)
- Licença da fonte: CDLA-Sharing-1.0
- SHA-256 do CSV baixado: `13a988266fed4e2b2c1ff947a89ef220ce09b5b13ac83c4a1496c0d7b81e8127`
- Linhas no CSV de origem: 44,884
- Linhas removidas por texto/rótulo ausente: 0
- Duplicatas exatas removidas: 0
- Linhas finais: 44,884

> Limitação conhecida: o Bitext se descreve como um dataset híbrido sintético.
> Ele é usado aqui porque fornece a variável-alvo de intenção já definida pela
> fonte. O B2W-Reviews01 continua separado, apenas para EDA e análise de
> feedback real em português.

## Esquema final

| Campo | Descrição |
| --- | --- |
| `text` | Solicitação do cliente (`instruction` da fonte) |
| `category` | Categoria original do Bitext |
| `intent` | Intenção original do Bitext, variável-alvo |
| `response` | Resposta de referência da fonte; não usada como entrada do classificador |
| `tags` | Variações linguísticas indicadas pela fonte |
| `split` | Partição estratificada e determinística (80/10/10) |

## Integridade e inspeção estrutural

| Verificação | Resultado |
| --- | ---: |
| Valores ausentes nos campos de treino (`text`, `category`, `intent`) | 0 |
| Duplicatas exatas no dataset final | 0 |
| Comprimento mediano do texto | 58 caracteres |
| Comprimento médio do texto | 58.3 caracteres |
| Percentil 95 do comprimento | 84 caracteres |

## Hipóteses verificadas

1. **Entrega, produto e devoluções concentram parte relevante das solicitações.**
   As categorias `DELIVERY`, `PRODUCT` e `RETURNS` somam
   20,199 registros
   (45.00%).
2. **As classes são adequadamente balanceadas para avaliação multiclasse.** A
   menor classe possui 721 exemplos
   e a maior 1,000; razão
   máxima/mínima de 1.39.
3. **Nenhuma intenção fica ausente da validação ou teste.** Todas as
   46 intenções aparecem em `train`, `validation` e `test`.
4. **Há variação de extensão que deve orientar o limite de tokens do modelo.**
   O percentil 95 é 84 caracteres; qualquer truncamento
   adotado no treinamento deve ser documentado.

## Categorias

| Categoria | Registros |
| --- | ---: |
| `ACCOUNT` | 4,950 |
| `APP_WEBSITE` | 1,993 |
| `CART` | 1,950 |
| `CONTACT` | 1,986 |
| `DELIVERY` | 6,595 |
| `FEEDBACK` | 2,980 |
| `ORDER` | 3,945 |
| `PAYMENT` | 2,981 |
| `PRODUCT` | 6,679 |
| `RETURNS` | 6,925 |
| `SALES` | 995 |
| `STORE` | 1,916 |
| `USER` | 989 |

## Intenções

| Intenção | Registros |
| --- | ---: |
| `add_product` | 957 |
| `availability` | 972 |
| `availability_in_store` | 756 |
| `availability_online` | 993 |
| `cancel_order` | 996 |
| `change_account` | 987 |
| `change_order` | 961 |
| `close_account` | 995 |
| `customer_service` | 992 |
| `damaged_delivery` | 992 |
| `delivery_issue` | 996 |
| `delivery_time` | 920 |
| `exchange_product` | 988 |
| `exchange_product_in_store` | 991 |
| `human_agent` | 994 |
| `missing_item` | 721 |
| `open_account` | 987 |
| `order_history` | 988 |
| `pay` | 990 |
| `payment_issue` | 996 |
| `payment_methods` | 995 |
| `product_information` | 987 |
| `product_issue` | 992 |
| `recover_password` | 993 |
| `refund_policy` | 994 |
| `refund_status` | 999 |
| `remove_product` | 993 |
| `request_invoice` | 1,000 |
| `request_refund` | 957 |
| `request_right_to_rectification` | 989 |
| `return_policy` | 994 |
| `return_product` | 994 |
| `return_product_in_store` | 994 |
| `return_product_online` | 993 |
| `sales_period` | 995 |
| `shipping_costs` | 974 |
| `store_location` | 924 |
| `store_opening_hours` | 992 |
| `submit_feedback` | 991 |
| `submit_product_feedback` | 994 |
| `submit_product_idea` | 995 |
| `technical_issue` | 994 |
| `track_delivery` | 996 |
| `track_order` | 988 |
| `use_app` | 999 |
| `wrong_item` | 996 |

## Partições

| Partição | Registros |
| --- | ---: |
| `train` | 35,906 |
| `validation` | 4,489 |
| `test` | 4,489 |

## Figuras geradas

- `01_distribuicao_categorias.png`
- `02_distribuicao_intencoes.png`
- `03_comprimento_textos_por_categoria.png`
- `04_particoes_por_categoria.png`
