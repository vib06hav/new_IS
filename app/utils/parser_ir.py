from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class LayoutBlockIR:
    page: int
    text: str
    clean_text: str
    first_line: str
    line_count: int
    char_count: int
    is_all_caps: bool
    bbox: Any
    x0: float
    y0: float
    x1: float
    y1: float
    center_y: float


@dataclass
class LayoutRowIR:
    row_index: int
    page: int
    blocks: List[Dict[str, Any]]
    text: str
    x_span: List[float]
    y_span: List[float]
    is_sparse: bool
    candidate_header_score: float
    table_context_id: Optional[str]


@dataclass
class ParserIssueIR:
    issue_type: str
    severity: str
    source_stage: str
    page: Optional[int]
    message: str


@dataclass
class SectionSpanIR:
    label: str
    normalized_label: str
    section_type: Optional[str]
    page_start: Optional[int]
    page_end: Optional[int]
    start_row_index: Optional[int]
    end_row_index: Optional[int]
    confidence_score: float


def serialize_ir_list(items: List[Any]) -> List[Dict[str, Any]]:
    return [asdict(item) for item in items]
