from __future__ import annotations

import os


def is_twilio_configured() -> bool:
    return all([
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_API_KEY"),
        os.getenv("TWILIO_API_SECRET"),
    ])


def is_azure_openai_configured() -> bool:
    enabled = (os.getenv("AI_FEATURES_ENABLED") or "").lower() in ("1", "true", "yes", "on")
    if not enabled:
        return False
    return all([
        os.getenv("AZURE_OPENAI_ENDPOINT"),
        os.getenv("AZURE_OPENAI_API_KEY"),
        os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT"),
    ])


def object_store_provider() -> str:
    return (os.getenv("OBJECT_STORE_PROVIDER") or "local").strip().lower()

