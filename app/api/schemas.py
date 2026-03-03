from typing import Dict, Any, Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class SynthesisOutput(BaseModel):
    snapshot: str
    discussion_focus_areas: str
    suggested_questions: str

class ApplicationResponse(BaseModel):
    id: UUID
    status: str
    confidence_score: Optional[float] = None
    created_at: datetime
    synthesis: Optional[SynthesisOutput] = None
    
    class Config:
        from_attributes = True

class ApplicationsListResponse(BaseModel):
    applications: list[ApplicationResponse]
