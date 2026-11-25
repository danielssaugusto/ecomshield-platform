# Relatório de EDA — B2W Intents v4

Este relatório é gerado automaticamente por `scripts/generate_b2w_eda.py`.

## Integridade

- Registros: 131,307
- Duplicatas exatas no Parquet: 0
- Texto vazio: 0
- Avaliações com múltiplos temas textuais: 22,695
- Período: 2018-01-01 a 2018-05-31

## Cobertura por origem

| Origem | Registros | Percentual |
| --- | ---: | ---: |
| `keyword_heuristic_v4` | 76,375 | 58.17% |
| `generic_topic_fallback_v1` | 54,932 | 41.83% |

## Categorias principais

| Categoria | Registros | Percentual |
| --- | ---: | ---: |
| `avaliacao_geral` | 54,932 | 41.83% |
| `qualidade_produto` | 14,094 | 10.73% |
| `atraso_entrega` | 12,141 | 9.25% |
| `entrega_antecipada` | 10,518 | 8.01% |
| `custo_beneficio` | 7,187 | 5.47% |
| `uso_desempenho` | 4,990 | 3.80% |
| `tamanho_dimensoes` | 4,874 | 3.71% |
| `produto_defeituoso` | 4,476 | 3.41% |
| `entrega_no_prazo` | 4,186 | 3.19% |
| `troca_devolucao` | 3,641 | 2.77% |
| `atendimento` | 2,053 | 1.56% |
| `estorno_reembolso` | 1,680 | 1.28% |
| `cancelamento` | 1,369 | 1.04% |
| `cobranca_pagamento` | 787 | 0.60% |
| `divergencia_anuncio` | 759 | 0.58% |
| `frete` | 755 | 0.57% |
| `duvida_produto` | 717 | 0.55% |
| `item_faltante` | 690 | 0.53% |
| `suspeita_autenticidade` | 475 | 0.36% |
| `avaria_entrega` | 443 | 0.34% |
| `produto_incorreto` | 280 | 0.21% |
| `informacao_anuncio` | 215 | 0.16% |
| `embalagem_danificada` | 45 | 0.03% |

## Sentimento

| Sentimento | Registros |
| --- | ---: |
| `positivo` | 85,854 |
| `neutro` | 11,270 |
| `negativo` | 31,236 |
| `misto` | 2,947 |

## Coocorrências principais

| Par | Registros |
| --- | ---: |
| entrega_antecipada + qualidade_produto | 2,491 |
| custo_beneficio + qualidade_produto | 2,049 |
| troca_devolucao + produto_defeituoso | 1,616 |
| tamanho_dimensoes + qualidade_produto | 1,546 |
| qualidade_produto + uso_desempenho | 1,438 |
| entrega_no_prazo + qualidade_produto | 1,061 |
| produto_defeituoso + qualidade_produto | 866 |
| custo_beneficio + uso_desempenho | 864 |
| cancelamento + atraso_entrega | 845 |
| entrega_antecipada + custo_beneficio | 773 |
| atraso_entrega + troca_devolucao | 759 |
| tamanho_dimensoes + uso_desempenho | 754 |
| atraso_entrega + qualidade_produto | 732 |
| estorno_reembolso + atraso_entrega | 712 |
| atraso_entrega + atendimento | 656 |
