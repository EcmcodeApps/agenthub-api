from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.services.email_service import send_team_invitation

router = APIRouter(prefix="/team", tags=["team"])


class InviteRequest(BaseModel):
    to_email: EmailStr
    inviter_name: str
    org_name: str
    role: str
    app_url: str = "https://app.agenthub.co"


@router.post("/invite")
async def invite_member(body: InviteRequest):
    invite_link = f"{body.app_url}/registro?invite={body.to_email}"
    ok = await send_team_invitation(
        to_email=body.to_email,
        inviter_name=body.inviter_name,
        org_name=body.org_name,
        role=body.role,
        invite_link=invite_link,
    )
    if not ok:
        raise HTTPException(status_code=500, detail="No se pudo enviar el correo")
    return {"sent": True, "to": body.to_email}
