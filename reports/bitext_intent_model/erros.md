# Análise de erros — baseline Bitext

## Pares mais confundidos

- `track_order` → `track_delivery`: 6
- `submit_product_idea` → `submit_product_feedback`: 4
- `submit_product_feedback` → `submit_product_idea`: 3
- `submit_product_feedback` → `submit_feedback`: 3
- `wrong_item` → `damaged_delivery`: 2
- `track_order` → `refund_status`: 2
- `return_product_online` → `return_product`: 2
- `return_product` → `cancel_order`: 2
- `request_invoice` → `request_refund`: 2
- `exchange_product` → `return_product`: 2

## Dez intenções com menor F1 no teste

- `submit_product_feedback`: F1 0.9436 (99 exemplos)
- `track_order`: F1 0.9468 (99 exemplos)
- `submit_product_idea`: F1 0.9500 (100 exemplos)
- `return_product`: F1 0.9500 (99 exemplos)
- `track_delivery`: F1 0.9709 (100 exemplos)
- `return_policy`: F1 0.9746 (99 exemplos)
- `submit_feedback`: F1 0.9751 (99 exemplos)
- `change_account`: F1 0.9798 (99 exemplos)
- `damaged_delivery`: F1 0.9798 (99 exemplos)
- `close_account`: F1 0.9800 (100 exemplos)

## Limite de interpretação

Esta análise mostra onde o baseline confunde rótulos dentro do próprio Bitext.
Ela não mede a qualidade em feedbacks reais brasileiros. A etapa de validação
humana em PT-BR é necessária antes de qualquer conclusão externa.
