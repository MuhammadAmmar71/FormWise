"""Thin HTTP wrappers for Groq (chat) and Gemini (embeddings). No SDKs, so swapping providers is easy."""
import math

import httpx

from . import config

_client = httpx.Client(timeout=60)


def chat(messages: list[dict], model: str | None = None, temperature: float = 0.1, max_tokens: int = 700) -> str:
    resp = _client.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
        json={"model": model or config.CHAT_MODEL, "messages": messages,
              "temperature": temperature, "max_tokens": max_tokens},
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def embed_query(text: str) -> list[float]:
    resp = _client.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{config.EMBED_MODEL}:embedContent",
        params={"key": config.GEMINI_API_KEY},
        json={"content": {"parts": [{"text": text}]}, "taskType": "RETRIEVAL_QUERY",
              "outputDimensionality": config.EMBED_DIM},
    )
    resp.raise_for_status()
    vec = resp.json()["embedding"]["values"]
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]
