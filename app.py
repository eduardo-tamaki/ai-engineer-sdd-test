"""
Interface de chat (Chainlit) para conversar com o agente.

Subir:
    uv run chainlit run app.py

Disponível em http://localhost:8000.

Esta camada é fina de propósito: ela traduz o ciclo de mensagens do Chainlit
para chamadas do `agent.handle_message`. Toda a lógica do agente mora em
`agent.py` (e nos módulos que você criar).
"""

from __future__ import annotations

import chainlit as cl
from dotenv import load_dotenv

from agent import handle_message

load_dotenv()

@cl.on_chat_start
async def on_chat_start() -> None:
    cl.user_session.set("conversation_agente", {})
    await cl.Message(
        content=(
            "Olá! Sou o assistente de agendamento do hospital. "
            "Como posso te ajudar hoje?"
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    session: dict = cl.user_session.get("conversation_agente") or {}
    try:
        reply = await handle_message(message.content, session)
    except Exception as e:  # noqa: BLE001 — última linha de defesa só pro Chainlit não engasgar
        # NOTA: o agente em si NÃO deve depender deste catch-all para tratamento
        # de erro. As restrições técnicas do desafio pedem tratamento explícito.
        reply = (
            "Tive um problema técnico ao processar sua mensagem. "
            "Pode tentar de novo, por favor?"
        )
        print(f"[app.py] erro não tratado vindo do agente: {e!r}")
    cl.user_session.set("conversation", session)
    await cl.Message(content=reply).send()
