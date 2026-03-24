import re
from typing import List, Dict, Any, Optional
from app.utils.form_vocab import SECTION_HEADERS
from app.utils.parser_ir import SectionSpanIR, serialize_ir_list
from app.utils.text_normalization import normalize_label
from app.utils.section_types import classify_section_label
from app.utils.row_grouper import build_layout_rows

# Build lookup set from centralized registry
KNOWN_SECTIONS = list(SECTION_HEADERS)
NORMALIZED_SECTION_HEADERS = {normalize_label(header): header for header in KNOWN_SECTIONS}
HEADER_KEYWORDS = {
    "details", "information", "activities", "activity", "academic", "academics",
    "test", "tests", "scores", "essay", "essays", "reference", "references",
    "declaration", "disclosure", "consent", "pledge", "address", "language",
    "languages", "leadership", "parent", "father", "mother", "sibling",
    "curricular", "communication", "permanent"
}
NON_HEADER_VALUE_KEYWORDS = {
    "board", "education", "cbse", "score", "percentage", "cgpa", "institute", "school captain",
    "council", "secondary"
}

def detect_sections(blocks: List[Dict[str, Any]], rows: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Groups ordered blocks into labeled sections.
    """
    sections = []
    rows = rows if rows is not None else build_layout_rows(blocks, y_threshold=12)
    current_section = {
        "label": "document_start",
        "normalized_label": normalize_label("document_start"),
        "section_type": classify_section_label("document_start"),
        "page_start": None,
        "page_end": None,
        "start_row_index": None,
        "end_row_index": None,
        "blocks": []
    }
    
    confidence = 0.90
    
    row_index_lookup = {}
    for row in rows:
        for row_block in row["blocks"]:
            row_index_lookup[id(row_block)] = row["row_index"]

    for block in blocks:
        text = block["text"]
        # Fuzzy matching heuristic: short, capitalized strings
        lines = text.split('\n')
        first_line = lines[0].strip()
        normalized_first_line = normalize_label(first_line)
        
        # Heuristic for section header: short text, title case or upper case, potentially matching known headers
        is_header = False
        if len(first_line) < 60:
            # Clean first_line of common prefixes like "1. ", "Activity 1:"
            cleaned_line = re.sub(r'^(?:\d+\.|\w+\s+\d+:?)\s*', '', first_line).strip()
            normalized_cleaned_line = normalize_label(cleaned_line)
            words = [w for w in normalized_cleaned_line.split() if w]
            keyword_overlap = HEADER_KEYWORDS.intersection(words)
            looks_like_value_row = any(term in normalized_cleaned_line for term in NON_HEADER_VALUE_KEYWORDS)
             
            if normalized_cleaned_line and normalized_cleaned_line in NORMALIZED_SECTION_HEADERS:
                is_header = True
            elif (
                first_line.isupper()
                and 1 < len(words) < 8
                and keyword_overlap
                and not looks_like_value_row
                and normalized_first_line not in {"yes", "no", "na"}
            ):
                # Potential unknown section, but only if it still resembles a section title.
                is_header = True
        
        if is_header:
            if current_section["blocks"] or current_section["label"] != "document_start":
                if current_section["blocks"]:
                    current_section["page_start"] = current_section["blocks"][0]["page"]
                    current_section["page_end"] = current_section["blocks"][-1]["page"]
                    row_indexes = [row_index_lookup.get(id(section_block)) for section_block in current_section["blocks"] if row_index_lookup.get(id(section_block)) is not None]
                    if row_indexes:
                        current_section["start_row_index"] = min(
                            [idx for idx in [current_section.get("start_row_index"), *row_indexes] if idx is not None]
                        )
                        current_section["end_row_index"] = max(
                            [idx for idx in [current_section.get("end_row_index"), *row_indexes] if idx is not None]
                        )
                sections.append(current_section)
            current_section = {
                "label": first_line,
                "normalized_label": normalize_label(first_line),
                "section_type": classify_section_label(first_line),
                "page_start": block["page"],
                "page_end": block["page"],
                "start_row_index": row_index_lookup.get(id(block)),
                "end_row_index": row_index_lookup.get(id(block)),
                "blocks": []
            }
            # Add remaining lines of the block if any
            if len(lines) > 1:
                remaining_text = "\n".join(lines[1:]).strip()
                if remaining_text:
                    # Preserve coordinates for the remaining text
                    remainder_block = {
                        "page": block["page"], 
                        "text": remaining_text,
                        "bbox": block["bbox"]
                    }
                    current_section["blocks"].append(remainder_block)
        else:
            current_section["blocks"].append(block)
            if current_section["page_start"] is None:
                current_section["page_start"] = block["page"]
            current_section["page_end"] = block["page"]
            block_row_index = row_index_lookup.get(id(block))
            if block_row_index is not None:
                if current_section["start_row_index"] is None:
                    current_section["start_row_index"] = block_row_index
                current_section["end_row_index"] = block_row_index
            
    if current_section["blocks"] or current_section["label"] != "document_start":
        if current_section["blocks"] and current_section["page_start"] is None:
            current_section["page_start"] = current_section["blocks"][0]["page"]
            current_section["page_end"] = current_section["blocks"][-1]["page"]
        if current_section["blocks"]:
            row_indexes = [row_index_lookup.get(id(section_block)) for section_block in current_section["blocks"] if row_index_lookup.get(id(section_block)) is not None]
            if row_indexes:
                current_section["start_row_index"] = min(
                    [idx for idx in [current_section.get("start_row_index"), *row_indexes] if idx is not None]
                )
                current_section["end_row_index"] = max(
                    [idx for idx in [current_section.get("end_row_index"), *row_indexes] if idx is not None]
                )
        sections.append(current_section)

    section_spans = serialize_ir_list([
        SectionSpanIR(
            label=section["label"],
            normalized_label=section["normalized_label"],
            section_type=section.get("section_type"),
            page_start=section.get("page_start"),
            page_end=section.get("page_end"),
            start_row_index=section.get("start_row_index"),
            end_row_index=section.get("end_row_index"),
            confidence_score=confidence,
        )
        for section in sections
    ])
        
    return {
        "sections": sections,
        "rows": rows,
        "section_spans": section_spans,
        "confidence_score": confidence
    }
