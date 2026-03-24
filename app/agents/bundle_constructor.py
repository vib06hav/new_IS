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
                "overall_max": entry.get("max_score_raw"),
                "grading_mode": entry.get("grading_mode"),
            }
            subjects = []
            for sub in entry.get("subject_entries", []) or []:
                score = safe_float(sub.get("score_raw"))
                mx = safe_float(sub.get("max_score_raw")) or 100.0
                subject_name = clean_text(sub.get("subject_name"))
                if score is None or not subject_name:
                    continue
                subjects.append((score, subject_name, mx))
            if subjects:
                high_score, high_subject, high_max = max(subjects, key=lambda item: (item[0]/item[2])*100)
                low_score, low_subject, low_max = min(subjects, key=lambda item: (item[0]/item[2])*100)
                content["subject_summary"] = {
                    "highest_subject": high_subject,
                    "highest_score": f"{high_score:.1f}/{high_max:.0f}",
                    "lowest_subject": low_subject,
                    "lowest_score": f"{low_score:.1f}/{low_max:.0f}"
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
                "text_excerpt": truncate_text(entry.get("raw_text"), max_words=300)
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
    collection_cursors = {}
    for mapping in entity_id_map:
        eid = mapping.get("entity_id")
        coll = mapping.get("collection")
        entries = canonical.get(coll, [])
        idx = collection_cursors.get(coll, 0)
        if idx < len(entries):
            entry = entries[idx]
            entity_cache[eid] = {
                "entity_id": eid,
                "collection": coll,
                "content": compact_content(entry, coll) if compact_mode else clean_entry(entry, coll)
            }
        collection_cursors[coll] = idx + 1

    # Build Signal-Evidence pairs
    signal_evidence_pairs = []
    already_included_entity_ids = set()
    for sig in validated_signals:
        evidence_list = []
        for eid in sig.get("referenced_entity_ids", []):
            if eid in entity_cache:
                if eid in already_included_entity_ids:
                    # Include lightweight reference for subsequent occurrences
                    cache_item = entity_cache[eid]
                    evidence_list.append({
                        "entity_id": eid,
                        "collection": cache_item["collection"],
                        "content_ref": "see_prior_signal"
                    })
                else:
                    # First occurrence gets full content
                    evidence_list.append(entity_cache[eid])
                    already_included_entity_ids.add(eid)
        
        signal_evidence_pairs.append({
            "signal": {
                "signal_id": sig.get("signal_id"),
                "title": sig.get("title"),
                "essay_claim": sig.get("essay_claim"),
                "evidence_observation": sig.get("evidence_observation"),
                "tension_or_coherence": sig.get("tension_or_coherence"),
                "interview_hook": sig.get("interview_hook"),
                "referenced_entity_ids": sig.get("referenced_entity_ids")
            },
            "evidence": evidence_list
        })

    app_id = canonical.get("identifiers", {}).get("application_id", "UNKNOWN")

    return {
        "application_id": app_id,
        "signal_evidence_pairs": signal_evidence_pairs
    }
