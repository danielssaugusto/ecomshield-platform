# EDA — validação humana PT-BR

## Escopo

Este relatório descreve a amostra B2W com rótulos humanos. Ela é um conjunto
externo de avaliação e não deve ser incorporada ao treinamento do baseline
Bitext. Essa separação preserva a validade da comparação futura.

## Integridade

- Avaliações com rótulo final: 500
- IDs únicos: 500
- Intenções observadas: 20 de 46 rótulos Bitext
- Rótulos por concordância dupla: 375
- Rótulos por adjudicação: 125
- Registros com incerteza: 78
- Registros elegíveis para métrica principal: 422
- Intenções com suporte entre elegíveis: 14 de 46

## Interpretação responsável

A distribuição é concentrada: `submit_product_feedback` representa
59.00% dos 500 registros e
69.19% dos elegíveis.
Entre os dados elegíveis, 5 intenções têm menos de cinco exemplos. O
resultado externo do baseline inglês está no
[relatório TP3](../tp3_data/avaliacao_externa_ptbr.md).
Sua interpretação exige suporte por intenção, comparação com a classe
majoritária e análise dos erros; Macro-F1 isolado não é conclusivo.

## Figuras

- `01_distribuicao_intencoes_validadas.png`
- `02_origem_rotulo_final.png`
- `03_incerteza_por_intencao.png`
- `04_amostra_elegivel_por_intencao.png`
