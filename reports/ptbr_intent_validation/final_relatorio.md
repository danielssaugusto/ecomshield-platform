# Dataset PT-BR validado por revisão humana

- Registros finais: 500
- Rótulos por concordância dupla: 375
- Rótulos por adjudicação: 125
- Registros com marca de incerteza: 78
- Registros elegíveis para a avaliação principal: 422
- Taxonomia: 46 intenções originais do Bitext Retail eCommerce.
- SHA-256 do CSV reconstruído: `36ddba3b620d73a86802a3863be0eb93dabcc2607b14ee4225f9e9d28b8cb8f0`.

O arquivo final preserva as duas opiniões, a decisão de adjudicação quando
necessária e o método que originou cada rótulo validado.

Os registros com `has_uncertainty_flag=true` são preservados para auditoria,
mas ficam fora da métrica principal. Os 500 registros usam
20 das 46 intenções da taxonomia; os
422 elegíveis usam apenas 14.
A classe mais frequente entre os elegíveis é
`submit_product_feedback` (292 registros).
A amostra foi estratificada por nota e não representa a distribuição
operacional de chamados de atendimento.
