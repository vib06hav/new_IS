import re

from app.config import settings

def construct_bundle(validated_signals: list, canonical: dict, entity_id_map: list) -> dict:
    """
    Agent 15: Signal–evidence bundle constructor.
    Pairs validated interpreted signals with their canonical evidence.
    Includes only non-null relevant fields, omitting internal metadata or artifacts.
    """

    compact_mode = settings.LLM_PAYLOAD_MODE == "compact"

    def is_artifact(text, is_duration=False, is_position=False):
        if not text: return True
        s_text = str(text).strip()
        if not s_text: return True
        if is_duration:
            try:
                float(re.findall(r"\d+\.?\d*", s_text)[0])
                return False
            except (ValueError, IndexError):
                return True
        blocklist = ["Organization", "Reference", "Position", "Role", "Title", "Name", "Duration", "Level"]
        if not is_position and s_text in blocklist:
            return True
        labels = ["Mobile Number", "Email Address", "Date of Birth"]
        if any(label.lower() in s_text.lower() for label in labels):
            return True
        if "?" in s_text:
            return True
        return False

    def clean_text(value):
        if value is None:
            return None
        cleaned = re.sub(r"\s+", " ", str(value)).strip()
        return cleaned or None

    def truncate_text(value, max_words=40):
        cleaned = clean_text(value)
        if not cleaned:
            return None
        words = cleaned.split()
        if len(words) <= max_words:
            return cleaned
        return " ".join(words[:max_words]) + "..."

    def safe_float(value):
        if value is None:
            return None
        match = re.search(r"-?\d+\.?\d*", str(value))
        if not match:
            return None
        try:
            return float(match.group(0))
        except ValueError:
            return None

    def compact_content(entry, collection):
        if collection == "activity_entries":
            parts = []
            for value in [
                clean_text(entry.get("activity_name")),
                clean_text(entry.get("position_title")),
                clean_text(entry.get("activity_type")),
            ]:
                if value and value not in parts:
                    parts.append(value)
            duration = clean_text(entry.get("duration"))
            if duration and not is_artifact(duration, is_duration=True):
                parts.append(f"duration {duration}")
            level = clean_text(entry.get("level"))
            if level:
                parts.append(level)
            detail = (
                truncate_text(entry.get("achievement"), max_words=16)
                or truncate_text(entry.get("roles_and_responsibilities"), max_words=16)
                or truncate_text(entry.get("description_raw"), max_words=16)
            )
            if detail:
                parts.append(detail)
            return {"summary": "; ".join(parts)} if parts else {}

        if collection == "academic_entries":
            content = {
                "academic_level": entry.get("academic_level"),
                "academic_year": entry.get("academic_year"),
                "overall_score": entry.get("score_raw"),
                "grading_mode": entry.get("grading_mode"),
            }
            subjects = []
            for sub in entry.get("subject_entries", []) or []:
                score = safe_float(sub.get("score_raw"))
                subject_name = clean_text(sub.get("subject_name"))
                if score is None or not subject_name:
                    continue
                subjects.append((score, subject_name))
            if subjects:
                high_score, high_subject = max(subjects, key=lambda item: item[0])
                low_score, low_subject = min(subjects, key=lambda item: item[0])
                content["subject_summary"] = {
                    "highest_subject": high_subject,
                    "highest_score": f"{high_score:.2f}".rstrip("0").rstrip("."),
                    "lowest_subject": low_subject,
                    "lowest_score": f"{low_score:.2f}".rstrip("0").rstrip(".")
                }
            return {k: v for k, v in content.items() if v is not None}

        if collection == "test_entries":
            content = {
                "test_name": entry.get("test_name"),
                "total_score": entry.get("total_score"),
                "percentile": entry.get("percentile"),
                "rank": entry.get("rank"),
            }
            sections = []
            scores = []
            for section in entry.get("sectional_scores", []) or []:
                score = safe_float(section.get("raw_score"))
                label = clean_text(section.get("label"))
                if score is None or not label:
                    continue
                scores.append((score, label))
            if scores:
                highest = max(score for score, _ in scores)
                lowest, lowest_label = min(scores, key=lambda item: item[0])
                if highest - lowest >= 8:
                    sections.append({"label": lowest_label, "score": f"{lowest:.2f}".rstrip("0").rstrip(".")})
            if sections:
                content["sections"] = sections
            return {k: v for k, v in content.items() if v is not None}

        if collection == "essay_entries":
            content = {
                "essay_identifier": entry.get("essay_identifier"),
                "text_excerpt": truncate_text(entry.get("raw_text"), max_words=120)
            }
            return {k: v for k, v in content.items() if v is not None}

        return clean_entry(entry, collection)

    def clean_entry(entry, collection):
        """Applies field hygiene and null omission to a canonical entry."""
        metadata_keys = {
            "entry_id", "confidence_score", "placeholder_flag", 
            "short_response_flag", "result_status", "extraction_confidence", 
            "marking_scheme_raw", "test_date"
        }
        
        cleaned = {}
        for k, v in entry.items():
            if k in metadata_keys or v is None:
                continue
            
            # Handle specific collection rules and artifact filtering
            if collection == "activity_entries":
                if k == "duration" and is_artifact(v, is_duration=True):
                    continue
                if k == "position_title" and is_artifact(v, is_position=True):
                    continue
                if k in ["activity_name", "roles_and_responsibilities"] and is_artifact(v):
                    continue
            
            # Recursive clean for nested objects/lists
            if isinstance(v, dict):
                nested = {nk: nv for nk, nv in v.items() if nk not in metadata_keys and nv is not None}
                if nested: cleaned[k] = nested
            elif isinstance(v, list):
                nested_list = []
                for item in v:
                    if isinstance(item, dict):
                        ni = {nk: nv for nk, nv in item.items() if nk not in metadata_keys and nv is not None}
                        if ni: nested_list.append(ni)
                    else:
                        nested_list.append(item)
                if nested_list: cleaned[k] = nested_list
            else:
                cleaned[k] = v
        return cleaned

    # Map entity_id to its canonical entry for fast lookup
    entity_cache = {}
    for mapping in entity_id_map:
        eid = mapping.get("entity_id")
        coll = mapping.get("collection")
        desc = mapping.get("descriptor")
        
        # Find the entry in the canonical collection
        entries = canonical.get(coll, [])
        for entry in entries:
            # Match descriptor based on collection type logic from projection builder
            match = False
            if coll == "academic_entries":
                match = entry.get("academic_level") == desc
            elif coll == "test_entries":
                match = entry.get("test_name") == desc
            elif coll == "essay_entries":
                match = entry.get("essay_identifier") == desc
            elif coll == "activity_entries":
                match = (entry.get("activity_name") or entry.get("activity_type")) == desc
            
            if match:
                entity_cache[eid] = {
                    "entity_id": eid,
                    "collection": coll,
                    "content": compact_content(entry, coll) if compact_mode else clean_entry(entry, coll)
                }
                break

    # Build Signal-Evidence pairs
    signal_evidence_pairs = []
    for sig in validated_signals:
        evidence_list = []
        for eid in sig.get("referenced_entity_ids", []):
            if eid in entity_cache:
                evidence_list.append(entity_cache[eid])
        
        signal_evidence_pairs.append({
            "signal": {
                "signal_id": sig.get("signal_id"),
                "title": sig.get("title"),
                "description": sig.get("description"),
                "referenced_entity_ids": sig.get("referenced_entity_ids")
            },
            "evidence": evidence_list
        })

    app_id = canonical.get("identifiers", {}).get("application_id", "UNKNOWN")

    return {
        "application_id": app_id,
        "signal_evidence_pairs": signal_evidence_pairs
    }
