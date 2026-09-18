# Protocolo de validação externa em PT-BR

## Objetivo

Criar um conjunto de avaliação em português com rótulos humanos para testar a
transferência do classificador treinado no Bitext. Não se geram intenções por
regras, palavras-chave ou previsões do próprio modelo.

## Amostra

`scripts/create_ptbr_validation_queue.py` seleciona 500 feedbacks reais do
B2W-Reviews01: 100 para cada nota de 1 a 5, com semente fixa 42. A fila omite
a nota, o produto, o identificador do cliente e outros metadados que poderiam
induzir o julgamento. Ela contém apenas um identificador opaco, o texto e
campos vazios para anotação.

## Rótulos

Use somente os 46 valores originais da coluna `intent` do Bitext Retail
eCommerce. Não renomeie, não combine e não crie novas classes. Quando não for
possível decidir com segurança, registre `uncertain=yes` e explique em
`notes`. Não transforme `uncertain` em uma intenção.

## Dupla anotação cega

1. Gere a fila e faça duas cópias, uma para cada anotador.
2. Cada anotador preenche sua cópia sem ver a outra, usando o campo `intent`.
3. Execute `scripts/validate_ptbr_annotations.py` com os dois CSVs completos.
4. Os casos divergentes recebem um `adjudicated_intent` por um terceiro
   revisor ou por consenso documentado. Os casos ainda incertos permanecem
   fora da métrica principal.

O script registra concordância simples e Cohen's kappa. O conjunto só pode ser
chamado de validado depois de concluída a adjudicação; antes disso, ele é uma
fila de revisão, não ground truth.

## Uso

```bash
python scripts/create_ptbr_validation_queue.py
cp data/annotations/ptbr_intent_validation_queue.csv data/annotations/annotator_a.csv
cp data/annotations/ptbr_intent_validation_queue.csv data/annotations/annotator_b.csv
python scripts/validate_ptbr_annotations.py \
  --annotator-a data/annotations/annotator_a.csv \
  --annotator-b data/annotations/annotator_b.csv
```

Quando as duas opiniões estiverem na mesma planilha formatada, use:

```bash
python scripts/validate_ptbr_annotations.py --workbook caminho/para/planilha.xlsx
```

Após preencher a planilha de adjudicação, gere o dataset final com:

```bash
python scripts/finalize_ptbr_intent_dataset.py \
  --source-workbook caminho/para/planilha_com_duas_opinioes.xlsx \
  --adjudication-workbook caminho/para/planilha_de_adjudicacao_preenchida.xlsx
```

## Limites

O B2W é uma fonte de avaliações reais, mas não publicou intenção como rótulo
original. Por isso, esta etapa demanda pessoas que dominem o domínio de
e-commerce e o vocabulário dos rótulos. Até existir essa revisão humana, o
resultado de 0,9887 de Macro F1 do Bitext permanece estritamente interno ao
corpus de origem.
