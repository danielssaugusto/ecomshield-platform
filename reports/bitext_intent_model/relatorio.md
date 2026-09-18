# Avaliação do baseline de intenção

- Modelo: TF-IDF (1–2 gramas) + Regressão Logística
- Treino/teste: 35,906/4,489 registros
- Accuracy: 0.9886
- Macro F1: 0.9887
- Weighted F1: 0.9886

## Interpretação responsável

O teste usa uma partição isolada e estratificada; não há vazamento entre treino e teste. Ainda assim, o Bitext é um corpus em inglês e híbrido/sintético. Essas métricas não representam desempenho em reclamações brasileiras reais nem autorizam uso produtivo sem validação externa.
