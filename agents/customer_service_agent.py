"""TP4 customer-service agent using the OpenAI Agents SDK and /classify."""
from __future__ import annotations

import asyncio
import json
import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from agents import Agent, Runner, function_tool

API_URL = os.getenv("ECOMSHIELD_API_URL", "http://127.0.0.1:8000")
API_TOKEN = os.getenv("ECOMSHIELD_API_TOKEN", "")


@function_tool
async def classify_customer_intent(text: str) -> str:
    """Classify a customer message through the protected E-ComShield API.

    Use this before answering a request about an order, payment, return, refund,
    delivery, account or product. It returns the predicted intent and confidence.
    """
    if not API_TOKEN:
        return json.dumps({"error": "ECOMSHIELD_API_TOKEN não configurado"})
    request = Request(
        f"{API_URL.rstrip('/')}/classify",
        data=json.dumps({"text": text}).encode("utf-8"),
        headers={"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            return response.read().decode("utf-8")
    except HTTPError as exc:
        return json.dumps({"error": f"API retornou HTTP {exc.code}"})


agent = Agent(
    name="Atendente E-ComShield",
    instructions=(
        "Você atende clientes de e-commerce em português. Sempre que a solicitação "
        "tiver uma intenção de suporte, use classify_customer_intent antes de responder. "
        "Explique de forma curta e educada; não invente status de pedidos nem políticas."
    ),
    tools=[classify_customer_intent],
)


async def main() -> None:
    conversation = [
        "Meu pedido ainda não chegou. Como acompanho a entrega?",
        "Também quero saber se posso pedir reembolso.",
        "Obrigado. Preciso falar com uma pessoa agora.",
    ]
    for turn, message in enumerate(conversation, start=1):
        result = await Runner.run(agent, message)
        print(f"Turno {turn} - cliente: {message}\nTurno {turn} - agente: {result.final_output}\n")


if __name__ == "__main__":
    asyncio.run(main())
