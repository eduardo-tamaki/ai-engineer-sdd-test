"""
Wrapper mínimo para chamadas ao Bedrock.

A autenticação usa o short-term API key do Bedrock via variável de ambiente
`AWS_BEARER_TOKEN_BEDROCK` (suportada pelo boto3 ≥ 1.39). Você não precisa de
AWS_ACCESS_KEY_ID / SECRET — basta exportar a chave fornecida.

Este arquivo é intencionalmente curto. Sinta-se à vontade para:
- Trocar por chamadas via Anthropic SDK (`anthropic[bedrock]`).
- Adicionar streaming, tool use, retries, cache, etc.
- Apagar e reescrever do zero.

Exemplo de uso:

    from llm import complete

    resp = complete(
        system="Você é um assistente útil.",
        messages=[{"role": "user", "content": [{"text": "Olá"}]}],
    )
    print(resp["output"]["message"]["content"][0]["text"])
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

import boto3


DEFAULT_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
)
DEFAULT_REGION = os.getenv("AWS_REGION", "us-east-1")


@lru_cache(maxsize=1)
def _client():
    return boto3.client("bedrock-runtime", region_name=DEFAULT_REGION)


def complete(
    messages: list[dict[str, Any]],
    system: str | None = None,
    model_id: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
    **extra: Any,
) -> dict[str, Any]:
    """
    Chama o endpoint Converse do Bedrock e devolve a resposta crua.

    `messages` segue o formato do Converse API:
        [{"role": "user", "content": [{"text": "..."}]}]

    Veja:
    https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html
    """
    params: dict[str, Any] = {
        "modelId": model_id or DEFAULT_MODEL_ID,
        "messages": messages,
        "inferenceConfig": {
            "temperature": temperature,
            "maxTokens": max_tokens,
        },
    }
    if system:
        params["system"] = [{"text": system}]
    params.update(extra)

    return _client().converse(**params)


def text_of(response: dict[str, Any]) -> str:
    """Atalho para extrair o texto da primeira mensagem retornada pelo Converse."""
    return response["output"]["message"]["content"][0]["text"]
