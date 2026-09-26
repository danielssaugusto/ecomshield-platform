# Entrega de dados — resposta ao feedback

## Decisão de desenho

O projeto separa dois usos de dados que antes estavam misturados:

| Necessidade | Evidência usada | Regra de uso |
| --- | --- | --- |
| Feedback real em português | B2W-Reviews01 | EDA e análise descritiva. Não produz rótulo de intenção. |
| Classificação de intenções | Bitext Retail eCommerce | Treino e teste com a coluna `intent` publicada pela própria fonte. |
| Validação externa em português | Amostra B2W com dupla anotação | 500 rótulos humanos, sem regra automática e com adjudicação. |

## O que foi corrigido

O pipeline antigo que convertia feedbacks B2W em intenções por heurística não
é usado para treinar nem para avaliar o classificador. Essa mudança evita medir
o quanto um modelo repete regras criadas pelo próprio projeto.

O Bitext fornece 44.884 textos, 46 intenções e 13 categorias com rótulos
originais. O processamento preserva esses valores, remove somente ausência de
texto/rótulo e duplicatas exatas, e produz divisões determinísticas de
treino/validação/teste (aproximadamente 80/10/10).
Textos idênticos são agrupados na mesma partição; a auditoria encontrou zero
sobreposições textuais exatas entre partições após a correção do split.

## Resultados reprodutíveis

- B2W limpo para EDA: 131.347 feedbacks reais em português.
- Bitext processado: 44.884 registros; nenhum valor ausente nos campos de
  treino; nenhuma intenção ausente de validação ou teste.
- Baseline transparente: TF-IDF de unigramas e bigramas com regressão
  logística; Macro F1 de 0,9887 no teste isolado do Bitext.

Esse último número é interno ao Bitext. Ele não é uma alegação de desempenho
em português, porque a fonte é em inglês e se declara híbrida/sintética.

## Validação externa concluída

A fila foi criada a partir de 500 reviews reais B2W, estratificada por nota e
sem mostrar a nota aos revisores. Dois anotadores trabalharam em cópias
independentes. O validador aceitou somente os 46 rótulos originais do Bitext,
calculou 75,00% de concordância simples e Cohen's kappa de 0,5504, e enviou
125 divergências para adjudicação humana.

O dataset final possui 500 rótulos, dos quais 375 vieram de concordância dupla
e 125 de adjudicação. Setenta e oito registros têm marca de incerteza e são
preservados para auditoria, mas ficam fora da métrica principal. Restam 422
registros elegíveis para avaliação externa.

As decisões humanas foram preservadas em arquivo sem os textos das avaliações,
com hashes de cada amostra e manifesto das planilhas originais. O script de
reconstrução gera novamente o CSV final a partir do B2W fixado por revisão e
SHA-256; a saída foi comparada byte a byte com a versão validada e teve o
mesmo SHA-256. Entre 125 casos adjudicados, 84 não têm justificativa textual
na planilha recebida. O motivo dessas decisões não pode ser recuperado sem
nova consulta aos revisores. Os 78 incertos tampouco devem ser tratados como
rótulos seguros.

O B2W é publicado pela B2W Digital sob [CC BY-NC-SA 4.0](https://github.com/americanas-tech/b2w-reviews01),
com atribuição, uso não comercial e compartilhamento pela mesma licença. O
Bitext é publicado sob CDLA-Sharing-1.0 e se descreve como híbrido/sintético.

## Artefatos

- `scripts/build_bitext_intent_dataset.py`
- `scripts/download_b2w_reviews.py`
- `scripts/export_ptbr_annotation_labels.py`
- `scripts/rebuild_ptbr_validation_dataset.py`
- `scripts/generate_b2w_feedback_eda.py`
- `scripts/train_bitext_intent_baseline.py`
- `scripts/create_ptbr_validation_queue.py`
- `scripts/validate_ptbr_annotations.py`
- `scripts/finalize_ptbr_intent_dataset.py`
- `scripts/generate_ptbr_validation_eda.py`
- `notebooks/03_b2w_feedback_eda.ipynb`
- `notebooks/04_bitext_intent_eda.ipynb`
- `notebooks/05_bitext_intent_baseline.ipynb`
- `notebooks/06_ptbr_validated_dataset_eda.ipynb`
