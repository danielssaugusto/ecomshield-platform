# Relatório de Análise Exploratória de Dados (EDA) — EcomShield Platform

**Projeto:** Plataforma EcomShield — Módulo de Inteligência e Triagem Operacional  
**Dataset Base:** B2W-Reviews01 Intents (v4) — Corpus de Avaliações de E-commerce com Rótulos Derivados  
**Data:** 26 de Setembro de 2026  
**Autor:** Equipe de Engenharia de Dados & Segurança EcomShield  

---

## 1. Problema

No cenário de e-commerce de alto volume, o atendimento ao cliente e a gestão de pós-venda enfrentam desafios críticos de escalabilidade. Milhares de avaliações e mensagens de suporte chegam diariamente, variando desde elogios simples até reclamações graves de defeitos de fabricação, fraudes e solicitações urgentes de estorno financeiro.

A ausência de uma triagem automatizada e precisa resulta em:
- **Atraso na Resolução Financeira:** Pedidos de cancelamento e estorno que demandam ação imediata acabam represados na mesma fila de feedbacks genéricos.
- **Perda de Visibilidade Operacional:** Dificuldade em identificar gargalos logísticos sistêmicos (ex.: atrasos recorrentes por transportadora ou região).
- **Risco de Segurança e Fraude:** Suspeitas de contrafação (produtos falsificados) ou cobranças indevidas sem alarme automatizado.

O objetivo do EcomShield nesta etapa é realizar uma **Análise Exploratória de Dados (EDA)** aprofundada no dataset B2W-Reviews01, compreendendo as relações estatísticas entre a extensão das avaliações, a nota atribuída (`overall_rating`), o sentimento e as intenções operacionais do consumidor, preparando o terreno para a construção de um modelo preditivo de classificação supervisionada.

---

## 2. Dados

### 2.1 Origem e Pipeline de Limpeza
O corpus original é derivado do repositório aberto `B2W-Reviews01` (composto por 132.373 avaliações brutas). O pipeline de ingestão e sanitização (`scripts/build_b2w_intent_dataset.py`) aplicou as seguintes transformações estritas:
1. **Anonimização e Proteção de Dados (LGPD/PII):** Substituição determinística de e-mails (`[EMAIL]`), CPFs (`[CPF]`) e telefones (`[TELEFONE]`) via expressões regulares.
2. **Normalização Textual:** Aplicação de normalização Unicode NFC, eliminação de caracteres nulos e fusão do título (`review_title`) com o corpo da mensagem (`review_text`).
3. **Remoção de Duplicatas Exatas e Textos Vazios:** Deduplicação estrita preservando apenas registros únicos com conteúdo relevante.
4. **Volume Final Sanitizado:** **131.307 registros** validados no formato Apache Parquet (`data/processed/b2w_reviews_intents.parquet`).

### 2.2 Estrutura do Schema

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `source_row_id` | `int64` | Identificador único do registro na fonte original |
| `submission_date` | `datetime64[ns]` | Data e hora de submissão da avaliação |
| `product_id` | `string` | Código identificador do produto |
| `overall_rating` | `int8` | Nota da avaliação (escala discreta de 1 a 5) |
| `text` | `string` | Prose completa da avaliação (Título + Texto limpo) |
| `intent` | `string` | Categoria de intenção primária identificada |
| `intent_matches` | `string` | Lista de todas as intenções mapeadas (coocorrências) |
| `label_source` | `string` | Proveniência do rótulo (`keyword_heuristic_v4` ou `generic_topic_fallback_v1`) |
| `sentiment` | `string` | Sentimento da avaliação (`positivo`, `negativo`, `neutro`, `misto`) |
| `sentiment_source` | `string` | Origem da classificação de sentimento |
| `text_length` | `int64` | Quantidade total de caracteres no texto |
| `word_count` | `int64` | Contagem total de palavras no texto |

---

## 3. Análise

### 3.1 Matriz de Correlação (Heatmap de Seaborn)
Foi calculada a matriz de correlação de Pearson entre os atributos numéricos (`overall_rating`, `word_count`, `text_length`) e as variáveis binárias codificadas de sentimento (`is_negativo`, `is_positivo`) e intenções operacionais mais críticas (`is_atraso_entrega`, `is_estorno_reembolso`, `is_qualidade_produto`).

```
+----------------------+----------------+--------------+-------------------+
| Atributos            | overall_rating | word_count   | is_negativo       |
+----------------------+----------------+--------------+-------------------+
| overall_rating       |      1.00      |    -0.34     |      -0.78        |
| word_count           |     -0.34      |     1.00     |       0.36        |
| is_negativo          |     -0.78      |     0.36     |       1.00        |
| is_positivo          |      0.82      |    -0.31     |      -0.62        |
| is_atraso_entrega    |     -0.45      |     0.28     |       0.52        |
| is_estorno_reembolso |     -0.51      |     0.32     |       0.58        |
+----------------------+----------------+--------------+-------------------+
```

**Principais Descobertas da Correlação:**
- **Forte Correlação Negativa entre Nota e Insatisfação ($r = -0,78$):** A nota geral reflete diretamente a polaridade de sentimento.
- **Correlação Inversa entre Nota e Extensão do Texto ($r = -0,34$):** Avaliações com notas baixas (1 e 2) tendem a apresentar maior número de palavras e caracteres, enquanto avaliações 5 estrelas são predominantemente sucintas (ex.: "Muito bom", "Chegou rápido").

### 3.2 Diagramas de Dispersão (Scatter Plots)
O gráfico de dispersão com acréscimo de ruído visual (jitter) no eixo da nota permitiu analisar a distribuição da contagem de palavras (`word_count`) em relação ao sentimento:
- Avaliações classificadas como **`negativo`** ou **`misto`** concentram a cauda longa da distribuição, atingindo valores superiores a 150-200 palavras.
- Avaliações **`positivo`** possuem mediana em torno de 8 palavras, agrupando-se densamente na faixa inferior do gráfico.

### 3.3 Teste de Hipótese Estatística Formal (SciPy)

#### Formulação das Hipóteses
- **Hipótese Nula ($H_0$):** Não há diferença na extensão do texto (`word_count`) entre avaliações insatisfeitas (nota $\le 2$) e avaliações satisfeitas (nota $\ge 4$), ou a extensão dos insatisfeitos é menor ($\mu_{\text{insatisfeitos}} \le \mu_{\text{satisfeitos}}$).
- **Hipótese Alternativa ($H_1$):** Clientes insatisfeitos escrevem textos estatisticamente e significativamente mais extensos do que clientes satisfeitos ($\mu_{\text{insatisfeitos}} > \mu_{\text{satisfeitos}}$).

#### Execução dos Testes via SciPy (`scipy.stats`)
Dado que a distribuição de palavras apresenta assimetria positiva (cauda longa à direita), aplicou-se o teste não-paramétrico de **Mann-Whitney U** (robusto a não-normalidade) paralelamente ao **Teste t de Welch** (duas amostras independentes com variâncias desiguais).

| Métria / Estatística | Amostra Insatisfeitos (Nota $\le 2$) | Amostra Satisfeitos (Nota $\ge 4$) |
| :--- | :--- | :--- |
| **Tamanho da Amostra ($N$)** | 38.412 avaliações | 76.850 avaliações |
| **Mediana de Palavras** | **16,0 palavras** | **8,0 palavras** |
| **Média de Palavras ($\mu$)** | **24,35 palavras** | **11,82 palavras** |
| **Desvio Padrão ($\sigma$)** | 22,14 palavras | 10,45 palavras |
| **Estatística de Mann-Whitney U** | **$U = 2,18 \times 10^9$** | — |
| **p-valor (Mann-Whitney U)** | **$p < 0,0001$ ($p = 0,0000 \times 10^0$)** | — |
| **Estatística t de Welch** | **$t = 104,85$** | — |
| **p-valor (Welch's t-test)** | **$p < 0,0001$** | — |

#### Interpretação dos Resultados em Linguagem Acessível
O teste estatístico formal resultou em um valor-p extremamente reduzido ($p < 0,0001$), consideravelmente menor do que o nível de significância padrão ($\alpha = 0,05$).

**O que isso significa na prática?**
Existe menos de 0,01% de chance de que a diferença observada no tamanho das mensagens seja fruto do acaso. Rejeitamos com 99,99% de confiança a hipótese nula. Consumidores insatisfeitos escrevem, em média, o **dobro de palavras** (mediana de 16 palavras contra 8 palavras dos satisfeitos) para detalhar sua frustração, descrever defeitos do produto ou solicitar o reembolso.

---

## 4. Insights Principais

1. **Logística é o Vetor Principal de Atrito:** As intenções `atraso_entrega` e `estorno_reembolso` respondem por mais de 35% de todas as reclamações operacionais registradas no dataset.
2. **Verbocidade como Sinalizador de Prioridade:** O tamanho da mensagem é um preditor forte de gravidade. Textos longos devem ser roteados com maior prioridade para a fila de atendimento do EcomShield.
3. **Desacoplamento entre Tema e Sentimento:** A separação explícita entre a intenção operacional (ex.: `troca_devolucao`) e a polaridade do sentimento (ex.: `neutro`, `negativo`) permitiu capturar feedbacks onde a troca ocorreu de maneira amigável e satisfatória.

---

## 5. Limitações

1. **Ruído de Rotulagem Heurística:** Os rótulos de intenção atuais foram gerados via regras determinísticas por palavras-chave (`keyword_heuristic_v4`), podendo apresentar falsos positivos em contextos irônicos ou ambiguidades.
2. **Sobreposição de Intenções (Multi-label):** Cerca de 12.450 avaliações ativaram mais de uma intenção simultaneamente (ex.: `atraso_entrega` + `estorno_reembolso`). O dataset atual força um rótulo primário.
3. **Ausência de Metadados de Pedido:** O dataset B2W não possui informações de valor financeiro do pedido ou prazos prometidos de entrega em dias úteis, limitando o cruzamento financeiro direto.

---

## 6. Próximos Passos (Transição para o Modelo de Classificação)

Para superar as limitações das regras heurísticas e implantar um classificador inteligente em produção na API FastAPI do EcomShield, os seguintes passos serão executados:

1. **Vetorização e Baseline NLP:** Treinar um pipeline baseline com TF-IDF (N-grams de 1 a 3 palavras) combinado com `LogisticRegression` e `LightGBM` otimizado por F1-score ponderado.
2. **Adoção de Modelos Transformer (Fine-Tuning):** Realizar fine-tuning do modelo pré-treinado em português `BERTimbau` (`neuralmind/bert-base-portuguese-cased`) ou `mDeBERTa-v3` para capturar semântica profunda e contexto de e-commerce.
3. **Arquitetura Multi-Label (Binary Relevance / Classifier Chains):** Reformular a camada final de classificação para prever múltiplos rótulos por avaliação, refletindo casos onde o cliente solicita estorno e reclama de atraso ao mesmo tempo.
4. **Integração com API FastAPI:** Empacotar o modelo final treinado no endpoint `/predictions/predict`, fornecendo previsões em tempo real com pontuação de confiança (confidence score).
