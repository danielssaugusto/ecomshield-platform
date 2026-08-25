# E-ComShield - Data Flow Diagram & Análise CIA

Este documento contém o diagrama de fluxo de dados (DFD) e a análise da Tríade CIA, cumprindo com as exigências de modelagem de ameaças e segurança do projeto.

## Data Flow Diagram (DFD)

O diagrama abaixo mapeia o fluxo de autenticação e predição, indicando claramente as fronteiras de confiança (Trust Boundaries) e os componentes do sistema.

```mermaid
flowchart TD
    subgraph Client [Fronteira de Confiança do Cliente / Usuário]
        A[Cliente / Interface]
    end

    subgraph Server [Fronteira de Confiança da Aplicação Backend]
        B(FastAPI Web Server)
        C{Módulo de Autenticação}
        D[(Fake DB - Usuários)]
        E[Módulo de Predição]
    end

    A -- "1. POST /auth/token (User, Pass)" --> B
    B -- "2. Valida credenciais" --> C
    C -- "3. Consulta usuário" --> D
    D -- "4. Retorna Hash" --> C
    C -- "5. Gera JWT Token" --> B
    B -- "6. Retorna Token" --> A

    A -- "7. POST /predict (Bearer JWT)" --> B
    B -- "8. Valida Token" --> C
    C -- "9. Token Válido" --> B
    B -- "10. Solicita Predição" --> E
    E -- "11. Resposta Placeholder" --> B
    B -- "12. Retorna Resultado" --> A
```

## Análise da Tríade CIA

A análise da Tríade CIA (Confidencialidade, Integridade, Disponibilidade) foi aplicada aos seguintes componentes do sistema:

### 1. API FastAPI (Web Server)
- **Confidencialidade:** As conexões devem ocorrer sobre TLS (HTTPS) no ambiente de produção para garantir que dados em trânsito (como senhas e tokens JWT) não sejam interceptados.
- **Integridade:** O servidor deve garantir que as rotas só processem requisições bem formatadas, utilizando a validação do Pydantic para evitar *payloads* maliciosos ou injetados.
- **Disponibilidade:** O servidor utiliza o Uvicorn, podendo escalar horizontalmente ou usar *load balancers* para assegurar que a API esteja sempre acessível e respondendo aos chamados dos clientes.

### 2. Módulo de Autenticação / Banco de Dados de Usuários
- **Confidencialidade:** O banco de dados (mesmo simulado em memória neste protótipo) não armazena as senhas em texto claro. É utilizado o `passlib` com o algoritmo `bcrypt` para gerar e armazenar apenas hashes irreversíveis.
- **Integridade:** Os tokens JWT são assinados digitalmente usando um `SECRET_KEY` forte (HS256). Qualquer tentativa de adulteração de privilégios ou identidade pelo cliente invalidará a integridade do token.
- **Disponibilidade:** Em um ambiente real, o banco de dados de usuários deve ser replicado e apresentar alta disponibilidade para que o gargalo de login não bloqueie o acesso aos serviços de predição.

### 3. Componente Cliente / Gerenciamento de Token
- **Confidencialidade:** O token de acesso deve ser guardado com segurança pelo lado do cliente (como variáveis de ambiente, cookies HTTP-only, ou mecanismos seguros da plataforma), evitando exposição em logs ou localStorage de forma vulnerável.
- **Integridade:** O cliente não deve (e não consegue, de forma validada) alterar o conteúdo do token, pois isso inviabiliza sua assinatura.
- **Disponibilidade:** O cliente deve gerenciar o ciclo de vida do token, prevendo retentativas e solicitando novos tokens caso o atual expire (implementando *refresh tokens*, se a arquitetura evoluir).
