"""
LLM Client con fallback automático: NVIDIA (gratis) → Anthropic → OpenAI.
Todos los proveedores usan la interfaz OpenAI-compatible para uniformidad.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

NVIDIA_BASE_URL    = "https://integrate.api.nvidia.com/v1"
DEEPSEEK_BASE_URL  = "https://api.deepseek.com/v1"
ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"
OPENAI_BASE_URL    = "https://api.openai.com/v1"

NVIDIA_MODEL    = "meta/llama-3.3-70b-instruct"
DEEPSEEK_MODEL  = "deepseek-chat"
ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL    = "gpt-4o"


class Provider(str, Enum):
    NVIDIA    = "nvidia"
    DEEPSEEK  = "deepseek"
    ANTHROPIC = "anthropic"
    OPENAI    = "openai"


@dataclass
class LLMResponse:
    content: str
    provider: Provider
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0


@dataclass
class ProviderStatus:
    available: bool = True
    failure_count: int = 0
    last_failure_ts: float = 0.0
    cooldown_seconds: int = 60

    def mark_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_ts = time.time()
        if self.failure_count >= 3:
            self.available = False
            logger.warning("Provider marked unavailable after %d failures", self.failure_count)

    def check_recovery(self) -> None:
        if not self.available and time.time() - self.last_failure_ts > self.cooldown_seconds:
            self.available = True
            self.failure_count = 0
            logger.info("Provider recovered after cooldown")


_provider_status: dict[Provider, ProviderStatus] = {
    Provider.NVIDIA:    ProviderStatus(),
    Provider.DEEPSEEK:  ProviderStatus(),
    Provider.ANTHROPIC: ProviderStatus(),
    Provider.OPENAI:    ProviderStatus(),
}


def _build_fallback_chain(forced: str) -> list[Provider]:
    if forced != "auto":
        try:
            return [Provider(forced)]
        except ValueError:
            pass
    return [Provider.NVIDIA, Provider.DEEPSEEK, Provider.ANTHROPIC, Provider.OPENAI]


async def _call_openai_compat(
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict],
    max_tokens: int,
    temperature: float,
    extra_headers: dict | None = None,
) -> tuple[str, int, int]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        **(extra_headers or {}),
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return content, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


async def _call_anthropic(
    api_key: str,
    messages: list[dict],
    max_tokens: int,
    temperature: float,
) -> tuple[str, int, int]:
    system_msgs = [m["content"] for m in messages if m["role"] == "system"]
    user_msgs = [m for m in messages if m["role"] != "system"]
    payload: dict = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": user_msgs,
    }
    if system_msgs:
        payload["system"] = "\n".join(system_msgs)
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(f"{ANTHROPIC_BASE_URL}/messages", json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
    content = data["content"][0]["text"]
    usage = data.get("usage", {})
    return content, usage.get("input_tokens", 0), usage.get("output_tokens", 0)


async def chat(
    messages: list[dict],
    max_tokens: int = 2048,
    temperature: float = 0.7,
) -> LLMResponse:
    """
    Envía un chat completion con fallback automático entre proveedores.
    messages: lista de dicts {"role": "system"|"user"|"assistant", "content": str}
    """
    settings = get_settings()
    chain = _build_fallback_chain(settings.llm_provider)

    for provider in chain:
        status = _provider_status[provider]
        status.check_recovery()
        if not status.available:
            logger.info("Skipping %s — in cooldown", provider)
            continue

        t0 = time.monotonic()
        try:
            if provider == Provider.NVIDIA:
                if not settings.nvidia_api_key:
                    continue
                content, in_tok, out_tok = await _call_openai_compat(
                    NVIDIA_BASE_URL, settings.nvidia_api_key, NVIDIA_MODEL,
                    messages, max_tokens, temperature,
                )

            elif provider == Provider.DEEPSEEK:
                if not settings.deepseek_api_key:
                    continue
                content, in_tok, out_tok = await _call_openai_compat(
                    DEEPSEEK_BASE_URL, settings.deepseek_api_key, DEEPSEEK_MODEL,
                    messages, max_tokens, temperature,
                )

            elif provider == Provider.ANTHROPIC:
                if not settings.anthropic_api_key:
                    continue
                content, in_tok, out_tok = await _call_anthropic(
                    settings.anthropic_api_key, messages, max_tokens, temperature,
                )

            else:  # OPENAI
                if not settings.openai_api_key:
                    continue
                content, in_tok, out_tok = await _call_openai_compat(
                    OPENAI_BASE_URL, settings.openai_api_key, OPENAI_MODEL,
                    messages, max_tokens, temperature,
                )

            latency = int((time.monotonic() - t0) * 1000)
            status.failure_count = 0
            status.available = True

            model_name = {
                Provider.NVIDIA:    NVIDIA_MODEL,
                Provider.DEEPSEEK:  DEEPSEEK_MODEL,
                Provider.ANTHROPIC: ANTHROPIC_MODEL,
                Provider.OPENAI:    OPENAI_MODEL,
            }[provider]

            logger.info("LLM OK provider=%s latency=%dms in=%d out=%d", provider, latency, in_tok, out_tok)
            return LLMResponse(
                content=content,
                provider=provider,
                model=model_name,
                input_tokens=in_tok,
                output_tokens=out_tok,
                latency_ms=latency,
            )

        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            logger.warning("LLM %s HTTP %d — trying next provider", provider, code)
            if code in (429, 503, 529):
                status.mark_failure()
            elif code == 401:
                status.available = False
                logger.error("LLM %s invalid API key — disabled", provider)
            else:
                status.mark_failure()

        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.warning("LLM %s network error: %s", provider, exc)
            status.mark_failure()

        except Exception as exc:
            logger.error("LLM %s unexpected error: %s", provider, exc)
            status.mark_failure()

    raise RuntimeError("All LLM providers failed or unconfigured.")


async def chat_simple(prompt: str, system: str = "", max_tokens: int = 2048) -> str:
    """Wrapper de conveniencia para prompt único."""
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    response = await chat(messages, max_tokens=max_tokens)
    return response.content


def get_provider_health() -> dict:
    """Estado actual de cada proveedor — para el endpoint /health."""
    return {
        p.value: {
            "available": s.available,
            "failure_count": s.failure_count,
        }
        for p, s in _provider_status.items()
    }
