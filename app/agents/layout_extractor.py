import os
import logging
from typing import List, Dict, Any
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

from app.utils.text_normalization import normalize_pdf_text
from app.utils.parser_ir import LayoutBlockIR, ParserIssueIR, serialize_ir_list
from app.utils.section_types import classify_section_label
from app.utils.row_grouper import build_layout_rows

logger = logging.getLogger(__name__)


def _build_page_stats(blocks: List[Dict[str, Any]], page_count: int) -> List[Dict[str, Any]]:
    page_stats = []
    for page in range(1, page_count + 1):
        page_blocks = [block for block in blocks if block["page"] == page]
        text_char_count = sum(len(block.get("text", "")) for block in page_blocks)
        header_candidates = 0
        for block in page_blocks:
            first_line = str(block.get("text", "")).split("\n", 1)[0].strip()
            if first_line and classify_section_label(first_line):
                header_candidates += 1

        page_stats.append({
            "page": page,
            "block_count": len(page_blocks),
            "text_char_count": text_char_count,
            "header_candidate_count": header_candidates,
            "text_density": round(text_char_count / max(len(page_blocks), 1), 2) if page_blocks else 0.0,
        })
    return page_stats


def _build_layout_issues(blocks: List[Dict[str, Any]], page_count: int) -> List[Dict[str, Any]]:
    issues = []
    if page_count > 0 and not blocks:
        issues.append({
            "issue_type": "missing_text_layer",
            "severity": "high",
            "source_stage": "layout_extraction",
            "page": None,
            "message": "No extractable text blocks were found in the PDF.",
        })
    return issues


def _enrich_block(page: int, text: str, bbox: Any) -> Dict[str, Any]:
    first_line = text.split("\n", 1)[0].strip()
    return {
        "page": page,
        "text": text,
        "clean_text": text.strip(),
        "first_line": first_line,
        "line_count": len([line for line in text.split("\n") if line.strip()]),
        "char_count": len(text),
        "is_all_caps": first_line.isupper(),
        "bbox": bbox,
        "x0": bbox[0],
        "y0": bbox[1],
        "x1": bbox[2],
        "y1": bbox[3],
        "center_y": (bbox[1] + bbox[3]) / 2,
    }


def _build_header_candidates(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidates = []
    for row in rows:
        section_type = classify_section_label(row.get("text", ""))
        if section_type or row.get("candidate_header_score", 0.0) >= 0.5:
            candidates.append({
                "row_index": row["row_index"],
                "page": row["page"],
                "text": row["text"],
                "section_type": section_type,
                "candidate_header_score": row["candidate_header_score"],
            })
    return candidates


def _build_block_ir(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items = [
        LayoutBlockIR(
            page=block["page"],
            text=block["text"],
            clean_text=block["clean_text"],
            first_line=block["first_line"],
            line_count=block["line_count"],
            char_count=block["char_count"],
            is_all_caps=block["is_all_caps"],
            bbox=block["bbox"],
            x0=block["x0"],
            y0=block["y0"],
            x1=block["x1"],
            y1=block["y1"],
            center_y=block["center_y"],
        )
        for block in blocks
    ]
    return serialize_ir_list(items)


def _build_issue_ir(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items = [
        ParserIssueIR(
            issue_type=issue["issue_type"],
            severity=issue["severity"],
            source_stage=issue["source_stage"],
            page=issue.get("page"),
            message=issue["message"],
        )
        for issue in issues
    ]
    return serialize_ir_list(items)

def extract_layout_blocks(pdf_path: str) -> Dict[str, Any]:
    """
    Extracts ordered text blocks from a PDF using pdfminer.six.
    Returns page metadata and blocks.
    """
    if not os.path.exists(pdf_path):
        return {"blocks": [], "page_count": 0, "confidence_score": 0.0, "error": "File not found"}

    blocks = []
    page_count = 0
    confidence = 0.95  # Base confidence for native PDF extraction

    try:
        for page_layout in extract_pages(pdf_path):
            page_count += 1
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text = normalize_pdf_text(element.get_text())
                    if text:
                        blocks.append(_enrich_block(page_count, text, element.bbox))
    except Exception as e:
        return {"blocks": [], "page_count": 0, "confidence_score": 0.0, "error": str(e)}

    # Simple OCR anomaly check: if no text from layout but pages exist
    if page_count > 0 and len(blocks) == 0:
        confidence = 0.1 # Likely a scanned PDF without text layer

    rows = build_layout_rows(blocks, y_threshold=12)
    header_candidates = _build_header_candidates(rows)
    page_stats = _build_page_stats(blocks, page_count)
    issues = _build_layout_issues(blocks, page_count)
        
    raw_text = "\n".join([b["text"] for b in blocks])
    logger.debug("RAW_PDF_TEXT_START")
    logger.debug(raw_text)
    logger.debug("RAW_PDF_TEXT_END")
        
    return {
        "blocks": blocks,
        "page_count": page_count,
        "confidence_score": confidence,
        "rows": rows,
        "header_candidates": header_candidates,
        "page_stats": page_stats,
        "issues": issues,
        "parsed_layout": {
            "blocks": _build_block_ir(blocks),
            "rows": rows,
            "header_candidates": header_candidates,
            "issues": _build_issue_ir(issues),
            "page_stats": page_stats,
        },
    }
