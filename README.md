# E-ComShield

Projeto acadêmico de análise de feedback e intenções em e-commerce, com API FastAPI e verificações de segurança para o TP2.

**Autores:** Nathalia Calazans Artigas e Daniel Augusto da Silva.

> O projeto separa a análise de dados da aplicação. O B2W-Reviews01 contém avaliações reais em português, mas não traz intenção de atendimento anotada. O Bitext traz rótulos de intenção publicados pela fonte, porém é um corpus em inglês e híbrido/sintético. A API ainda **não** usa o classificador: `/predictions/predict` grava uma resposta *placeholder*.

## Índice

- [O que foi entregue](#o-que-foi-entregue)
- [Início rápido da API com Docker Compose](#início-rápido-da-api-com-docker-compose)
- [Execução local da API](#execução-local-da-api)
- [Rotas e controles de segurança](#rotas-e-controles-de-segurança)
- [Reproduzir a parte de dados](#reproduzir-a-parte-de-dados)
- [Resultados de dados e do TP2](#resultados-de-dados-e-do-tp2)
- [Testes e OWASP ZAP](#testes-e-owasp-zap)
- [Entrega, limitações e próximos passos](#entrega-limitações-e-próximos-passos)

## O que foi entregue

| Área | Evidência principal |
| --- | --- |
| EDA aprofundada do TP2 | [Relatório estruturado](reports/tp2_data_eda/relatorio.md), [notebook B2W](notebooks/03_b2w_feedback_eda.ipynb) e [notebook Bitext](notebooks/04_bitext_intent_eda.ipynb) |
| Classificação exploratória | [Baseline Bitext](reports/bitext_intent_model/relatorio.md) e [análise de erros](reports/bitext_intent_model/erros.md); **não integrado à API** |
| Revisão humana PT-BR | [Metodologia](reports/data_methodology/relatorio.md), [protocolo](docs/ptbr_intent_validation_protocol.md) e [relatório final](reports/ptbr_intent_validation/final_relatorio.md) |
| API e segurança | [Código FastAPI](src/main.py), [DFD](DFD.md), [testes](tests/test_security.py) e [triagem do ZAP](reports/relatorio_owasp_zap.md) |
| Entrega acadêmica | [PDF do TP2](output/pdf/nathalia_artigas_PB_TP2.PDF) |

Os notebooks `01_data_cleaning.ipynb` e `02_eda.ipynb` documentam a exploração inicial do TP1. Para os resultados atuais do TP2, use os notebooks `03` a `06` e os relatórios vinculados acima.

### Estrutura resumida

| Caminho | Conteúdo |
| --- | --- |
| `src/app/routers/`, `src/app/models.py`, `src/app/database.py` | Rotas, schemas/tabelas SQLModel e acesso ao banco |
| `scripts/` | Download verificado, preparação dos dados, baseline, relatórios, ZAP e geração do PDF |
| `notebooks/` | EDA, avaliação do baseline e análise descritiva da amostra humana |
| `data/annotations/` | Decisões humanas e manifesto de proveniência, sem textos brutos das avaliações |
| `reports/` | Relatórios, figuras, resultados do ZAP e limitações |
| `output/pdf/` | PDF final do TP2 |

## Início rápido da API com Docker Compose

**Pré-requisitos:** Git e Docker com o comando `docker compose`. O Compose sobe PostgreSQL 16 e a API. As credenciais do exemplo são apenas para desenvolvimento local.

```bash
git clone https://github.com/danielssaugusto/ecomshield-platform.git
cd ecomshield-platform
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copie a chave gerada para `SECRET_KEY=<valor>` em `.env` (descomente a linha). Mantenha-a secreta e estável entre reinícios: sem essa configuração, a aplicação gera uma nova chave a cada processo e tokens emitidos anteriormente deixam de valer. A URL `DATABASE_URL` de `.env.example` usa o host `db`, válido **dentro** da rede do Compose. Se quiser criar o administrador no primeiro boot, defina também `ADMIN_BOOTSTRAP_PASSWORD` com uma senha forte. Não publique `.env`.

No PowerShell, use `Copy-Item .env.example .env` em vez de `cp`; os demais comandos Docker são os mesmos.

```bash
docker compose up --build -d
docker compose ps
curl http://127.0.0.1:8000/health
```

A resposta esperada é `{"status":"ok","message":"API operacional"}`. Esse endpoint confirma que a API responde; **não** testa sozinho a disponibilidade do banco. Para acompanhar a inicialização e parar os serviços:

```bash
docker compose logs -f api
docker compose down
```

`docker compose down` mantém o volume `pgdata`. **Não** acrescente `-v` se quiser preservar o banco. O esquema é criado na inicialização via SQLModel; o projeto não dispõe de migrações de banco. Em um banco criado por versões antigas, uma conta `admin` existente pode conservar senha antiga: revise-a antes de expor a API.

- Saúde: <http://127.0.0.1:8000/health>
- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- OpenAPI: <http://127.0.0.1:8000/openapi.json>

As interfaces Swagger/ReDoc usam recursos estáticos locais, com origem, licença e hashes descritos em [`src/app/static/THIRD_PARTY.md`](src/app/static/THIRD_PARTY.md).

## Execução local da API

Use **Python 3.11 ou superior** e um PostgreSQL acessível ao processo local. A `DATABASE_URL` padrão do Compose (`@db:5432`) **não funciona fora dos contêineres**; para execução local, configure em `.env` uma URL com host e credenciais reais, por exemplo `postgresql://usuario:senha@localhost:5432/ecomshield`. O banco e o usuário já devem existir.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn src.main:app --reload
```

No PowerShell, ative o ambiente com `.venv\Scripts\Activate.ps1`. O `--reload` serve apenas ao desenvolvimento; o [Dockerfile](Dockerfile) inicia sem ele. Configure uma `SECRET_KEY` persistente antes de usar autenticação de forma contínua. O arquivo `.env.example` explica as variáveis principais; `ALLOWED_ORIGINS` tem uma lista explícita em [`src/app/config.py`](src/app/config.py).

## Rotas e controles de segurança

| Rota | Uso e acesso |
| --- | --- |
| `POST /auth/register` | Cadastro público; cria somente usuário `viewer`; não aceita escolha de papel |
| `POST /auth/token` | Login via formulário `username`/`password`; devolve JWT |
| `GET /users/me` | Perfil do usuário autenticado |
| `GET /users/`, `GET /users/{id}` | Visão limitada ao próprio usuário; administrador pode consultar outros |
| `POST /reviews/`, `GET /reviews/`, `GET /reviews/{id}` | Avaliações vinculadas ao usuário; leitura filtrada por dono ou administrador |
| `POST /predictions/predict`, `GET /predictions/`, `GET /predictions/{id}` | Registra e consulta predições por usuário; o resultado de `predict` ainda é *placeholder* |
| `POST /refunds/`, `GET /refunds/`, `GET /refunds/{id}` | Solicitações de reembolso vinculadas ao usuário |
| `PATCH /refunds/{id}` | Atualização restrita ao administrador |
| `GET /health` | Estado básico da API, sem autenticação |

Os schemas de entrada usam Pydantic com `extra="forbid"`, recusando campos não previstos. As consultas usam SQLModel/SQLAlchemy. Recursos por ID e listagens são verificados por usuário para mitigar BOLA/IDOR. Isso **não** substitui uma tabela real de pedidos: `order_id` em reembolsos é um identificador informado na solicitação, sem validação contra um catálogo de pedidos nesta versão.

A autenticação usa senha com hash e JWT. Usuários desativados não conseguem fazer login nem reutilizar token. Com `ADMIN_BOOTSTRAP_PASSWORD` configurada, a inicialização cria o usuário `admin` apenas se ele ainda não existir; não existe senha padrão de administrador nem rotação automática de uma conta antiga. O middleware envia HSTS, `X-Frame-Options`, `X-Content-Type-Options` e CSP, além de CORS com allowlist. HSTS protege conexões HTTPS, não transforma HTTP local em TLS.

### Limite de autenticação

`POST /auth/token` aceita **5 tentativas por endereço IP em janela móvel de 60 segundos**; a seguinte recebe HTTP 429 com `Retry-After`. O valor reduz rajadas de tentativas automatizadas e tolera poucos erros de digitação em uma demonstração local. O contador é **em memória e por processo**: reiniciar a API o zera, workers não compartilham contagens e pessoas atrás do mesmo IP/NAT dividem a cota. Antes de produção, é necessário armazenamento compartilhado, tratamento correto de proxy/IP e monitoramento.

## Reproduzir a parte de dados

A parte de dados é independente da API e do banco. Use Python 3.10 ou superior, acesso à internet para obter os datasets e espaço em disco para CSVs/Parquet. Execute os comandos na raiz do repositório:

```bash
python3 -m venv .venv-data
source .venv-data/bin/activate
python -m pip install -r requirements-data.txt

python scripts/download_b2w_reviews.py
python scripts/build_bitext_intent_dataset.py
python scripts/rebuild_ptbr_validation_dataset.py
python scripts/generate_b2w_feedback_eda.py
python scripts/generate_ptbr_validation_eda.py
python scripts/train_bitext_intent_baseline.py
```

No Windows, crie o ambiente com `python -m venv .venv-data` e ative-o no PowerShell com `.venv-data\Scripts\Activate.ps1` antes de instalar as dependências.

O primeiro download obtém o B2W; o segundo script obtém o Bitext, se necessário. Ambos fixam revisão/URL e verificam SHA-256. `rebuild_ptbr_validation_dataset.py` reconstrói a amostra final usando as **decisões humanas versionadas** em `data/annotations/`; não inventa rótulos novos. CSVs/Parquet brutos ou derivados, bem como o modelo `.joblib`, são gerados localmente e não entram no Git. Para regenerar a fila original de anotação, separadamente, use `python scripts/create_ptbr_validation_queue.py`; isso **não** substitui as anotações já concluídas.

Para abrir e executar os notebooks atuais:

```bash
jupyter notebook
```

A sequência é `03_b2w_feedback_eda.ipynb`, `04_bitext_intent_eda.ipynb`, `05_bitext_intent_baseline.ipynb` e `06_ptbr_validated_dataset_eda.ipynb`. Os relatórios e figuras principais já estão versionados; reproduzir tudo não é pré-requisito para ler a entrega.

### Fontes, papéis e licenças

| Fonte | Papel e volume utilizado | Limite importante |
| --- | --- | --- |
| [B2W-Reviews01](https://github.com/americanas-tech/b2w-reviews01) — CC BY-NC-SA 4.0 | 132.373 avaliações originais; 131.347 feedbacks após limpeza. Fonte de EDA e amostra humana PT-BR. | Avaliações de 2018, não chamados de suporte nem intenções originalmente anotadas. Uso não comercial, atribuição e compartilhamento conforme a licença. |
| [Bitext Retail eCommerce](https://huggingface.co/datasets/bitext/Bitext-retail-ecommerce-llm-chatbot-training-dataset) — CDLA-Sharing-1.0 | 44.884 solicitações preparadas, 46 intenções e 13 categorias originais. Fonte de rótulos para baseline. | Corpus em inglês, híbrido/sintético; não equivale a desempenho em atendimento brasileiro. |
| Amostra B2W revisada por humanos | 500 avaliações com dupla anotação e adjudicação de divergências. Reservada para avaliação externa. | Amostragem balanceada por nota; não estima distribuição operacional de intenções. |

**Não treinamos intenções usando rótulos criados por palavras-chave no B2W.** O Bitext foi dividido de forma determinística em treino, validação e teste (aproximadamente 80/10/10), agrupando textos idênticos na mesma partição; houve zero sobreposição textual **exata** entre elas. Isso não prova ausência de paráfrases ou outras formas de vazamento semântico. As respostas de referência do Bitext não entram como entrada do classificador.

## Resultados de dados e do TP2

- **EDA de intenções:** o [relatório TP2](reports/tp2_data_eda/relatorio.md) traz heatmap de Spearman, dois scatter plots e interpretação. Comprimento da solicitação e da resposta têm correlação aproximada de **0,05** neste corpus.
- **Hipótese formal:** no B2W, avaliações com notas 1–2 tendem a ter textos mais longos que as de notas 4–5. O teste Mann–Whitney unilateral encontrou `p < 10^-300`, medianas de **154 vs. 102 caracteres** e probabilidade de superioridade de **0,6771**. É uma análise exploratória e observacional, não causal.
- **Baseline de intenção:** TF-IDF + regressão logística obteve **Macro F1 de 0,9887** no teste interno isolado do Bitext. O número **não** é desempenho em português e o modelo **não** está ligado a `/predictions/predict`. Consulte o [relatório](reports/bitext_intent_model/relatorio.md) e os [erros](reports/bitext_intent_model/erros.md).
- **Revisão humana:** 500 rótulos finais, sendo 375 por concordância dupla e 125 por adjudicação; 78 casos marcados incertos ficam fora da avaliação principal, restando 422 elegíveis. Concordância simples de 75,00% e kappa de Cohen de 0,5504. A amostra contém 20 das 46 intenções, e 84 decisões adjudicadas não têm justificativa textual recuperável. Ela permanece reservada para avaliação externa; **a métrica nessa amostra ainda não foi calculada**. Veja [protocolo](docs/ptbr_intent_validation_protocol.md), [metodologia](reports/data_methodology/relatorio.md) e [relatório final](reports/ptbr_intent_validation/final_relatorio.md).

## Testes e OWASP ZAP

Após instalar as dependências da API, execute:

```bash
python -m pytest tests/ -q
```

A última verificação desta entrega passou com **16 testes**, incluindo acesso sem token, tentativa de leitura de recurso alheio, rejeição de campo extra, limites de login e cabeçalhos. Os testes de API usam SQLite em memória; uma validação separada com **PostgreSQL 16.15** confirmou persistência após reinício e respostas **403/200/401** para outro usuário/dono/sem token. A suíte automatizada não substitui testes de integração completos com PostgreSQL.

O scan passivo **real** do OWASP ZAP 2.17.0 está em [HTML](reports/zap_report.html), [JSON](reports/zap_report.json) e [triagem explicada](reports/relatorio_owasp_zap.md). Foram importadas 17 URLs, sem sessão autenticada. Houve **zero alertas High** e **um Medium**: `style-src 'unsafe-inline'` em `/docs`. O risco foi **aceito apenas para o TP2 local**, não corrigido. Há ainda dois tipos de alerta Low e três informativos, detalhados no relatório. O scan passivo não prova ausência de BOLA/IDOR ou de vulnerabilidades exploráveis; os testes de autorização constituem evidência separada.

Para repetir uma varredura de leitura em uma API local com ZAP portátil:

```bash
python scripts/run_owasp_zap_scan.py --zap-home /caminho/ZAP_2.17.0 --target http://127.0.0.1:8000
```

A opção `--import-openapi` aumenta a cobertura, mas **pode enviar POSTs**: use-a somente em banco descartável. Sem `--zap-home`, o script usa a imagem Docker do ZAP; consulte o [procedimento](reports/relatorio_owasp_zap.md). O scan foi passivo e não autenticado, não um pentest completo.

## Entrega, limitações e próximos passos

Para o TP2, envie:

1. O [PDF final](output/pdf/nathalia_artigas_PB_TP2.PDF), nomeado `nathalia_artigas_PB_TP2.PDF`, com **Nathalia Calazans Artigas e Daniel Augusto da Silva** identificados como autores.
2. O [link do repositório na `main`](https://github.com/danielssaugusto/ecomshield-platform/tree/main).
3. O [relatório exportado pelo ZAP](reports/zap_report.html) e, para facilitar a correção, o [documento de findings](reports/relatorio_owasp_zap.md).

O PDF pode ser regenerado a partir dos relatórios e figuras versionados com `python -m pip install reportlab` e `python scripts/build_tp2_submission_pdf.py`. O gerador usa Arial no macOS ou DejaVu Sans no Linux. A entrega no portal da disciplina deve ser feita pelos autores; publicar no GitHub não a substitui.

**Limitações que não devem ser omitidas:** o Bitext não demonstra desempenho em PT-BR; o B2W não possui intenção nativa; 78 rótulos humanos permanecem incertos; o endpoint de predição é *placeholder*; o rate limiting não é distribuído; `order_id` não é verificado contra pedidos reais; o Compose expõe HTTP local sem configurar TLS; e o alerta Medium de CSP permanece aceito somente no contexto local. Antes de uso público, é preciso validar o modelo em dados apropriados, completar o domínio de pedidos e revisar a segurança, inclusive HTTPS e a exposição de `/docs`.

O código do repositório possui [licença MIT](LICENSE); os datasets têm licenças próprias, indicadas acima, que devem ser respeitadas independentemente da licença do código.
