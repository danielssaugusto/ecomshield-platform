# TP3 — planejamento técnico de dados para o T2

## Tarefa e fronteira entre as bases

A tarefa preditiva é classificar a intenção de uma solicitação de atendimento
com base em seu texto. O **Bitext**, em inglês e híbrido/sintético, contém os
rótulos originais de 46 intenções e será a base de treinamento inicial. O
**B2W-Reviews01** fornece feedback real em português, não rótulos nativos de
intenção. Sua amostra anotada por humanos é uma avaliação externa separada.
Nenhuma nota, resposta de referência, tag ou rótulo inferido por palavra-chave
será usado como substituto da intenção.

## Modelo candidato e engenharia de atributos

O candidato inicial é **TF-IDF de uni e bigramas + regressão logística
multiclasse**. O [baseline exploratório já versionado](../../scripts/train_bitext_intent_baseline.py)
usa `min_df=2`, `sublinear_tf=True` e até 100.000 atributos. O TF-IDF será
ajustado apenas nos textos de treino, dentro de um pipeline, para evitar
vazamento de vocabulário e frequências. A regressão logística produz escores
por classe e é um ponto de partida transparente para analisar erros. Uma SVM
linear poderá ser comparada posteriormente, sob as mesmas partições e métricas.

As partições Bitext já são determinísticas e estratificadas por intenção,
aproximadamente 80/10/10. Textos idênticos ficam em uma só partição. No T2,
escolhas de hiperparâmetros devem usar **treino e validação**; o teste interno
fica reservado para avaliação final uma única vez. Também será examinada
similaridade semântica entre partições, pois ausência de duplicatas exatas
não elimina paráfrases quase iguais.

## Métricas e análise de erros

Serão informados acurácia, Macro-F1, Weighted-F1, precisão e recall por
intenção, suporte e matriz de confusão. O Macro-F1 é central porque dá peso
igual às classes; nenhuma média isolada substituirá a análise dos rótulos
confundidos. A linha de base existente obteve Macro-F1 **0,9887 no teste
interno do Bitext**; esse número não mede generalização em PT-BR.

Na avaliação externa, os **422 textos PT-BR elegíveis** não serão usados para
ajustar vetorizador, modelo, hiperparâmetros ou limiar. O protocolo deverá
registrar versão do modelo antes do teste, apresentar resultados por intenção
com suporte, exemplos anonimizados de erros e eventual abstinência/fora de
escopo. Só **20 das 46 intenções** têm suporte na amostra; classes sem suporte
não receberão uma estimativa de desempenho. Como a seleção foi estratificada
por nota, a média nessa amostra não estimará prevalência em produção.

## Qualidade da anotação e próximos dados

Os 78 textos marcados como incertos ficam fora da métrica principal. A próxima
rodada de anotação deve ampliar as intenções sub-representadas e coletar
justificativa textual para todas as adjudicações; hoje **84 decisões** não
possuem essa justificativa. Antes de ampliar, serão definidos critérios de
inclusão, manual de rótulos, dupla revisão e controle de versões para evitar
mudanças silenciosas no conjunto de avaliação.

## Dependência de equipe para o documento T2 completo

O enunciado também exige **colega adversário identificado, URL/IP da API-alvo
e confirmação de acesso para o TP4/TP5**. Esses dados dependem de acordo com
a outra equipe e ainda não foram fornecidos; não serão inventados. A parte de
segurança da API, seu CI/CD e a auditoria final são responsabilidade da frente
correspondente e serão consolidadas com este planejamento no PDF final do TP3.
