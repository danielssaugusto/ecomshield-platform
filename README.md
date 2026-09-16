# 🛡️ E-ComShield Platform

Plataforma completa e segura para e-commerce focada em gestão de reembolsos, análise de risco, controle de acesso baseado em funções (RBAC), banco de dados relacional PostgreSQL e análise de dados (EDA) com suporte a LLM tool calling.

---

## 🚀 Quickstart Guide (Guia Rápido)

Siga os passos abaixo para iniciar a aplicação rapidamente.

### Opção 1: Com Docker Compose (Recomendado)

Execute a API FastAPI e o Banco PostgreSQL 16 integrados em containers com um único comando:

1. **Clone o repositório e acesse a pasta:**
   ```bash
   git clone <URL_DO_REPOSITORIO>
   cd ecomshield-platform
   ```

2. **Configure as variáveis de ambiente:**
   ```bash
   cp .env.example .env
   ```

3. **Inicie os serviços via Docker:**
   ```bash
   docker compose up -d
   ```

4. **Acesse os serviços:**
   - 📖 **Documentação Interativa (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
   - 📌 **Documentação Alternativa (ReDoc):** [http://localhost:8000/redoc](http://localhost:8000/redoc)
   - ❤️ **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
   - 🔑 **Credenciais do Administrador Padrão:**
     - **Usuário:** `admin`
     - **Senha:** `senha123`

---

### Opção 2: Instalação Local (Sem Docker)

Se preferir rodar a aplicação localmente utilizando Python:

1. **Crie e ative o ambiente virtual:**
   - **Linux / macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .venv\Scripts\activate
     ```

2. **Instale TODAS as dependências com um único comando:**
   ```bash
   python -m pip install -r requirements.txt
   ```

3. **Configure o arquivo `.env`:**
   ```bash
   cp .env.example .env
   ```

4. **Inicie o servidor de desenvolvimento:**
   ```bash
   python -m uvicorn src.main:app --reload
   ```

5. **Acesse a API em [http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem & Framework:** Python 3.10+ / FastAPI
- **Banco de Dados & ORM:** PostgreSQL 16 + SQLModel (SQLAlchemy)
- **Autenticação & Segurança:** OAuth2 / JWT (python-jose, passlib, bcrypt)
- **Data Science & EDA:** Pandas, NumPy, PyArrow, Matplotlib, Seaborn
- **Ambientes de Desenvolvimento:** Docker & Docker Compose, Jupyter Notebook
- **Testes & Qualidade:** Pytest, HTTPX, Ruff

---

## 📦 Dependências do Projeto (`requirements.txt`)

Todas as bibliotecas necessárias para rodar a API, executar o banco de dados, gerar as análises de dados e rodar a suíte de testes estão consolidadas no arquivo `requirements.txt`:

```text
# Core API: fastapi, uvicorn, pydantic, pydantic-settings, python-multipart
# Auth: python-jose, passlib, bcrypt
# Database: sqlmodel, psycopg2-binary
# Data Science / EDA: pandas, pyarrow, numpy, matplotlib, seaborn
# Notebooks: jupyter, ipykernel
# Testing & Quality: pytest, httpx, ruff
```

Basta executar `pip install -r requirements.txt` para baixar tudo de uma vez.

---

## 📁 Estrutura do Projeto

```text
ecomshield-platform/
├── .env.example             # Modelo de variáveis de ambiente
├── docker-compose.yml       # Configuração dos serviços Docker (PostgreSQL 16 + API)
├── Dockerfile               # Build da imagem Docker da aplicação
├── pyproject.toml           # Metadados e configurações do projeto
├── requirements.txt         # Dependências completas consolidada do projeto
├── README.md                # Documentação e Quickstart Guide
├── data/
│   ├── raw/                 # Dados brutos recebidos
│   └── processed/           # Datasets processados em formato Parquet
├── notebooks/               # Notebooks Jupyter de Análise Exploratória (EDA)
│   └── 03_b2w_intent_eda.ipynb
├── scripts/                 # Scripts auxiliares para ETL e amostragem
│   ├── build_b2w_intent_dataset.py
│   └── create_b2w_review_sample.py
├── src/
│   ├── main.py              # Ponto de entrada da API FastAPI
│   └── app/
│       ├── auth.py          # Autenticação JWT e controle de acesso RBAC
│       ├── config.py        # Configurações globais da aplicação
│       ├── database.py      # Conexão e inicialização do banco de dados relacional
│       ├── seed.py          # Carga inicial do usuário administrador
│       ├── models/          # Modelos relacionais SQLModel
│       └── routers/         # Endpoints RESTful da API
└── tests/                   # Suíte de testes automatizados com Pytest
```

---

## 🗄️ Banco de Dados Relacional (PostgreSQL)

O projeto utiliza **SQLModel** para gerenciamento de banco de dados relacional PostgreSQL.

### Principais Entidades:
- **Users:** Cadastro de usuários e controle de funções (`admin`, `analyst`, `agent`, `customer`).
- **RefundRequests:** Gestão de solicitações de reembolso e transações.
- **RiskAssessments:** Análises e scores de risco detalhados por reembolso.
- **AuditLogs:** Registros de auditoria para rastreabilidade de ações na plataforma.

### Comandos do Docker Compose para o Banco:
- **Verificar status:** `docker compose ps`
- **Logs em tempo real:** `docker compose logs -f`
- **Resetar banco de dados (remover volumes):** `docker compose down -v`

---

## 🧪 Suíte de Testes

Para executar os testes automatizados da API:

```bash
pytest
```

---

## 📊 Dataset & Análise Exploratória (B2W-Reviews01)

A plataforma conta com um módulo de análise exploratória de intenções de suporte a clientes baseado no dataset público **B2W-Reviews01** (132.373 avaliações no e-commerce brasileiro).

### Como reproduzir a preparação do dataset:

```bash
mkdir -p data/raw/b2w-reviews01

curl -L -o data/raw/b2w-reviews01/B2W-Reviews01.csv \
  https://raw.githubusercontent.com/americanas-tech/b2w-reviews01/4639429ec698d7821fc99a0bc665fa213d9fcd5a/B2W-Reviews01.csv

python3 scripts/build_b2w_intent_dataset.py \
  --input data/raw/b2w-reviews01/B2W-Reviews01.csv \
  --output data/processed/b2w_reviews_intents.parquet \
  --report data/processed/b2w_reviews_intents_report.json
```

---

## 📜 Licença

Este projeto e os datasets derivados utilizam a licença **Creative Commons Attribution 4.0 International (CC BY 4.0)**.
