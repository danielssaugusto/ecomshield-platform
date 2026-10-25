# TP3 — regressão linear múltipla no Bitext

Alvo: comprimento da resposta de referência, em caracteres. Preditores: apenas características da solicitação. A partição de validação não foi usada.

Treino: 35,906 linhas; teste: 4,489 linhas; zero textos idênticos entre essas partições.

| Modelo | R² teste | RMSE teste (caracteres) |
| --- | ---: | ---: |
| LinearRegression | 0.0080 | 308.82 |
| Média do treino | -0.0002 | 310.10 |

A melhora de RMSE sobre a média foi de apenas 0.41%; o R² próximo de zero indica poder explicativo muito baixo. As previsões se concentram em faixa estreita e os resíduos têm cauda superior longa no Q-Q plot. Mediana dos resíduos: -19.68; percentis 5 e 95: -474.55 e 519.13 caracteres. Ver [resíduos versus previsto](figures/01_residuos_vs_previsto.png) e [Q-Q plot](figures/02_qq_residuos.png).

## Limitações

O Bitext é inglês e híbrido/sintético; comprimento de resposta não equivale a intenção. Colinearidade entre medidas de extensão, assimetria e cauda não normal limitam inferência. A regressão não substitui a classificação supervisionada e não mede desempenho em PT-BR.
