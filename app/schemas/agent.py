from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class AgentStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    running = "running"
    completed = "completed"


class AgentSuggestion(BaseModel):
    name: str
    role: str
    goal: str
    tools: List[str]
    modelRecommendation: str
    prompt: str
    order: int
    outputType: str


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    goal: Optional[str] = None
    status: Optional[AgentStatus] = None


class AgentResponse(BaseModel):
    id: str
    missionId: str
    name: str
    role: str
    goal: str
    tools: List[str]
    modelRecommendation: str
    prompt: str
    status: str
    order: int
    outputType: str
