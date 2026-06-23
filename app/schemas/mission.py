from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class MissionDepth(str, Enum):
    fast = "fast"
    balanced = "balanced"
    deep = "deep"


class BudgetMode(str, Enum):
    plan_credits = "plan_credits"
    estimate_first = "estimate_first"
    require_approval = "require_approval"


class MissionStatus(str, Enum):
    draft = "draft"
    agents_generated = "agents_generated"
    waiting_approval = "waiting_approval"
    running = "running"
    processing_documents = "processing_documents"
    researching = "researching"
    writing_report = "writing_report"
    reviewing = "reviewing"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class MissionCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    industryId: str
    objective: str = Field(..., min_length=10)
    context: Optional[str] = None
    expectedOutput: Optional[str] = None
    depth: MissionDepth = MissionDepth.balanced
    budgetMode: BudgetMode = BudgetMode.plan_credits
    selectedDocumentIds: List[str] = []


class MissionResponse(BaseModel):
    id: str
    organizationId: str
    userId: str
    title: str
    industryId: str
    objective: str
    context: Optional[str]
    expectedOutput: Optional[str]
    depth: str
    budgetMode: str
    status: str
    selectedDocumentIds: List[str]
    createdAt: Optional[str] = None
