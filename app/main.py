from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_auth import router as auth_router
from app.api.routes_missions import router as missions_router
from app.api.routes_team import router as team_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="AgentHub Empresarial API",
    description="Backend para la plataforma SaaS de agentes IA empresariales",
    version="0.1.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://agenthub-web.vercel.app",
        "https://agenthub-web-git-master-edwins-projects-887d45f9.vercel.app",
        "*",  # temporal hasta tener dominio propio
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(missions_router)
app.include_router(team_router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "environment": settings.environment,
        "mock_mode": settings.mock_ai_mode,
    }


@app.get("/health/llm")
async def health_llm():
    from app.ai.llm_client import get_provider_health
    return {
        "active_provider": settings.llm_provider,
        "providers": get_provider_health(),
    }


@app.post("/dev/llm/test")
async def test_llm(body: dict):
    """Endpoint de prueba — solo disponible en development."""
    if settings.environment != "development":
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
    from app.ai.llm_monitor import chat_simple
    prompt = body.get("prompt", "Di 'hola' en español.")
    result = await chat_simple(prompt)
    return {"response": result}
