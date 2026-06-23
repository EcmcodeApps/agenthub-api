"""
Servicio de misiones: crea, actualiza y orquesta la ejecución de misiones.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from app.schemas.mission import MissionCreate, MissionResponse, MissionStatus
from app.schemas.agent import AgentSuggestion, AgentResponse
from app.ai.agents.agent_generator import generate_agent_team
from app.core.config import get_settings

# Almacenamiento en memoria para modo mock (reemplazar con Firestore en producción)
_missions_store: dict = {}
_agents_store: dict = {}


def create_mission(data: MissionCreate, user: dict) -> MissionResponse:
    mission_id = f"mission_{uuid.uuid4().hex[:12]}"
    org_id = user.get("organizationId", f"org_{user['uid']}")

    mission = {
        "id": mission_id,
        "organizationId": org_id,
        "userId": user["uid"],
        "title": data.title,
        "industryId": data.industryId,
        "objective": data.objective,
        "context": data.context,
        "expectedOutput": data.expectedOutput,
        "depth": data.depth.value,
        "budgetMode": data.budgetMode.value,
        "status": MissionStatus.draft.value,
        "selectedDocumentIds": data.selectedDocumentIds,
        "createdAt": datetime.utcnow().isoformat(),
    }
    _missions_store[mission_id] = mission
    return MissionResponse(**mission)


def get_mission(mission_id: str, user: dict) -> Optional[MissionResponse]:
    mission = _missions_store.get(mission_id)
    if not mission:
        return None
    org_id = user.get("organizationId", f"org_{user['uid']}")
    if mission["organizationId"] != org_id:
        return None
    return MissionResponse(**mission)


def list_missions(user: dict) -> List[MissionResponse]:
    org_id = user.get("organizationId", f"org_{user['uid']}")
    return [
        MissionResponse(**m)
        for m in _missions_store.values()
        if m["organizationId"] == org_id
    ]


def generate_agents_for_mission(mission_id: str, user: dict) -> List[AgentResponse]:
    mission = _missions_store.get(mission_id)
    if not mission:
        return []

    suggestions = generate_agent_team(
        industry=mission["industryId"],
        objective=mission["objective"],
        depth=mission["depth"],
    )

    agents = []
    for s in suggestions:
        agent_id = f"agent_{uuid.uuid4().hex[:10]}"
        agent = {
            "id": agent_id,
            "missionId": mission_id,
            "name": s.name,
            "role": s.role,
            "goal": s.goal,
            "tools": s.tools,
            "modelRecommendation": s.modelRecommendation,
            "prompt": s.prompt,
            "status": "pending",
            "order": s.order,
            "outputType": s.outputType,
        }
        _agents_store[agent_id] = agent
        agents.append(AgentResponse(**agent))

    # Actualizar estado de la misión
    mission["status"] = MissionStatus.agents_generated.value
    _missions_store[mission_id] = mission

    return agents


def get_agents_for_mission(mission_id: str) -> List[AgentResponse]:
    return [
        AgentResponse(**a)
        for a in _agents_store.values()
        if a["missionId"] == mission_id
    ]


def approve_agents(mission_id: str, user: dict) -> bool:
    mission = _missions_store.get(mission_id)
    if not mission:
        return False
    mission["status"] = MissionStatus.waiting_approval.value
    _missions_store[mission_id] = mission

    # Aprobar todos los agentes pendientes
    for agent in _agents_store.values():
        if agent["missionId"] == mission_id and agent["status"] == "pending":
            agent["status"] = "approved"
    return True
