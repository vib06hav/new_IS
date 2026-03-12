from typing import List, Dict, Any
import uuid
import re


def extract_academic_records(section_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract academic records using precise spatial layout blocks.
    Clusters blocks into horizontal rows by Y-coordinate, then uses a
    state-machine approach:
      1. Detect metadata header row (School Name | Board | Year | ...)
      2. Detect the level+data row (12th | SGGS... | CBSE... | 2024 | ...)
      3. Detect subject table header, then read subject data rows
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
            if cur_y is None or abs(cy - cur_y) < 10:
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

    def _texts(row):
        return [b["text"].strip().replace("\n", " ") for b in row]

    # ─── Known column headers ───
    HEADER_LABELS = {
        "school name", "institute name", "board", "year of passing", "marking scheme",
        "obtained percentage/cgp a", "obtained percentage/cgpa",
        "predicted marks/grades", "result status",
    }

    LEVEL_RE = re.compile(
        r'\b(9th|10th|11th|12th|class\s*9|class\s*10|class\s*11|class\s*12)\b',
        re.IGNORECASE
    )

    current_entry = None
    in_subject_table = False
    # Ordered column names from the most recent header row (excluding the implicit Level column)
    header_columns = []

    for row in all_rows:
        texts = _texts(row)
        text_full = " ".join(texts)
        lower_full = text_full.lower()

        # ── Skip noise rows ──
        if "do you have" in lower_full or "gap after" in lower_full:
            continue
        if "upload" in lower_full and "transcript" in lower_full:
            continue
        if lower_full.startswith("country:") or lower_full.startswith("state:"):
            continue
        # Skip personal info labels that appear in the full block list
        if any(kw in lower_full for kw in [
            "highest degree", "field of employment", "educational institute",
            "father details", "mother details", "sibling details",
            "address details", "communication address", "permanent address",
            "additional information", "preferred major", "positions of",
            "date of birth", "mobile number", "email address",
            "nationality", "first generation", "full name",
            "subject category",
        ]):
            continue

        # ── A. Metadata header row? ──
        lower_cells = {t.lower() for t in texts}
        header_hits = lower_cells & HEADER_LABELS
        if len(header_hits) >= 3:
            header_columns = [t.lower() for t in texts]
            in_subject_table = False
            continue

        # ── B. Level trigger row (may also contain inline data) ──
        level_match = LEVEL_RE.search(lower_full)
        if level_match:
            # Normalize the level string
            raw_level = level_match.group(1).upper()
            clean_level = re.sub(r'CLASS\s*', '', raw_level).strip() or raw_level

            in_subject_table = False
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
                "predicted_score_raw": None,
                "subject_entries": [],
                "component_tags": [],
                "confidence_score": confidence,
            }

            # The level token occupies cell 0; the rest are data values
            # that correspond to header_columns (which also starts at "School Name")
            # So data_vals[0] → header_columns[0], data_vals[1] → header_columns[1], etc.
            data_vals = texts[1:]  # Skip the level cell
            _apply_header_data(current_entry, header_columns, data_vals)
            continue

        # ── C. Subject table header ──
        if ("subject wise marks" in lower_full
            or ("subject" in lower_full
                and ("maximum" in lower_full or "obtained" in lower_full
                     or "predicted" in lower_full))):
            in_subject_table = True
            continue

        # ── D. Subject data row ──
        if in_subject_table and current_entry and len(texts) >= 2:
            first = texts[0]
            is_serial = bool(re.match(r'^\d+\.?$', first))

            if is_serial and len(texts) >= 3:
                subj_name = texts[1]
                obtained = texts[3] if len(texts) >= 4 else texts[2]
            elif not is_serial and len(texts) >= 2:
                subj_name = texts[0]
                obtained = texts[2] if len(texts) >= 3 else texts[1]
            else:
                # Row doesn't match subject pattern — exit table mode
                in_subject_table = False
                continue

            # Valid subject: must have digits in score and short subject name
            if (len(subj_name) >= 2 and len(subj_name) < 50
                    and any(c.isdigit() for c in obtained)
                    and not any(kw in subj_name.lower() for kw in [
                        "applicant", "date:", "rank", "position", "role",
                        "prefect", "leadership", "cultural",
                    ])):
                current_entry["subject_entries"].append({
                    "subject_name": subj_name,
                    "score_raw": obtained,
                    "predicted_score_raw": None,
                    "component_tag": None,
                })
            else:
                # Failed validation — this isn't a real subject row, exit table
                in_subject_table = False
            continue

        # ── E. Freeform school name extraction ──
        if current_entry and not in_subject_table:
            for cell in texts:
                if not current_entry["school_name"]:
                    m = re.search(
                        r'([A-Z][A-Za-z\s]+(?:School|College|Institute|Academy|University))',
                        cell,
                    )
                    if m:
                        current_entry["school_name"] = m.group(1).strip()

    # Flush last entry
    if current_entry:
        entries.append(current_entry)

    # ── Deduplicate: merge entries with the same level ──
    merged = {}
    for e in entries:
        lvl = e["academic_level"]
        if lvl in merged:
            existing = merged[lvl]
            for key in ["school_name", "board_name", "academic_year",
                         "marking_scheme_raw", "score_raw", "predicted_score_raw"]:
                if not existing.get(key) and e.get(key):
                    existing[key] = e[key]
            if e.get("grading_mode") != "unknown":
                existing["grading_mode"] = e["grading_mode"]
            if e.get("subject_entries"):
                existing["subject_entries"].extend(e["subject_entries"])
        else:
            merged[lvl] = e

    final_entries = list(merged.values())

    # Map academic entries to schooling history (Page 1 summary)
    for ent in final_entries:
        schooling_history.append({
            "entry_id": uuid.uuid4(),
            "level": ent["academic_level"],
            "school_name": ent.get("school_name"),
            "board_name": ent.get("board_name"),
            "location": None,  # Optional: could parse from noise rows if available
            "confidence_score": ent.get("confidence_score", 0.9)
        })

    return {
        "academic_entries": final_entries,
        "schooling_history": schooling_history,
        "confidence_score": confidence,
    }


def _apply_header_data(entry: dict, header_columns: list, data_vals: list):
    """Map data values to the entry dict using the header column labels."""
    for idx, hdr in enumerate(header_columns):
        val = data_vals[idx] if idx < len(data_vals) else None
        if not val:
            continue
        if "school" in hdr or "institute" in hdr:
            entry["school_name"] = val
        elif hdr == "board":
            entry["board_name"] = val
        elif "year" in hdr:
            entry["academic_year"] = val
        elif "marking" in hdr:
            entry["marking_scheme_raw"] = val
            entry["grading_mode"] = (
                "percentage" if "percent" in val.lower()
                else "cgpa" if "cgpa" in val.lower()
                else "unknown"
            )
        elif "percentage" in hdr or "cgpa" in hdr:
            entry["score_raw"] = val
        elif "predicted" in hdr:
            entry["predicted_score_raw"] = val
        elif "result" in hdr:
            entry.setdefault("result_status", val)
