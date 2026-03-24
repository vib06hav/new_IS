from typing import List, Dict, Any, Optional
import uuid
import re
import math
import logging
from app.utils.grid_detector import get_vertical_lines, get_page_heights
from app.utils.activity_filter import is_valid_activity

logger = logging.getLogger(__name__)

def extract_activities(section_blocks: List[Dict[str, Any]], pdf_path: str = "") -> Dict[str, Any]:
    """
    Extract activities using a Grid-Line based spatial approach with Dynamic Column Mapping.
    Handles isolated headers, cross-page stitching, and horizontal layout shifts.
    """
    all_entries = []
    preferred_major = None
    confidence = 0.90
    if not section_blocks: return {"activity_entries": [], "confidence_score": confidence}

    # 1. Page Heights and Virtual Coordinates
    page_heights = {}
    if pdf_path:
        page_heights = get_page_heights(pdf_path)
    
    cumulative_offsets = {1: 0.0}
    max_page = max(b.get("page", 1) for b in section_blocks)
    for p in range(2, max_page + 1):
        cumulative_offsets[p] = cumulative_offsets[p-1] + page_heights.get(p-1, 842.0)

    for b in section_blocks:
        p = int(b.get("page", 1))
        offset = cumulative_offsets.get(p, 0.0)
        p_height = page_heights.get(p, 842.0)
        # Convert to Top-Down Virtual coordinates
        b["v_y_top"] = offset + (p_height - float(b["bbox"][3]))
        b["v_y_bottom"] = offset + (p_height - float(b["bbox"][1]))
        b["v_y_center"] = (b["v_y_top"] + b["v_y_bottom"]) / 2

    # 2. Cluster rows globally
    sorted_blocks = sorted(section_blocks, key=lambda b: (b["v_y_center"], float(b["bbox"][0])))
    all_rows: List[List[Dict[str, Any]]] = []
    cur_row, cur_v_y = [], None
    for b in sorted_blocks:
        vcy = b["v_y_center"]
        if cur_v_y is None or abs(vcy - cur_v_y) < 8:
            cur_row.append(b)
            cur_v_y = vcy if cur_v_y is None else cur_v_y
        else:
            all_rows.append(cur_row)
            cur_row, cur_v_y = [b], vcy
    if cur_row: all_rows.append(cur_row)

    # 3. Extraction Logic
    SECTION_RE = {
        "extracurricular": re.compile(r'extra\s*-?\s*curricular\s*activities', re.IGNORECASE),
        "co_curricular": re.compile(r'co\s*-?\s*curricular\s*activities', re.IGNORECASE),
        "leadership": re.compile(r'leadership\s*role\s*at\s*school|leadership\s*positions?', re.IGNORECASE)
    }

    # Stopper keywords to identify the end of the activities cluster
    STOPPER_KEYWORDS = [
        "reference 1", "reference- 1", "reference-1", "referees", 
        "reference 2", "declaration", 
        "anything else which you would like", "honour pledge", "admission office"
    ]

    # Keyword mapping for dynamic column header detection
    LABEL_FIELD_MAP = {
        "activity": "activity_name",
        "level": "level",
        "participation": "level",
        "duration": "duration",
        "years": "duration",
        "achievement": "achievement",
        "responsibility": "roles_and_responsibilities",
        "roles": "roles_and_responsibilities",
        "position": "position_title",
        "title": "position_title"
    }

    FIELD_MAPS_FALLBACK = {
        "extracurricular": {1: "activity_name", 2: "level", 3: "duration", 4: "achievement", 5: "achievement"},
        "co_curricular": {1: "activity_name", 2: "level", 3: "duration", 4: "achievement", 5: "achievement"},
        "leadership": {1: "position_title", 2: "duration", 3: "roles_and_responsibilities"}
    }

    current_section: Optional[str] = None
    v_lines: List[float] = []
    v_lines_page = -1
    active_field_map: Dict[int, str] = {}
    
    for row in all_rows:
        row_text = " ".join([str(b.get("text", "")).strip() for b in row]).lower()
        row_page = int(row[0]["page"])
        row_y_top_pdf = float(row[0]["bbox"][3])
        row_y_bottom_pdf = float(row[0]["bbox"][1])
        
        # X. Specific catch for Preferred Major (Additional Information section)
        if "preferred major" in row_text:
            # The value is usually to the right or in the same row
            # Let's try to grab all text in the row excluding the label
            label_match = re.search(r'preferred\s*major', row_text)
            if label_match:
                # Find blocks to the right of the label block
                label_blocks = [b for b in row if "preferred" in b.get("text", "").lower() or "major" in b.get("text", "").lower()]
                if label_blocks:
                    label_x1 = max(b["bbox"][2] for b in label_blocks)
                    val_blocks = [b for b in row if b["bbox"][0] > label_x1 - 5]
                    val_text = " ".join([b["text"].strip() for b in val_blocks if b not in label_blocks]).strip()
                    if val_text:
                        preferred_major = val_text
                        logger.info(f"Extracted Preferred Major: {preferred_major}")
            continue

        # A. Detect Stoppers (ignore if at the very top of a page as header)
        is_top_of_page = row[0]["v_y_top"] - cumulative_offsets.get(row_page, 0) < 60
        if any(stop in row_text for stop in STOPPER_KEYWORDS) and not is_top_of_page:
            current_section = None
            continue

        # B. Detect Section Start/Reset
        found_section = None
        for s_type, pattern in SECTION_RE.items():
            if pattern.search(row_text):
                found_section = s_type
                break
        
        if found_section:
            # Handle continuation headers on new pages
            if found_section == current_section and is_top_of_page:
                continue
            current_section = found_section
            active_field_map = {} # Reset field map for new section or layout
            # Trigger fresh grid detection on the header page
            v_lines = get_vertical_lines(pdf_path, row_page, row_y_bottom_pdf - 300, row_y_top_pdf + 10)
            v_lines_page = row_page
            continue

        if not current_section:
            continue

        # C. Page-Based Grid Maintenance
        if pdf_path and (row_page != v_lines_page or not v_lines):
            # Localized grid search to handle tables spanning multiple pages or multiple tables on one page
            v_lines = get_vertical_lines(pdf_path, row_page, row_y_bottom_pdf - 100, row_y_top_pdf + 100)
            v_lines_page = row_page
            active_field_map = {} # Potential column shift on new page or new table body

        if not v_lines:
            continue

        # D. Dynamic Column Detection (Header Row)
        gaps = [{"x0": v_lines[g], "x1": v_lines[g+1], "center": (v_lines[g] + v_lines[g+1])/2} for g in range(len(v_lines)-1)]
        is_header_row = sum(1 for kw in ["activity", "level", "duration", "achievement", "position", "responsibility", "roles", "years", "participation"] if kw in row_text) >= 2
        
        if is_header_row:
            for b in row:
                bx_center = (float(b["bbox"][0]) + float(b["bbox"][2])) / 2
                txt = b.get("text", "").lower()
                for idx, g in enumerate(gaps):
                    if g["x0"] - 10 <= bx_center <= g["x1"] + 10:
                        for kw, field in LABEL_FIELD_MAP.items():
                            if kw in txt:
                                if idx not in active_field_map or len(kw) > 3:
                                    active_field_map[idx] = field
            continue

        # E. Data Row Processing
        if not active_field_map:
            active_field_map = FIELD_MAPS_FALLBACK.get(current_section, {})

        entry: Dict[str, Any] = {
            "entry_id": str(uuid.uuid4()), "activity_type": current_section,
            "activity_name": None, "position_title": None, "level": None,
            "duration": None, "achievement": None, "roles_and_responsibilities": None,
            "confidence_score": 0.95
        }
        
        row_has_data = False
        for b in row:
            bx_center = (float(b["bbox"][0]) + float(b["bbox"][2])) / 2
            txt = str(b.get("text", "")).strip()
            
            best_idx, min_dist = -1, 9999.0
            for idx, g in enumerate(gaps):
                if g["x0"] - 15 <= bx_center <= g["x1"] + 15:
                    dist = abs(bx_center - g["center"])
                    if dist < min_dist:
                        min_dist = dist
                        best_idx = idx
            
            if best_idx != -1:
                field = active_field_map.get(best_idx)
                if field:
                    if best_idx == 0 and txt.endswith(".") and txt[:-1].isdigit(): continue
                    existing = entry.get(field)
                    entry[field] = f"{existing} {txt}" if existing else txt
                    row_has_data = True
        
        if row_has_data:
            if is_valid_activity(entry):
                all_entries.append(entry)

    return {
        "activity_entries": all_entries,
        "preferred_major": preferred_major,
        "confidence_score": confidence
    }
