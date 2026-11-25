# TP3 — mapa de evidências da frente de dados

Este documento vincula os requisitos de dados do TP3 às evidências já
versionadas. Ele não substitui a frente de API, CI/CD, auditoria de segurança
ou a definição da equipe adversária.

| Requisito do TP3 | Evidência | Estado |
| --- | --- | --- |
| Regressão linear com alvo numérico derivado, R², RMSE, resíduos e Q-Q plot | [Notebook 07](../../notebooks/07_tp3_regressao_linear.ipynb) e [relatório](regressao_linear.md) | Concluído |
| Pergunta de classificação, classes, distribuição e justificativa de ML supervisionado | [Pergunta de classificação](pergunta_classificacao.md) | Concluído |
| Plano T2: modelo candidato e engenharia de atributos | [Planejamento técnico](plano_t2_dados.md) | Concluído |
| Separação entre treinamento e avaliação PT-BR | [Protocolo](../../docs/ptbr_intent_validation_protocol.md) e [avaliação externa](avaliacao_externa_ptbr.md) | Concluído, com limitações documentadas |
| Evidência adicional de dados reais anotados para a transição ao T2 | [Piloto ConsumerBR consolidado](consumerbr_human_labels.md) | Concluído como piloto de desenvolvimento |

## Limites que permanecem explícitos

- A regressão explica comprimento de resposta, não intenção; ela não é um
  classificador.
- O baseline Bitext não demonstra desempenho em português real. A avaliação
  B2W foi consultada em experimentos exploratórios anteriores e não deve ser
  reutilizada para escolher um novo modelo como se fosse teste independente.
- O piloto ConsumerBR possui 240 rótulos humanos em 20 classes observadas. Os
  80 textos reservados continuam sem rótulo e não foram usados para escolha de
  modelo. Portanto, não há alegação de 60% nem de cobertura das 46 intenções.
- Colega adversário e URL/IP da API são exigências de equipe para o plano T2,
  não fatos de dados. Permanecem pendentes de confirmação externa e não foram
  inventados.

## Próximo passo após o TP3

No T2, o modelo candidato será selecionado apenas com dados de desenvolvimento
e validação. Antes de qualquer afirmação externa nova, o conjunto reservado
precisará de rótulos humanos independentes. A ampliação para classes não
observadas depende de novas solicitações reais e anotação, não de regras
heurísticas sobre avaliações B2W.
