"""
Registra en Firestore cada switch de proveedor LLM y envía alertas por email.
Se engancha al llm_client mediante un middleware de logging.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from app.ai.llm_client import LLMResponse, Provider, chat as _base_chat, get_provider_health
from app.core.config import get_settings

logger = logging.getLogger(__name__)

_last_provider: Provider | None = None
_switch_callbacks: list = []


def on_provider_switch(callback) -> None:
    """Registra un callback async(from_provider, to_provider) para notificaciones externas."""
    _switch_callbacks.append(callback)


async def _log_to_firestore(event: dict) -> None:
    try:
        from google.cloud import firestore as gfs
        settings = get_settings()
        db = gfs.AsyncClient(project=settings.firebase_project_id)
        await db.collection("llm_events").add(event)
    except Exception as exc:
        logger.warning("Could not write LLM event to Firestore: %s", exc)


async def _send_email_alert(from_provider: Provider, to_provider: Provider) -> None:
    settings = get_settings()
    alert_email = getattr(settings, "alert_email", "")
    if not alert_email:
        return
    try:
        import httpx
        # SendGrid simple mail send
        sendgrid_key = getattr(settings, "sendgrid_api_key", "")
        if not sendgrid_key:
            logger.info("No SENDGRID_API_KEY — skipping email alert")
            return
        payload = {
            "personalizations": [{"to": [{"email": alert_email}]}],
            "from": {"email": "noreply@agenthub.co"},
            "subject": f"[AgentHub] LLM Switch: {from_provider} → {to_provider}",
            "content": [{
                "type": "text/plain",
                "value": (
                    f"El sistema cambió automáticamente de proveedor LLM.\n\n"
                    f"De: {from_provider.value}\n"
                    f"A:  {to_provider.value}\n"
                    f"Hora: {datetime.now(timezone.utc).isoformat()}\n\n"
                    f"Revisa el dashboard de salud en /health/llm"
                ),
            }],
        }
        async with httpx.AsyncClient() as client:
            r = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers={"Authorization": f"Bearer {sendgrid_key}"},
                timeout=10.0,
            )
            r.raise_for_status()
        logger.info("Alert email sent to %s", alert_email)
    except Exception as exc:
        logger.warning("Failed to send alert email: %s", exc)


async def chat(messages: list[dict], max_tokens: int = 2048, temperature: float = 0.7) -> LLMResponse:
    """
    Wrapper sobre llm_client.chat que detecta switches de proveedor
    y dispara logging + alertas.
    """
    global _last_provider

    response = await _base_chat(messages, max_tokens=max_tokens, temperature=temperature)
    current = response.provider

    if _last_provider is not None and _last_provider != current:
        logger.warning("LLM PROVIDER SWITCH: %s → %s", _last_provider, current)

        event = {
            "type": "provider_switch",
            "from": _last_provider.value,
            "to": current.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health": get_provider_health(),
        }

        asyncio.create_task(_log_to_firestore(event))
        asyncio.create_task(_send_email_alert(_last_provider, current))

        for cb in _switch_callbacks:
            try:
                asyncio.create_task(cb(_last_provider, current))
            except Exception:
                pass

    _last_provider = current
    return response


async def chat_simple(prompt: str, system: str = "", max_tokens: int = 2048) -> str:
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    response = await chat(messages, max_tokens=max_tokens)
    return response.content
