# Piloto ConsumerBR: anotação humana de solicitações reais

## Objetivo e situação

Esta é uma **fila de anotação**, ainda sem ground truth. Os 240 textos de
desenvolvimento foram selecionados de reclamações reais anonimizadas do
[ConsumerBR](https://doi.org/10.5281/zenodo.18022568), licença CC BY 4.0.
Outros 80 textos ficaram em arquivo privado separado e **não** devem ser vistos
pela equipe que escolherá modelos ou hiperparâmetros. O arquivo de origem,
mesmo anonimizado pelos autores, pode conter dados pessoais residuais; não
publique as planilhas nem copie relatos para o repositório ou serviços externos.

A amostra usa somente as primeiras 30.000 linhas do ZIP de origem e 8 empresas
de varejo on-line, com 40 registros de cada. Esse recorte facilita o piloto,
mas não representa a distribuição de todas as reclamações nem de um atendimento
em produção. A empresa foi usada somente para amostragem e foi omitida das
planilhas dos anotadores. Nota, resposta, status e demais campos não são
rótulos de intenção.

## Instruções aos dois anotadores

Cada pessoa recebe apenas sua própria planilha: `piloto_anotador_A.xlsx` ou
`piloto_anotador_B.xlsx`. Para cada linha, leia o texto completo e preencha:

1. **Intenção:** selecione um dos 46 rótulos originais do Bitext, quando o
   pedido principal corresponder claramente a ele. A aba `Intenções` contém
   a lista. `fora_de_escopo` é a única classe adicional deste piloto, para
   relatos sem pedido enquadrável na taxonomia.
2. **Incerto?:** `não` se a decisão for clara; `sim` se faltar contexto, houver
   pedidos concorrentes sem prioridade clara ou a distinção entre classes
   continuar ambígua. Se marcar `sim`, pode deixar a intenção vazia.
3. **Justificativa:** é obrigatória para `fora_de_escopo` e `sim`; explique
   por que a taxonomia não se aplica ou por que não foi possível decidir.
   Decisões claras não exigem justificativa nesta fase. Não inclua dados
   pessoais. Toda decisão de adjudicação posterior terá justificativa textual.
4. **Revisor:** escreva seu nome ou identificador estável. A coluna `Situação`
   indica `Completo` quando os campos exigidos estão presentes.

Trabalhe sozinho, sem consultar a planilha do outro anotador e sem usar
previsões de modelo, nota, empresa ou resposta como pistas. Não reescreva o
texto nem os IDs. Se uma reclamação descreve vários problemas, priorize o
**pedido principal do consumidor**, não o primeiro substantivo encontrado.
Se nenhum pedido se destaca, marque `Incerto? = sim` e justifique. Não force
uma das 46 classes para atingir cobertura numérica.

### Distinções que exigem cuidado

- `cancel_order` é cancelar um pedido; `request_refund` é pedir devolução do
  valor pago. O relato pode mencionar ambos; anote o pedido principal ou
  incerteza se não houver como decidir.
- `delivery_time` trata de prazo; `track_delivery` de acompanhar entrega;
  `delivery_issue` de problema geral de entrega. Um atraso concreto pode
  combinar as três ideias; registre a razão da escolha.
- `damaged_delivery`, `wrong_item` e `missing_item` descrevem problemas
  específicos da entrega. `product_issue` trata do produto ou funcionamento;
  não substitua automaticamente uma reclamação de entrega por ele.
- `submit_product_feedback` no Bitext costuma ser pedido de ajuda para
  **enviar** uma avaliação. Não use essa classe apenas porque o texto é uma
  opinião sobre produto ou empresa. Este é um erro de correspondência já
  observado no B2W.
- `fora_de_escopo` não é sinônimo de `incerto`: use o primeiro quando a
  taxonomia não contempla o pedido e o segundo quando a evidência textual
  não permite decidir com segurança.

## Controle e próximos passos

O [manifesto do piloto](../reports/tp3_data/consumerbr_pilot_manifest.json)
registra fonte, recorte, seleção determinística, hashes e limitações **sem
publicar os textos**. O script `scripts/prepare_consumerbr_pilot.py` reproduz
os arquivos privados. O script
`scripts/validate_consumerbr_pilot_annotations.py` deverá conferir as duas
planilhas devolvidas por ID, texto, taxonomia, campos obrigatórios e divergências.
Nenhum conflito será resolvido automaticamente: um terceiro revisor ou consenso
documentado fará a adjudicação.

Depois da revisão, somente os 240 casos de desenvolvimento podem sustentar
manual, comparação de modelos e validação. Os 80 reservados continuam sem
rótulos para a seleção. Este piloto não garante 60% nem cobre adequadamente as
46 intenções; ele mede a viabilidade do manual e identifica o volume real de
anotação necessário para a avaliação final.
