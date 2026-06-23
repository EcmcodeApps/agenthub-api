from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    environment: str = "development"
    secret_key: str = "change-this-in-production"
    mock_ai_mode: bool = True

    # Firebase
    firebase_project_id: str = ""
    firebase_private_key: str = ""
    firebase_client_email: str = ""

    # Proveedores IA (solo backend)
    deepseek_api_key: str = ""
    mistral_api_key: str = ""
    grok_api_key: str = ""
    tavily_api_key: str = ""

    # LLM routing
    nvidia_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_provider: str = "auto"  # auto | nvidia | anthropic | openai

    # Email
    sendgrid_api_key: str = ""
    email_from: str = "noreply@agenthub.co"
    email_from_name: str = "AgentHub Empresarial"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
