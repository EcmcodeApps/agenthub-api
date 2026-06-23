from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from app.core.config import get_settings
import json

_initialized = False
security = HTTPBearer()


def _init_firebase():
    global _initialized
    if _initialized or firebase_admin._apps:
        _initialized = True
        return
    settings = get_settings()
    if settings.firebase_private_key:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": settings.firebase_project_id,
            "private_key": settings.firebase_private_key.replace("\\n", "\n"),
            "client_email": settings.firebase_client_email,
            "token_uri": "https://oauth2.googleapis.com/token",
        })
        firebase_admin.initialize_app(cred)
    _initialized = True


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict:
    """Verifica el token Firebase y retorna el payload del usuario."""
    _init_firebase()
    token = credentials.credentials
    settings = get_settings()

    # Modo mock para desarrollo sin Firebase configurado
    if settings.mock_ai_mode and not settings.firebase_project_id:
        return {
            "uid": "mock_user_001",
            "email": "demo@agenthub.co",
            "name": "Usuario Demo",
            "organizationId": "org_mock_001",
        }

    try:
        decoded = firebase_auth.verify_id_token(token)
        return decoded
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )
