# TP3 — avaliação externa PT-BR do baseline congelado

## Protocolo e proveniência

O modelo TF-IDF (uni e bigramas) + regressão logística foi treinado somente na
partição `train` do Bitext, em inglês. Seu código e artefato foram congelados
antes desta avaliação. Nenhum dos 500 feedbacks B2W anotados foi usado para
ajustar o vocabulário, o modelo, hiperparâmetros ou limiares. A avaliação
principal exclui os 78 registros marcados incertos por qualquer anotador.

- CSV validado (SHA-256): `36ddba3b620d73a86802a3863be0eb93dabcc2607b14ee4225f9e9d28b8cb8f0`.
- Modelo avaliado (SHA-256): `55e4b83616e0126e2595e8297c7a8196a04001d22aaec659bf8fc4e19b24ce6d`.
- Receita de treinamento (SHA-256): `0b9138af7f85c4f66e070e5989b6558929daea04f359d61c7226de624b013bae`.
- Textos idênticos entre Bitext treino e B2W elegível: 0.
- Registros com vetor TF-IDF vazio: 125 de 422.
- Acertos com vetor vazio: 0; acertos com vetor não vazio: 6.

## Resultados

| Medida | Resultado |
| --- | ---: |
| Feedbacks elegíveis | 422 |
| Acertos | 6 |
| Intenções com suporte | 14 de 46 |
| Acurácia do modelo | 0.0142 |
| Acurácia de prever sempre `submit_product_feedback` | 0.6919 |
| Macro-F1 nas intenções com suporte | 0.0108 |
| Weighted-F1 nas intenções com suporte | 0.0166 |

A linha de base majoritária usa apenas a distribuição dos rótulos para comparação
descritiva. Não é um classificador treinado com esses feedbacks. O Macro-F1 é
calculado nas 14 intenções com pelo menos um rótulo real;
as outras 32 não têm estimativa de desempenho.
Predições para intenções sem suporte no conjunto: 389.

### Diagnóstico de cobertura textual e revisão humana

| Subconjunto | Casos | Acertos | Acurácia |
| --- | ---: | ---: | ---: |
| Vetor TF-IDF vazio | 125 | 0 | 0.0000 |
| Vetor TF-IDF não vazio | 297 | 6 | 0.0202 |
| Dupla concordância humana | 349 | 2 | 0.0057 |
| Adjudicação humana | 73 | 4 | 0.0548 |

Esses estratos são diagnósticos descritivos, não testes independentes nem
estimativas de desempenho em produção. A diferença entre grupos de anotação
não mede qualidade dos revisores, porque os casos adjudicados tendem a ser
mais ambíguos.

### Métricas por intenção

| Intenção real | Suporte | Precisão | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| `submit_product_feedback` | 292 | 0.000 | 0.000 | 0.000 |
| `product_issue` | 46 | 0.182 | 0.130 | 0.152 |
| `delivery_time` | 23 | 0.000 | 0.000 | 0.000 |
| `delivery_issue` | 17 | 0.000 | 0.000 | 0.000 |
| `product_information` | 11 | 0.000 | 0.000 | 0.000 |
| `damaged_delivery` | 6 | 0.000 | 0.000 | 0.000 |
| `missing_item` | 5 | 0.000 | 0.000 | 0.000 |
| `submit_feedback` | 5 | 0.000 | 0.000 | 0.000 |
| `wrong_item` | 5 | 0.000 | 0.000 | 0.000 |
| `shipping_costs` | 4 | 0.000 | 0.000 | 0.000 |
| `technical_issue` | 3 | 0.000 | 0.000 | 0.000 |
| `track_delivery` | 3 | 0.000 | 0.000 | 0.000 |
| `cancel_order` | 1 | 0.000 | 0.000 | 0.000 |
| `exchange_product` | 1 | 0.000 | 0.000 | 0.000 |

### Erros mais frequentes

| Intenção real | Previsão | Casos |
| --- | --- | ---: |
| `submit_product_feedback` | `pay` | 219 |
| `submit_product_feedback` | `request_invoice` | 29 |
| `product_issue` | `pay` | 28 |
| `submit_product_feedback` | `product_issue` | 25 |
| `delivery_time` | `pay` | 15 |
| `delivery_issue` | `pay` | 14 |
| `submit_product_feedback` | `store_location` | 9 |
| `delivery_time` | `request_invoice` | 7 |
| `product_issue` | `request_invoice` | 7 |
| `product_information` | `pay` | 6 |

Casos concretos para conferência no CSV local, sem publicar o texto do cliente:

| ID opaco | Intenção humana | Previsão |
| --- | --- | --- |
| `b2w-1529868ee5f31554` | `submit_product_feedback` | `pay` |
| `b2w-a90f2852e93c9e9d` | `submit_product_feedback` | `request_invoice` |
| `b2w-a849581b4d7a2b58` | `product_issue` | `pay` |
| `b2w-a61e96597abe80d9` | `submit_product_feedback` | `product_issue` |
| `b2w-8d2745f4cc98148f` | `delivery_time` | `pay` |
| `b2w-ef26ef1fb131dbf7` | `delivery_issue` | `pay` |
| `b2w-4d7f28fe3ff03e6e` | `submit_product_feedback` | `store_location` |
| `b2w-39129ef55d968125` | `delivery_time` | `request_invoice` |
| `b2w-7f2bd50054cd51e7` | `product_issue` | `request_invoice` |
| `b2w-ec860849e2ea29ae` | `product_information` | `pay` |

## Interpretação e limites

O teste interno do Bitext não pode ser extrapolado para esta amostra: o corpus
de treino é inglês e híbrido/sintético, enquanto o B2W contém avaliações reais
de produtos em português, não chamados de suporte. A taxonomia de intenção foi
aplicada por anotadores humanos, mas pode não representar bem cada avaliação.
Todos os 125 textos sem atributos reconhecidos
receberam a previsão `pay`; nenhum foi
classificado corretamente. Esse padrão é compatível com a lacuna de vocabulário
entre os dois idiomas, mas não isola todas as causas dos erros.
Os 500 rótulos cobrem 20 intenções; os 422 elegíveis cobrem
somente 14. A classe majoritária responde por
292 casos.
Classes com suporte 1–5 produzem estimativas especialmente instáveis. A amostra
foi estratificada por nota de avaliação e não estima prevalência em produção.
Entre as adjudicações, 84 decisões não têm justificativa textual recuperável,
incluindo 60 no subconjunto elegível. Não inventamos essas justificativas.

Este resultado mede apenas transferência para a amostra anotada. Não autoriza
integração do classificador à API ou alegação de desempenho em atendimento real.
O [JSON de resultados](avaliacao_externa_ptbr.json) inclui os 422 pares de
rótulo humano e previsão com ID pseudônimo e tamanho do vetor, sem texto bruto,
permitindo recalcular as métricas e conferir os exemplos acima.
Para ampliar a cobertura, será necessária nova revisão humana de solicitações
reais de suporte; acrescentar apenas reviews B2W pode manter o mesmo viés.
