# Avaliação do baseline de intenção

- Modelo: TF-IDF (1–2 gramas) + Regressão Logística
- Treino/teste: 35,906/4,489 registros
- Textos idênticos em treino e teste: 0
- Accuracy: 0.9886
- Macro F1: 0.9887
- Weighted F1: 0.9886

## Interpretação responsável

O particionamento é estratificado por intenção e agrupa textos repetidos para
evitar que a mesma solicitação apareça em treino e teste. A verificação acima
conta sobreposições textuais exatas; não prova ausência de paráfrases ou outros
tipos de vazamento semântico. O Bitext é um corpus em inglês e híbrido/sintético.
Essas métricas não representam desempenho em reclamações brasileiras reais nem
autorizam uso produtivo sem validação externa.
