from typing import List, Dict, Any, Optional
import uuid
import re
import logging
from app.utils.form_vocab import ACADEMIC_COLUMN_MAP, is_stop_word

logger = logging.getLogger(__name__)

def extract_academic_records(section_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract academic records using precise spatial layout blocks.
    Clusters blocks into horizontal rows by Y-coordinate, then uses a
    state-machine approach with spatial column mapping for tables.
    """
    entries = []
    schooling_history = []
    confidence = 0.85

    # ─── Step 1: Cluster blocks into horizontal rows ───
    blocks_by_page = {}
    for b in section_blocks:
        blocks_by_page.setdefault(b["page"], []).append(b)

    all_rows = []
    for page in sorted(blocks_by_page.keys()):
        page_blocks = sorted(
            blocks_by_page[page],
            key=lambda b: -(b["bbox"][1] + b["bbox"][3]) / 2,
        )
        rows, cur_row, cur_y = [], [], None
        for b in page_blocks:
            cy = (b["bbox"][1] + b["bbox"][3]) / 2
            # Use 12px cluster threshold
            if cur_y is None or abs(cy - cur_y) < 12:
                cur_row.append(b)
                cur_y = cy if cur_y is None else cur_y
            else:
                rows.append(cur_row)
                cur_row, cur_y = [b], cy
        if cur_row:
            rows.append(cur_row)
        for r in rows:
            r.sort(key=lambda b: b["bbox"][0])
            all_rows.append(r)

    # ─── Known column headers ───
    HEADER_LABELS = set(ACADEMIC_COLUMN_MAP.keys())

    LEVEL_RE = re.compile(
        r'\b(9th|10th|11th|12th|class\s*9|class\s*10|class\s*11|class\s*12)\b',
        re.IGNORECASE
    )

    current_entry = None
    in_subject_table = False
    
    # Header state for Metadata (School, Board, etc.) — maps canonical key to X-anchor
    metadata_column_map = {}
    
    # Header state for Subject Table (Subject, Max, Obtained)
    subject_column_map = {}

    for row_blocks in all_rows:
        texts = [b["text"].strip().replace("\n", " ") for b in row_blocks]
        text_full = " ".join(texts)
        lower_full = text_full.lower()

        # ── Skip noise rows ──
        if any(kw in lower_full for kw in ["do you have", "gap after", "upload transcript", "country:", "state:", "subject category"]):
            continue

        # ── A. Metadata header row? (School Name | Board | ...) ──
        lower_cells = {t.lower().replace("\n", " ") for t in texts}
        header_hits = lower_cells & HEADER_LABELS
        if len(header_hits) >= 2:
            metadata_column_map = {}
            for b in row_blocks:
                hdr_norm = b["text"].lower().strip().replace("\n", " ")
                canonical = ACADEMIC_COLUMN_MAP.get(hdr_norm)
                if canonical:
                    metadata_column_map[canonical] = b["bbox"][0]
            # If it's pure header, skip the rest
            if not LEVEL_RE.search(lower_full) and "subject" not in lower_full:
                continue

        # ── B. Subject Table Header (Detect columns spatially) ──
        # Check this BEFORE level trigger for rows that contain both (Telangana)
        if "subject" in lower_full and ("marks" in lower_full or "grade" in lower_full):
            in_subject_table = True
            subject_column_map = {}
            for b in row_blocks:
                t_norm = b["text"].lower().strip()
                if "subject" == t_norm or "subject name" == t_norm:
                    subject_column_map["subject_name"] = b["bbox"][0]
                elif "maximum" in t_norm:
                    subject_column_map["max_score_raw"] = b["bbox"][0]
                elif "obtained" in t_norm:
                    subject_column_map["score_raw"] = b["bbox"][0]
                elif "predicted" in t_norm:
                    subject_column_map["predicted_score_raw"] = b["bbox"][0]
            # Don't continue yet, might also be a Level Trigger

        # ── C. Level trigger row (trigger new Entry) ──
        level_match = LEVEL_RE.search(lower_full)
        if level_match:
            raw_level = level_match.group(1).upper()
            clean_level = re.sub(r'CLASS\s*', '', raw_level).strip() or raw_level

            # If we already have an active entry for this level, don't restart!
            if current_entry and current_entry["academic_level"] == clean_level:
                # Map inline metadata spatially
                _apply_spatial_metadata(current_entry, metadata_column_map, row_blocks)
                continue

            if "subject" not in lower_full:
                in_subject_table = False
                subject_column_map = {}
            
            if current_entry:
                entries.append(current_entry)

            current_entry = {
                "entry_id": str(uuid.uuid4()),
                "academic_level": clean_level,
                "school_name": None,
                "board_name": None,
                "academic_year": None,
                "marking_scheme_raw": None,
                "grading_mode": "unknown",
                "score_raw": None,
                "max_score_raw": None,
                "predicted_score_raw": None,
                "subject_entries": [],
                "confidence_score": confidence,
            }

            # Map inline metadata spatially
            _apply_spatial_metadata(current_entry, metadata_column_map, row_blocks)
            continue

        # ── D. Subject Table Data (Use Spatial Column Map) ──
        if in_subject_table and current_entry and subject_column_map:
            row_data = {"subject_name": None, "max_score_raw": None, "score_raw": None, "predicted_score_raw": None}
            used_blocks = set()
            for key, anchor_x in subject_column_map.items():
                best_block, min_dist = None, 50
                for i, b in enumerate(row_blocks):
                    if i in used_blocks: continue
                    dist = abs(b["bbox"][0] - anchor_x)
                    if dist < min_dist:
                        min_dist, best_block = dist, (i, b)
                if best_block:
                    idx, b = best_block
                    row_data[key] = b["text"].strip()
                    used_blocks.add(idx)

            subj_name, score = row_data["subject_name"], row_data["score_raw"]
            if subj_name and score and not is_stop_word(subj_name):
                 if any(c.isdigit() for c in score) or len(score) <= 3:
                      current_entry["subject_entries"].append({
                          "subject_name": subj_name,
                          "score_raw": score,
                          "max_score_raw": row_data.get("max_score_raw"),
                          "predicted_score_raw": row_data.get("predicted_score_raw"),
                      })
                      continue
            if not subj_name or len(subj_name) < 2:
                in_subject_table = False

    if current_entry:
        entries.append(current_entry)

    # ── Merge and Deduplicate ──
    merged = {}
    for e in entries:
        lvl = e["academic_level"]
        if lvl in merged:
            existing = merged[lvl]
            for key in ["school_name", "board_name", "academic_year", "marking_scheme_raw", "score_raw", "max_score_raw", "predicted_score_raw"]:
                if not existing.get(key) and e.get(key):
                    existing[key] = e[key]
            if e.get("grading_mode") != "unknown":
                existing["grading_mode"] = e["grading_mode"]
            if e.get("subject_entries"):
                existing["subject_entries"].extend(e["subject_entries"])
        else:
            merged[lvl] = e

    final_entries = list(merged.values())
    for ent in final_entries:
        schooling_history.append({
            "entry_id": str(uuid.uuid4()), "level": ent["academic_level"],
            "school_name": ent.get("school_name"), "board_name": ent.get("board_name"),
            "location": None, "confidence_score": ent.get("confidence_score", 0.9)
        })

    return {"academic_entries": final_entries, "schooling_history": schooling_history, "confidence_score": confidence}

def _apply_spatial_metadata(entry: dict, anchor_map: dict, row_blocks: list):
    """Aligns metadata blocks to anchors using distance-ranked pairing."""
    if not anchor_map: return
    
    # 1. Create candidates for all (key, block_idx) pairs
    candidates = []
    for key, anchor_x in anchor_map.items():
        for i, b in enumerate(row_blocks):
            t_cleaned = b["text"].strip().replace("\n", " ")
            if not t_cleaned: continue
            
            # Skip Level Identifiers
            if re.search(r'\b(9th|10th|11th|12th|class)\b', t_cleaned, re.I):
                continue
            # Skip Boilerplate (Labels)
            if is_stop_word(t_cleaned) or (b["bbox"][2] - b["bbox"][0]) > 350:
                continue
                
            dist = abs(b["bbox"][0] - anchor_x)
            if dist < 120:  # Broader threshold for metadata drift
                candidates.append((dist, key, i))
    
    # 2. Sort candidates by distance (best matches first)
    candidates.sort(key=lambda x: x[0])
    
    # 3. Satisfy pairings
    used_keys = set()
    used_indices = set()
    for dist, key, idx in candidates:
        if key not in used_keys and idx not in used_indices:
            val = row_blocks[idx]["text"].strip().replace("\n", " ")
            entry[key] = val
            used_keys.add(key)
            used_indices.add(idx)
            
            if key == "marking_scheme_raw":
                entry["grading_mode"] = "percentage" if "percent" in val.lower() else "cgpa" if "cgpa" in val.lower() else "unknown"

def _apply_header_data(entry: dict, header_columns: list, data_vals: list):
    # LEGACY - removed in Phase 3.0
    pass
