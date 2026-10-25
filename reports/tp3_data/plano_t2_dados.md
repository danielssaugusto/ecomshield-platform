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

Na [avaliação externa TP3](avaliacao_externa_ptbr.md), os **422 textos PT-BR
elegíveis** não foram usados para ajustar vetorizador, modelo, hiperparâmetros
ou limiar. O relatório registra o hash do modelo, resultados por intenção com
suporte e erros rastreáveis por ID opaco. As 500 anotações cobrem 20 intenções,
mas somente **14 das 46** aparecem no subconjunto elegível; as 32 classes sem
suporte não recebem estimativa de desempenho. Como a seleção foi estratificada
por nota, a média nessa amostra não estima prevalência em produção.

O baseline inglês teve desempenho externo muito baixo. No T2, qualquer
adaptação linguística ou novo modelo terá de ser definida e ajustada com dados
de desenvolvimento separados, sem reutilizar os 422 registros como treino ou
conjunto de escolha de hiperparâmetros. Se os 422 forem consultados repetidas
vezes para selecionar abordagens, deixarão de funcionar como teste externo
independente; será necessário obter outra amostra humana reservada.

Um [experimento adicional de transferência multilíngue](transferencia_multilingue.md)
selecionou o hiperparâmetro apenas na validação Bitext e chegou a 38/422
(9,0%) na amostra PT-BR. O ganho sobre 6/422 não aproxima a meta de 60%.
O resultado reforça a mudança de domínio e de definição dos rótulos:
`submit_product_feedback` no Bitext é um pedido para enviar feedback, enquanto
um review B2W já é o próprio feedback. Não se pode corrigir isso somente com
um encoder multilíngue. Ver o [plano de dados para a meta de
60%](plano_melhoria_intencoes_ptbr.md).

## Qualidade da anotação e próximos dados

Os 78 textos marcados como incertos ficam fora da métrica principal. A próxima
rodada de anotação deve ampliar as intenções sub-representadas e coletar
justificativa textual para todas as adjudicações; hoje **84 decisões** não
possuem essa justificativa. Uma planilha local reúne esses 84 casos para retorno
dos revisores, sem alterar os rótulos existentes. Antes de ampliar, serão
definidos critérios de inclusão, manual de rótulos, dupla revisão e controle de
versões para evitar mudanças silenciosas no conjunto de avaliação. Reviews B2W
continuam úteis para avaliar feedback de produto, mas a próxima coleta deve
incluir solicitações reais de suporte para cobrir intenções de conta, pagamento
e pedidos que quase não aparecem em avaliações de produto.

## Dependência de equipe para o documento T2 completo

O enunciado também exige **colega adversário identificado, URL/IP da API-alvo
e confirmação de acesso para o TP4/TP5**. Esses dados dependem de acordo com
a outra equipe e ainda não foram fornecidos; não serão inventados. A parte de
segurança da API, seu CI/CD e a auditoria final são responsabilidade da frente
correspondente e serão consolidadas com este planejamento no PDF final do TP3.
