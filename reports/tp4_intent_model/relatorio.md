# TP4 - Classificador de intenções

"
        f"- Pipeline: TF-IDF (1-2 gramas) + LogisticRegression
"
        f"- Dados: 40,395 treino/validação e 4,489 teste
"
        f"- GridSearchCV: 3 folds, métrica macro F1
"
        f"- Parâmetros pesquisados: `tfidf__min_df` = [1, 2, 3]; `classifier__C` = [0.5, 1.0, 2.0]
"
        f"- Melhores parâmetros: `{'classifier__C': 2.0, 'tfidf__min_df': 1}`
"
        f"- Melhor macro F1 de validação cruzada: 0.9876

"
        f"## Teste isolado

"
        f"| Modelo | Accuracy | Macro F1 | ROC-AUC OvR macro |
| --- | ---: | ---: | ---: |
"
        f"| Baseline (classe mais frequente) | 0.0223 | 0.0009 | N/A |
"
        f"| Modelo ajustado | 0.9902 | 0.9903 | 1.0000 |

"
        f"O ganho de macro F1 sobre a baseline foi 0.9893. A matriz de confusão está em `matriz_confusao.png`; as métricas por classe estão em `tp4_intent_evaluation.json`.

"
        f"## Limitação

The Bitext corpus is English and hybrid/synthetic; these in-distribution metrics are not a PT-BR or production-performance claim.
