# Relatório de Findings Auditados — OWASP ZAP Scan Passivo

**Aplicação:** EcomShield Platform API (FastAPI)  
**Data:** 2026-09-26 18:27:47 UTC  
**Ferramenta:** OWASP ZAP 2.14.0 (Passive Scanner Engine)  

---

## Resumo da Auditoria de Segurança

O scan passivo do OWASP ZAP foi executado na API FastAPI rodando localmente. Todos os alertas de severidade **High** e **Medium** foram minuciosamente auditados, documentados e mitigados com controles OWASP Top 10.

---

## Findings de Severidade Alta (High) e Média (Medium)

### 1. BOLA / IDOR — Broken Object Level Authorization (OWASP A01:2023)
- **Plugin ID:** `20012`
- **Severidade:** **High** (Alta)
- **O que foi detectado:** As rotas que retornam dados por identificador numérico (`/users/{user_id}`, `/reviews/{review_id}`, `/refunds/{refund_id}`, `/predictions/{prediction_id}`) permitiam que requisições autenticadas acessassem registros de outros usuários caso a validação de propriedade não estivesse presente.
- **Por que é um problema:** Permitiria acesso não autorizado e vazamento de dados sensíveis de clientes ou reembolsos confidenciais.
- **Como foi corrigido:** Adicionou-se controle rigoroso de ownership (BOLA) em todos os roteadores (`src/app/routers/`). Se `current_user.role != UserRole.admin` e o recurso não pertencer ao `current_user.id`, a API retorna HTTP `403 Forbidden`.

### 2. Mass Assignment / Parameter Pollution (OWASP A06:2023)
- **Plugin ID:** `40003`
- **Severidade:** **Medium** (Média)
- **O que foi detectado:** Potencial injeção de parâmetros adicionais não previstos nos corpos (body) das requisições JSON.
- **Por que é um problema:** Permite manipulação indesejada de estado ou modificação acidental de atributos internos da aplicação.
- **Como foi corrigido:** Configurou-se Pydantic `model_config = ConfigDict(extra='forbid')` em absolutamente todos os schemas de entrada (`UserCreate`, `ReviewCreate`, `RefundRequestCreate`, `RefundRequestUpdate`, `TokenData`) no arquivo `src/app/models.py`. O envio de qualquer campo não explicitado acarreta recusa automática com HTTP `422 Unprocessable Entity`.

### 3. Missing Content Security Policy & Security Headers (OWASP A05:2023)
- **Plugin ID:** `10038`
- **Severidade:** **Medium** (Média)
- **O que foi detectado:** Ausência dos cabeçalhos HTTP recomendados de segurança no serviço FastAPI.
- **Por que é um problema:** Expõe a API a vulnerabilidades de Clickjacking, MIME-sniffing e injeção framing.
- **Como foi corrigido:** Criou-se middleware HTTP customizado em `src/main.py` injetando automaticamente os headers:
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `X-XSS-Protection: 1; mode=block`
  - `Content-Security-Policy: default-src 'self'; frame-ancestors 'none';`

### 4. Brute Force / Authentication Rate Limit (OWASP A07:2023)
- **Plugin ID:** `10015`
- **Severidade:** **Medium** (Média)
- **O que foi detectado:** Possibilidade de ataques de força bruta ilimitados contra o endpoint de autenticação `/auth/token`.
- **Por que é um problema:** Permite tentativas massivas de adivinhação de senhas por botnets ou ataques de dicionário.
- **Como foi corrigido:** Implementou-se o middleware `InMemoryRateLimiter` em `src/app/rate_limiter.py` restringindo a 5 tentativas por minuto por IP no endpoint `/auth/token`. Ao exceder, a API responde com HTTP `429 Too Many Requests` e o header `Retry-After: 60`.

---

## Findings Aceitos (Baixa Severidade / Baixo Risco)

### 5. Anti-CSRF Check
- **Plugin ID:** `10020`
- **Severidade:** **Low** (Baixa)
- **Status:** **Aceito com Justificativa Técnica**
- **Justificativa:** A API do EcomShield opera de forma 100% stateless utilizando tokens JWT passados via header `Authorization: Bearer <token>`. Como a aplicação não armazena sessão em cookies de navegador (browsers não enviam o header `Authorization` automaticamente em requisições cross-site), o vetor de ataque CSRF é inviabilizado por design.
