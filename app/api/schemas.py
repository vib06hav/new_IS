from typing import Dict, Any, Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class Theme(BaseModel):
    theme_id: str
    title: str
    description: str
    referenced_entity_ids: list[str]

class QuestionGroup(BaseModel):
    theme_id: str
    group_title: str
    questions: list[str]

class Page4FocusThemes(BaseModel):
    themes: list[Theme]

class Page5QuestionGroups(BaseModel):
    question_groups: list[QuestionGroup]

class SynthesisOutput(BaseModel):
    report_metadata: Dict[str, Any]
    page_1_background_profile: Dict[str, Any]
    page_2_academic_and_engagement: Dict[str, Any]
    page_3_essays: Dict[str, Any]
    page_4_focus_themes: Page4FocusThemes
    page_5_question_groups: Page5QuestionGroups

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
