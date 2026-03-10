from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID

from app.canonical.version import CANONICAL_VERSION

# --- Family Background ---
class FamilyMember(BaseModel):
    name: Optional[str] = None
    education: Optional[str] = None
    occupation: Optional[str] = None
    organization: Optional[str] = None

class FamilyBackground(BaseModel):
    father: FamilyMember
    mother: FamilyMember

# --- Schooling History ---
class SchoolingHistoryEntry(BaseModel):
    entry_id: UUID
    level: str
    school_name: Optional[str] = None
    board_name: Optional[str] = None
    location: Optional[str] = None
    confidence_score: float

# --- Identifiers ---
class Identifiers(BaseModel):
    application_id: str
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    family_background: Optional[FamilyBackground] = None
    declared_preferences: Dict[str, Any] = Field(default_factory=dict)
    demographic_flags: Dict[str, Any] = Field(default_factory=dict)

# --- Profile Meta ---
class ProfileMeta(BaseModel):
    source_document_page_count: int
    extraction_timestamp: str
    layout_block_count: int
    detected_section_labels: List[str] = Field(default_factory=list)

# --- Academic Entries ---
class SubjectEntry(BaseModel):
    subject_name: str
    score_raw: Optional[str] = None
    predicted_score_raw: Optional[str] = None
    component_tag: Optional[str] = None

class AcademicEntry(BaseModel):
    entry_id: str
    academic_level: str
    school_name: Optional[str] = None
    board_name: Optional[str] = None
    academic_year: Optional[str] = None
    marking_scheme_raw: Optional[str] = None
    grading_mode: str
    score_raw: Optional[str] = None
    predicted_score_raw: Optional[str] = None
    subject_entries: List[SubjectEntry] = Field(default_factory=list)
    component_tags: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)

# --- Test Entries ---
class SectionalScore(BaseModel):
    label: str
    raw_score: str

class TestEntry(BaseModel):
    entry_id: str
    test_name: str
    test_date: Optional[str] = None
    total_score: Optional[str] = None
    sectional_scores: List[SectionalScore] = Field(default_factory=list)
    percentile: Optional[str] = None
    rank: Optional[str] = None
    result_status: str
    confidence_score: float = Field(ge=0.0, le=1.0)

# --- Essay Entries ---
class EssayEntry(BaseModel):
    entry_id: str
    essay_identifier: str
    raw_text: str
    word_count: int
    character_count: int
    placeholder_flag: bool
    duplication_ratio: float = Field(ge=0.0, le=1.0)
    short_response_flag: bool
    confidence_score: float = Field(ge=0.0, le=1.0)

# --- Activity Entries ---
class ActivityEntry(BaseModel):
    entry_id: str
    activity_type: str
    category: Optional[str] = None
    activity_name: Optional[str] = None
    level: Optional[str] = None
    duration: Optional[str] = None
    description_raw: Optional[str] = None
    upload_flag: bool
    confidence_score: float = Field(ge=0.0, le=1.0)

# --- Timeline Entries ---
class TimelineEntry(BaseModel):
    entry_id: str
    year: str
    event_label: str
    source_type: str
    source_reference: str

# --- Cross References ---
class SourceReference(BaseModel):
    source_type: str
    entry_id: str

class EntityTokenMatch(BaseModel):
    entity_token: str
    source_references: List[SourceReference] = Field(default_factory=list)

class CrossReferences(BaseModel):
    entity_map: List[EntityTokenMatch] = Field(default_factory=list)

# --- Integrity Report ---
class Anomaly(BaseModel):
    anomaly_id: str
    anomaly_type: str
    severity_level: str
    source_reference: Optional[str] = None
    description: str

class IntegrityReport(BaseModel):
    anomalies: List[Anomaly] = Field(default_factory=list)

# --- Extraction Confidence ---
class AgentScore(BaseModel):
    agent_id: int
    agent_name: str
    confidence_score: float = Field(ge=0.0, le=1.0)

class ExtractionConfidence(BaseModel):
    agent_scores: List[AgentScore] = Field(default_factory=list)
    aggregate_confidence: float = Field(ge=0.0, le=1.0)

# --- CANONICAL ROOT ---
class CanonicalData(BaseModel):
    canonical_version: str = Field(default=CANONICAL_VERSION)
    identifiers: Identifiers
    profile_meta: ProfileMeta
    academic_entries: List[AcademicEntry] = Field(default_factory=list)
    schooling_history: List[SchoolingHistoryEntry] = Field(default_factory=list)
    test_entries: List[TestEntry] = Field(default_factory=list)
    essay_entries: List[EssayEntry] = Field(default_factory=list)
    activity_entries: List[ActivityEntry] = Field(default_factory=list)
    timeline_entries: List[TimelineEntry] = Field(default_factory=list)
    cross_references: CrossReferences
    integrity_report: IntegrityReport
    extraction_confidence: ExtractionConfidence
