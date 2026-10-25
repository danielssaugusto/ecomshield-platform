# TP3/T2 — caminho verificável para melhorar a classificação PT-BR

## Resultado que já podemos afirmar

O [baseline inglês](avaliacao_externa_ptbr.md) acertou 6/422 (1,4%). Um
[encoder multilíngue congelado](transferencia_multilingue.md), seguido por
regressão logística treinada apenas no Bitext, acertou 38/422 (9,0%);
Macro-F1 nas 14 intenções com suporte foi 0,132. A seleção do hiperparâmetro
ocorreu na validação Bitext, não no B2W. O teste PT-BR já havia sido consultado
para o baseline anterior: esta segunda medição é exploratória, não uma nova
confirmação independente.

Prever sempre `submit_product_feedback` daria 292/422 (69,2%) **nesta amostra**,
porque ela foi estratificada por nota e contém muitas avaliações de produtos.
Isso supera 60% de acurácia sem reconhecer nenhuma das outras 13 intenções.
Logo, não é evidência de um classificador de atendimento útil. Como a classe
majoritária foi identificada no próprio teste, usar essa decisão para construir
o modelo também violaria a separação de desenvolvimento/avaliação.

## Causa operacional

O Bitext contém perguntas dirigidas ao suporte em inglês. A classe
`submit_product_feedback` refere-se tipicamente a *pedir ajuda para enviar*
uma avaliação. O B2W contém avaliações *já escritas* em português. Ambos os
conjuntos foram ligados à mesma taxonomia, mas a relação texto–rótulo mudou.
Há ainda 32 intenções sem casos no conjunto elegível. Nenhum resultado nesta
amostra estima a capacidade de reconhecer as 46 intenções em atendimento real.

## Fontes pesquisadas e decisão

- [Bitext Retail eCommerce](https://huggingface.co/datasets/bitext/Bitext-retail-ecommerce-llm-chatbot-training-dataset): útil para protótipo e validação interna, mas é inglês e formulado como solicitações de atendimento.
- [Sentence Transformers multilíngue](https://sbert.net/docs/sentence_transformer/pretrained_models.html): o MiniLM multilíngue foi treinado para representar textos em mais de 50 idiomas; o teste local mostra que resolver idioma isoladamente não resolve este domínio.
- [ConsumerBR](https://aclanthology.org/2026.propor-1.66/): mais de 3,1 milhões de reclamações reais anonimizadas em português brasileiro. É fonte promissora de textos candidatos para anotação, mas **não** traz rótulos das 46 intenções; seus metadados, incluindo nota, não substituem anotação humana. O CSV integral tem aproximadamente 5,2 GiB e não foi baixado para este ambiente.
- [Brazilian Customer Service Conversations](https://huggingface.co/datasets/RichardSakaguchiMS/brazilian-customer-service-conversations): contém rótulos de atendimento em PT-BR, mas o próprio cartão declara conversas sintéticas e somente nove intenções. Não atende à exigência de exemplos reais ou à taxonomia Bitext.
- [Pesquisa em atendimento de e-commerce](https://aclanthology.org/2021.ecnlp-1.7/): evidencia o valor de dados do domínio e casos negativos; não justifica converter reviews em solicitações nem afirmar desempenho externo sem teste.

## Execução proposta para T2

1. **Fixar a pergunta e o manual.** A unidade é a primeira solicitação real de
   um cliente ao suporte. Definir cada uma das 46 intenções com exemplos e
   contraexemplos; acrescentar `fora_de_escopo` para reviews já publicados,
   mensagens sem pedido e casos que a taxonomia não cobre. Uma eventual
   hierarquia de categorias deve ser documentada como outra tarefa, não como
   substituição silenciosa dos 46 rótulos do TP3.
2. **Obter textos reais.** Priorizar mensagens de suporte do projeto, se houver
   consentimento e tratamento de dados pessoais. Se não houver, amostrar
   reclamações públicas anonimizadas do ConsumerBR, verificando licença,
   proveniência e adequação ao cenário de atendimento. Não utilizar nota,
   resposta da empresa nem categoria automática como rótulo de intenção.
3. **Anotar com humanos.** Remover identificadores pessoais, deduplicar por
   texto normalizado e por conversa, atribuir IDs estáveis, aplicar dupla
   anotação cega e adjudicação com justificativa. Registrar `incerto` e
   `fora_de_escopo`. Amostrar deliberadamente intenções raras e difíceis;
   documentar que essa amostragem não representa prevalência natural.
   Fazer primeiro um piloto de cerca de 300 solicitações para corrigir o manual
   e verificar se a taxonomia cobre os textos. Só depois dimensionar a coleta
   principal. Como referência de planejamento, 30 casos de teste por intenção
   exigiriam até 1.380 exemplos **apenas no teste** se as 46 classes forem
   avaliadas individualmente; treino e validação exigem exemplos adicionais.
   O volume final deve ser definido pela disponibilidade real de cada classe,
   não por duplicação artificial de exemplos.
4. **Separar antes de modelar.** Reservar um teste novo por conversa/origem,
   com rótulos ocultos até a escolha final. Dividir o restante em treino e
   validação, bloqueando duplicatas e paráfrases próximas entre partições.
   Os 422 B2W existentes podem continuar como teste de transferência para
   *reviews*, mas não como fonte repetida de seleção. Se forem usados para
   desenvolver o modelo, deixarão de ser teste externo e exigirão substituto.
5. **Comparar candidatos na validação PT-BR.** Começar por TF-IDF de palavras
   e caracteres + regressão logística/SVM linear; depois avaliar encoder
   multilíngue ou português com a mesma partição. Ajustar pesos, limiares e
   abstenção somente na validação. O teste novo é executado uma vez após a
   seleção. Não integrar o modelo à API nesta etapa de dados.
6. **Critério de aceitação.** Reportar acurácia **e** Macro-F1 nas classes com
   suporte, recall/suporte por intenção, matriz de confusão e taxa de
   abstenção. A meta de 60% será considerada alcançada apenas se acurácia
   ≥0,60 e Macro-F1 ≥0,60 no novo teste de solicitações reais, com todas as
   classes avaliadas e intervalo de confiança para a acurácia. Se 46 classes
   não tiverem suporte suficiente, declarar explicitamente a cobertura e
   restringir a afirmação ao escopo realmente medido.

## Dependências humanas

Ainda faltam justificativas para 84 adjudicações antigas (60 no teste
elegível). Elas não podem ser inventadas. Também não há hoje um corpus PT-BR
de solicitações reais com os 46 rótulos humanos e um teste novo reservado.
Essas são dependências de coleta/anotação, não falhas corrigíveis por mudar
apenas o algoritmo.

### Primeiro passo executado: piloto ConsumerBR

Foi preparada uma seleção reproduzível de **320 reclamações reais anonimizadas**
do ConsumerBR: 240 para desenvolvimento com duas planilhas independentes de
anotação cega e 80 reservadas, ainda sem rótulo. A seleção percorreu as
primeiras 30.000 linhas do ZIP por leitura remota, sem baixar o arquivo
integral, e escolheu 40 textos de cada uma de oito empresas de varejo on-line.
O [manifesto](consumerbr_pilot_manifest.json) registra fonte, licença, hashes,
contagens e limites sem publicar os relatos. O
[protocolo de anotação](../../docs/consumerbr_pilot_annotation_protocol.md)
explica `fora_de_escopo`, incerteza, dupla revisão e adjudicação. Os arquivos
com texto permanecem apenas em `outputs/tp3-consumerbr/`, ignorado pelo Git.

**Estado:** as 240 reclamações de desenvolvimento receberam duas avaliações
independentes. Houve 73 concordâncias claras e 167 decisões de adjudicação com
justificativa, gerando um conjunto consolidado com 20 rótulos finais. O
resumo sem textos está em
[consumerbr_human_labels.md](consumerbr_human_labels.md); o CSV com relatos e
rótulos permanece privado. Os 80 reservados continuam sem rótulo e não foram
incluídos na seleção de modelo. Ainda não há nova métrica de 60%: a cobertura
de 20 rótulos é insuficiente para alegar desempenho nas 46 intenções e a
avaliação final exigirá amostra maior conforme a cobertura observada.
