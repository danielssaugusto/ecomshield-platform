# E-ComShield

Projeto acadêmico de análise de feedback e classificação de intenções para
e-commerce. A estratégia de dados separa explicitamente duas finalidades:

| Finalidade | Dataset | Como é usado |
| --- | --- | --- |
| Feedback real e análise exploratória | B2W-Reviews01 | Avaliações reais em PT-BR; EDA, satisfação e amostra para validação humana. A nota não é usada como variável-alvo de intenção. |
| Classificação de intenção | Bitext Retail eCommerce | Corpus rotulado com os campos originais `instruction`, `category` e `intent`. |

Essa divisão evita a criação de intenções por heurísticas de palavras-chave. O
modelo de intenção deve usar apenas o campo `intent` publicado pelo Bitext.

## Reproduzir a parte de dados

Use Python 3.10 ou superior. As dependências abaixo são exclusivas desta parte
e não exigem instalar ou executar a API ou o banco:

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

Execute os notebooks `03` a `06` em ordem após os comandos. Os dois downloads
são fixados a revisões específicas e verificados por SHA-256. Os CSVs brutos e
derivados permanecem fora do Git; o arquivo versionado
`data/annotations/ptbr_human_labels.csv` guarda apenas decisões humanas e hashes
dos textos, não as avaliações originais. Seu manifesto documenta os hashes das
duas planilhas fornecidas pelos revisores. Os relatórios gerados resumem cada
etapa e as limitações metodológicas.

## Dataset de intenção

O pipeline preserva os 46 rótulos de intenção e as 13 categorias da fonte,
incluindo entrega, pedido, pagamento, troca e devolução. A fonte é o
[Bitext Retail eCommerce](https://huggingface.co/datasets/bitext/Bitext-retail-ecommerce-llm-chatbot-training-dataset),
sob licença CDLA-Sharing-1.0. O corpus se declara híbrido/sintético; essa
limitação é registrada nos relatórios e não é ocultada.

Para baixar, validar, dividir de modo determinístico e gerar o relatório:

```bash
python scripts/build_bitext_intent_dataset.py
```

O comando gera, localmente e sem versionar dados brutos:

- `data/raw/bitext-retail-ecommerce/bitext-retail-ecommerce.csv`
- `data/processed/bitext_retail_intents.parquet`
- `data/processed/bitext_retail_intents_report.json`
- `reports/bitext_retail_intents/relatorio.md`

As categorias e intenções não são renomeadas, inferidas ou combinadas pelo
pipeline. A divisão `train`/`validation`/`test` é estratificada por intenção e
determinística (aproximadamente 80/10/10). Textos idênticos permanecem na
mesma partição, evitando vazamento exato entre treino, validação e teste.

Para treinar e avaliar um baseline transparente, exclusivamente no Bitext:

```bash
python scripts/train_bitext_intent_baseline.py
```

O modelo e as métricas são gerados localmente. A avaliação usa somente o teste
isolado e não deve ser apresentada como desempenho em dados brasileiros reais.
O notebook de avaliação é `notebooks/05_bitext_intent_baseline.ipynb`.
O relatório de erros fica em `reports/bitext_intent_model/erros.md`.

## B2W-Reviews01

O B2W-Reviews01 permanece como fonte complementar de avaliações reais em
português. Artefatos antigos que contêm rótulos por heurística não devem ser
usados para treinamento ou avaliação do classificador de intenção; são apenas
histórico da exploração inicial.

A fonte é o [B2W-Reviews01 da B2W Digital](https://github.com/americanas-tech/b2w-reviews01),
distribuído sob [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
O uso deve ser não comercial, com atribuição e compartilhamento pela mesma
licença. O CSV original não é versionado neste repositório.

Para regenerar a EDA do B2W sem criar intenções artificiais:

```bash
python scripts/generate_b2w_feedback_eda.py
```

O notebook correspondente é `notebooks/03_b2w_feedback_eda.ipynb`.

## Validação externa em português

Para responder à limitação de idioma e à origem híbrida/sintética do Bitext,
o projeto inclui uma fila reprodutível de revisão humana de feedbacks reais do
B2W. Ela não recebe rótulos automáticos. O protocolo, os critérios de dupla
anotação e a métrica de concordância estão em
[`docs/ptbr_intent_validation_protocol.md`](docs/ptbr_intent_validation_protocol.md).

```bash
python scripts/create_ptbr_validation_queue.py
```

As 500 avaliações já receberam duas anotações humanas independentes e 125
divergências foram adjudicadas. Para reproduzir o CSV final a partir das
decisões versionadas, use `scripts/rebuild_ptbr_validation_dataset.py`. Isso
não recria decisões humanas ausentes nem transforma casos incertos em certeza.

O panorama completo e as limitações da entrega de dados estão em
[`reports/data_methodology/relatorio.md`](reports/data_methodology/relatorio.md).

Após a dupla anotação e a adjudicação, o conjunto PT-BR fica reservado para
avaliação externa. Ele não deve ser usado no treinamento do baseline Bitext.
O notebook descritivo correspondente é
`notebooks/06_ptbr_validated_dataset_eda.ipynb`.

## TP2 — análise exploratória aprofundada

O [relatório separado de EDA](reports/tp2_data_eda/relatorio.md) reúne o
heatmap de correlação e os scatter plots do Bitext com o teste formal
Mann–Whitney da hipótese de comprimento textual do B2W. Os notebooks
`04_bitext_intent_eda.ipynb` e `03_b2w_feedback_eda.ipynb` contêm o código,
as saídas executadas e a interpretação. A análise de dados é descritiva e
independente da API. Para verificar os testes da parte de
dados, execute `python -m pytest tests/test_data_pipeline.py -q` no ambiente
instalado com `requirements-data.txt`.

## API e segurança

A aplicação FastAPI completa está em `src.main:app`. Configure `DATABASE_URL`
e uma `SECRET_KEY` aleatória e persistente em `.env` (veja `.env.example`),
instale `requirements.txt` e execute `uvicorn src.main:app --reload`.
O cadastro público cria somente usuários `viewer`; a criação inicial de um
administrador exige definir `ADMIN_BOOTSTRAP_PASSWORD` antes do primeiro boot.
Sem essa variável, nenhum administrador com senha padrão é criado.
Em bancos já inicializados pela versão anterior, a conta `admin` pode ainda
ter a senha antiga; ela precisa ter a senha rotacionada antes de expor a API.

Execute `python -m pytest tests/test_api.py tests/test_security.py -q` para
verificar autenticação, autorização por objeto, validação de payloads e
controles básicos. O relatório de EDA canônico é
[`reports/tp2_data_eda/relatorio.md`](reports/tp2_data_eda/relatorio.md).
O scan passivo do OWASP ZAP precisa ser executado contra a API local;
resultados simulados não são aceitos como relatório da ferramenta. Consulte
[`reports/relatorio_owasp_zap.md`](reports/relatorio_owasp_zap.md).

## Ferramentas
 - Jupyter Notebook
 -  Docker
 -  Python 3.11+
 -  FastAPI

## Setting Up the Virtual Environment
To create an isolated Python environment for the project, follow the instructions for your operating system.

### Linux
Create the virtual environment:
```bash
python3 -m venv .venv
```

Activate the virtual environment:
```bash
source .venv/bin/activate
```

Once activated, your terminal should look similar to:
```text
(.venv) user@computer:~/ecomshield-platform$
```

> [!NOTE]
> The `(.venv)` prefix indicates that the virtual environment is currently active.

### Windows
Create the virtual environment:
```powershell
python -m venv .venv
```

Activate the virtual environment:
```powershell
.venv\Scripts\activate
```

### Installing Dependencies
Before installing the project dependencies, make sure the project contains either a `pyproject.toml` or a `setup.py` file in its root directory.

These files contain the project's **Python packaging configuration**. They define information such as the project name, version, dependencies, build system, and other metadata required by Python package managers such as `pip`.

> [!NOTE]
> A `pyproject.toml` file is the modern and recommended approach for configuring Python projects. `setup.py` is the older approach and is still supported by many projects.

If neither file exists, running the following command will result in an error:
```bash
pip install -e ".[dev]"
```
This installs the project in editable mode along with the development dependencies defined for the project.

To verify the installed packages and their versions, run:
```bash
pip list
```

You can learn more about Python project configuration in the official Python documentation:
- [Python Packaging User Guide](https://packaging.python.org/)
- [Writing your pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [Setuptools Documentation](https://setuptools.pypa.io/)

Once `pyproject.toml` or `setup.py` is present, activate the virtual environment and install the project's dependencies.

> [!IMPORTANT]
> Make sure the virtual environment is activated before installing dependencies or running project commands.

## Running the Application
After installing the dependencies, make sure you are in the project's root directory:
    cd ecomshield-platform

The project uses **Uvicorn** as the ASGI server to run the FastAPI application.

Start the development server with:
    uvicorn src.main:app --reload

> [!IMPORTANT]
> Run the Uvicorn command from the project's root directory.

The `src.main:app` syntax follows this structure:

    src.main:app
    │   │    │
    │   │    └── FastAPI application instance
    │   └────── Python module (main.py)
    └────────── Python package (src)

The `--reload` option automatically restarts the development server whenever changes are detected in the source code.

Once the server is running, the API will be available at:

    http://127.0.0.1:8000

### Health Check
The project provides a health check endpoint to verify that the API is running correctly:

    http://127.0.0.1:8000/health

Expected response:

    {
        "status": "ok"
    }

### API Documentation
FastAPI automatically generates interactive API documentation.
**Swagger UI:**

    http://127.0.0.1:8000/docs

**ReDoc:**

    http://127.0.0.1:8000/redoc

> [!NOTE]
> The `--reload` option is intended for development environments. It should not be used in production.
