from fastapi import APIRouter, Depends
from app.core.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "uid": user.get("uid"),
        "email": user.get("email"),
        "name": user.get("name"),
        "organizationId": user.get("organizationId"),
    }
