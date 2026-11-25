# Demonstração do agente de atendimento - TP4

O código do agente está em `agents/customer_service_agent.py`. Ele usa
`Agent`, `@function_tool` e `Runner.run` do OpenAI Agents SDK. A ferramenta
`classify_customer_intent` faz uma chamada autenticada a `POST /classify`.

## Como executar

Em um terminal, inicie a API:

```bash
PYTHONPATH=src uvicorn ecomshield.main:app --reload
```

Registre uma conta de teste, obtenha um token em `/auth/token` e exporte:

```bash
export OPENAI_API_KEY='...'
export ECOMSHIELD_API_TOKEN='token-jwt-de-teste'
python agents/customer_service_agent.py
```

## Conversa de três turnos usada na demonstração

1. Cliente: "Meu pedido ainda não chegou. Como acompanho a entrega?"
2. Cliente: "Também quero saber se posso pedir reembolso."
3. Cliente: "Obrigado. Preciso falar com uma pessoa agora."

O script imprime a resposta do agente em cada turno e registra a chamada à
ferramenta no trace do Agents SDK. A execução requer uma chave OpenAI válida;
nenhuma transcrição foi inventada ou incluída sem executar o agente.
