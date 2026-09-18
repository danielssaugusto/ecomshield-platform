# EDA — B2W-Reviews01 como feedback real

## Escopo

Este relatório analisa avaliações reais de e-commerce em português. O campo de
análise `feedback_text` combina o título e o corpo originais da avaliação.
Nenhuma coluna de intenção é criada ou usada. O B2W complementa o corpus
Bitext, que é o dataset usado para classificação de intenções.

## Integridade

- Fonte: [B2W-Reviews01](https://raw.githubusercontent.com/americanas-tech/b2w-reviews01/4639429ec698d7821fc99a0bc665fa213d9fcd5a/B2W-Reviews01.csv)
- SHA-256: `821fb0bf9f7230b0fba4e4f9fadd75a66d1a9ff0b1657810791d33007eb2ab38`
- Linhas originais: 132,373
- Textos vazios removidos: 72
- Duplicatas exatas removidas: 954
- Linhas finais: 131,347
- Período: 2018-01-01 a 2018-05-31

## Hipóteses verificadas

1. **As avaliações tendem a notas altas.** A proporção de notas 4 e 5 é
   60.99%.
2. **Textos de notas baixas são mais detalhados.** A mediana de caracteres em
   notas 1–2 é 154, contra
   102 em notas 4–5.
3. **O volume está concentrado em poucas categorias de produto.** As cinco
   maiores categorias representam 43.35% das avaliações.
4. **A recomendação a amigos acompanha a satisfação declarada.** A taxa de
   recomendação é 73.15% entre os registros
   com essa resposta preenchida.

## Figuras

- `01_valores_ausentes.png`
- `02_distribuicao_notas.png`
- `03_categorias_mais_avaliadas.png`
- `04_volume_mensal.png`
- `05_comprimento_por_nota.png`
