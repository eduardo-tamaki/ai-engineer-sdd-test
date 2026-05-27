"""
Exemplo MÍNIMO de agente com LangGraph + Amazon Bedrock.

Intenção
========
Este arquivo é um ponto de partida. Ele mostra o **wiring** entre LangGraph,
Bedrock e Chainlit — não resolve o problema do desafio. Espera-se que você
substitua/expanda este código durante a Fase 3.

O que este exemplo demonstra
----------------------------
1. Estado da conversa tipado (TypedDict + reducer `add_messages`).
2. Um `StateGraph` declarativo — dá pra olhar `_build_graph()` e ver os
   estados/transições sem caçar `if/else` espalhados pelo arquivo.
3. Chamada ao Bedrock via `ChatBedrockConverse` — ele cria internamente um
   client `boto3.bedrock-runtime` que lê automaticamente a variável de
   ambiente `AWS_BEARER_TOKEN_BEDROCK` (short-term API key). Você não precisa
   passar `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`.
4. Entrypoint `handle_message` integrado ao Chainlit em `app.py`.

O que você ainda precisa fazer (não-exaustivo)
----------------------------------------------
- Estender o `AgentState` com os campos relevantes para sua modelagem
  (`patient_id`, `exam_id`, `desired_date`, `selected_slot`, `phase`, etc.).
- Adicionar nós para extrair intenção, validar paciente, buscar slots,
  apresentar preparo, confirmar booking. Use **arestas condicionais**
  (`add_conditional_edges`) — não `if/else` dentro de um nó gigante.
- Implementar as tools que chamam `api/exam_scheduler.py` e amarrá-las ao
  LLM via `llm.bind_tools(...)` + `ToolNode`. As chamadas a tools devem
  ficar separadas da lógica de raciocínio do LLM (restrição do enunciado).
- Tratar erros explicitamente — sem depender de `try/except` no topo do
  `app.py`. Por exemplo: nó dedicado para `availability_error` quando a API
  retorna 500.

Veja o `SPEC.md` que você escreveu na Fase 2.
"""

from __future__ import annotations

import os
from typing import Annotated, TypedDict

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


SYSTEM_PROMPT = """Você é o assistente virtual de agendamento de exames de um hospital.

Tom de voz (obrigatório):
- Sempre em português.
- Formal mas acolhedor. Trate o paciente por "você" — nunca "o senhor" ou "a senhora".
- Nunca dê diagnóstico nem opinião médica.
- Mencione instruções de preparo ANTES de confirmar qualquer horário, nunca depois.
- Em caso de falha do sistema, não exponha detalhes técnicos — peça desculpas e
  oriente o paciente sobre o próximo passo.

Este é apenas o prompt base do exemplo. Você provavelmente vai querer prompts
específicos por nó (extração de intenção, apresentação de slots, etc.)."""


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------


class AgentState(TypedDict):
    """Estado tipado da conversa.

    O reducer `add_messages` faz com que retornos parciais de nós
    (ex.: `{"messages": [nova_msg]}`) sejam **appended** à lista existente,
    em vez de sobrescrita.

    Estenda este TypedDict com os campos da sua modelagem. Mantenha-os
    explícitos e tipados — o enunciado proíbe esconder estado em variáveis
    globais ou no histórico cru de mensagens.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    # patient_id: str | None
    # exam_id: str | None
    # desired_date: str | None
    # selected_slot: dict | None
    # phase: Literal["greeting", "collecting", "presenting_slots", "confirmed", ...]


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------


def _build_llm() -> ChatBedrockConverse:
    """Cliente Bedrock.

    `ChatBedrockConverse` usa o Converse API do Bedrock por baixo dos panos.
    Quando você não passa um `client` explícito, ele cria um via
    `boto3.client('bedrock-runtime', region_name=...)`, que lê a variável
    `AWS_BEARER_TOKEN_BEDROCK` automaticamente (boto3 ≥ 1.39).
    """
    return ChatBedrockConverse(
        model=os.getenv(
            "BEDROCK_MODEL_ID",
            "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        ),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        temperature=0.3,
        max_tokens=1024,
    )


# Instanciado uma única vez no import — barato; só guarda configuração.
LLM = _build_llm()


# ---------------------------------------------------------------------------
# Nós
# ---------------------------------------------------------------------------


def chat_node(state: AgentState) -> dict:
    """Nó único deste exemplo: empilha o system prompt e chama o LLM.

    Substitua por uma topologia mais rica. Padrão típico para este desafio:

        START
          ↓
        extract_intent          (LLM com saída estruturada)
          ↓
        route                   (aresta condicional baseada no estado)
          ↓                ↘
        ask_for_missing     fetch_availability   (tool)
          ↓                     ↓
        ...                  present_slots
                                ↓
                              confirm_booking   (tool)
                                ↓
                               END
    """
    prompt = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    reply = LLM.invoke(prompt)
    return {"messages": [reply]}


# ---------------------------------------------------------------------------
# Grafo
# ---------------------------------------------------------------------------


def _build_graph():
    g = StateGraph(AgentState)
    g.add_node("chat", chat_node)
    g.add_edge(START, "chat")
    g.add_edge("chat", END)
    return g.compile()


GRAPH = _build_graph()


# ---------------------------------------------------------------------------
# Entrypoint chamado por app.py
# ---------------------------------------------------------------------------


async def handle_message(user_message: str, session: dict) -> str:
    """Recebe a mensagem do usuário, roda o grafo, devolve a resposta em texto.

    `session` é o `cl.user_session` do Chainlit (um dict mutável que sobrevive
    entre mensagens do mesmo chat). Persistimos a lista de mensagens aqui;
    quando o estado ficar mais rico, persista o `state` inteiro.
    """
    previous: list[BaseMessage] = session.get("messages", [])
    state: AgentState = {
        "messages": [*previous, HumanMessage(content=user_message)],
    }

    result = await GRAPH.ainvoke(state)
    session["messages"] = result["messages"]

    last = result["messages"][-1]
    # `.content` em ChatBedrockConverse pode vir como string ou como lista de
    # blocos (text, tool_use, ...). Aqui só lidamos com texto — quando você
    # adicionar tools, ajuste para iterar pelos blocos.
    if isinstance(last.content, str):
        return last.content
    return "".join(
        block.get("text", "") for block in last.content if isinstance(block, dict)
    )
