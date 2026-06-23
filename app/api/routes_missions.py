from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.schemas.mission import MissionCreate, MissionResponse
from app.schemas.agent import AgentResponse
from app.services.mission_service import (
    create_mission,
    get_mission,
    list_missions,
    generate_agents_for_mission,
    get_agents_for_mission,
    approve_agents,
)
from app.core.security import get_current_user

router = APIRouter(prefix="/missions", tags=["Misiones"])


@router.post("", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
async def create(data: MissionCreate, user: dict = Depends(get_current_user)):
    return create_mission(data, user)


@router.get("", response_model=List[MissionResponse])
async def list_all(user: dict = Depends(get_current_user)):
    return list_missions(user)


@router.get("/{mission_id}", response_model=MissionResponse)
async def get_one(mission_id: str, user: dict = Depends(get_current_user)):
    mission = get_mission(mission_id, user)
    if not mission:
        raise HTTPException(status_code=404, detail="Misión no encontrada")
    return mission


@router.post("/{mission_id}/generate-agents", response_model=List[AgentResponse])
async def generate_agents(mission_id: str, user: dict = Depends(get_current_user)):
    agents = generate_agents_for_mission(mission_id, user)
    if not agents:
        raise HTTPException(status_code=404, detail="Misión no encontrada")
    return agents


@router.get("/{mission_id}/agents", response_model=List[AgentResponse])
async def get_agents(mission_id: str, user: dict = Depends(get_current_user)):
    return get_agents_for_mission(mission_id)


@router.post("/{mission_id}/approve-agents")
async def approve(mission_id: str, user: dict = Depends(get_current_user)):
    ok = approve_agents(mission_id, user)
    if not ok:
        raise HTTPException(status_code=404, detail="Misión no encontrada")
    return {"message": "Agentes aprobados. Misión lista para ejecutar."}
