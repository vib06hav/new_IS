import re
from typing import Any

from app.config import settings


def _is_artifact(text: Any, is_duration: bool = False, is_position: bool = False) -> bool:
    if not text:
        return True
    s_text = str(text).strip()
    if not s_text:
        return True
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


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", str(value)).strip()
    return cleaned or None


def _truncate_text(value: Any, max_words: int = 40) -> str | None:
    cleaned = _clean_text(value)
    if not cleaned:
        return None
    words = cleaned.split()
    if len(words) <= max_words:
        return cleaned
    return " ".join(words[:max_words]) + "..."


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    match = re.search(r"-?\d+\.?\d*", str(value))
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _clean_entry(entry: dict[str, Any], collection: str) -> dict[str, Any]:
    metadata_keys = {
        "entry_id", "confidence_score", "placeholder_flag",
        "short_response_flag", "result_status", "extraction_confidence",
        "marking_scheme_raw", "test_date",
    }

    cleaned: dict[str, Any] = {}
    for key, value in entry.items():
        if key in metadata_keys or value is None:
            continue

        if collection == "activity_entries":
            if key == "duration" and _is_artifact(value, is_duration=True):
                continue
            if key == "position_title" and _is_artifact(value, is_position=True):
                continue
            if key in ["activity_name", "roles_and_responsibilities"] and _is_artifact(value):
                continue

        if isinstance(value, dict):
            nested = {nk: nv for nk, nv in value.items() if nk not in metadata_keys and nv is not None}
            if nested:
                cleaned[key] = nested
        elif isinstance(value, list):
            nested_list = []
            for item in value:
                if isinstance(item, dict):
                    nested_item = {nk: nv for nk, nv in item.items() if nk not in metadata_keys and nv is not None}
                    if nested_item:
                        nested_list.append(nested_item)
                else:
                    nested_list.append(item)
            if nested_list:
                cleaned[key] = nested_list
        else:
            cleaned[key] = value
    return cleaned


def _compact_content(entry: dict[str, Any], collection: str) -> dict[str, Any]:
    if collection == "activity_entries":
        parts = []
        for value in [
            _clean_text(entry.get("activity_name")),
            _clean_text(entry.get("position_title")),
            _clean_text(entry.get("activity_type")),
        ]:
            if value and value not in parts:
                parts.append(value)
        duration = _clean_text(entry.get("duration"))
        if duration and not _is_artifact(duration, is_duration=True):
            parts.append(f"duration {duration}")
        level = _clean_text(entry.get("level"))
        if level:
            parts.append(level)
        detail = (
            _truncate_text(entry.get("achievement"), max_words=16)
            or _truncate_text(entry.get("roles_and_responsibilities"), max_words=16)
            or _truncate_text(entry.get("description_raw"), max_words=16)
        )
        if detail:
            parts.append(detail)
        return {"summary": "; ".join(parts)} if parts else {}

    if collection == "academic_entries":
        content: dict[str, Any] = {
            "academic_level": entry.get("academic_level"),
            "academic_year": entry.get("academic_year"),
            "overall_score": entry.get("score_raw"),
            "overall_max": entry.get("max_score_raw"),
            "grading_mode": entry.get("grading_mode"),
        }
        subjects = []
        for sub in entry.get("subject_entries", []) or []:
            score = _safe_float(sub.get("score_raw"))
            max_score = _safe_float(sub.get("max_score_raw")) or 100.0
            subject_name = _clean_text(sub.get("subject_name"))
            if score is None or not subject_name:
                continue
            subjects.append((score, subject_name, max_score))
        if subjects:
            high_score, high_subject, high_max = max(subjects, key=lambda item: (item[0] / item[2]) * 100)
            low_score, low_subject, low_max = min(subjects, key=lambda item: (item[0] / item[2]) * 100)
            content["subject_summary"] = {
                "highest_subject": high_subject,
                "highest_score": f"{high_score:.1f}/{high_max:.0f}",
                "lowest_subject": low_subject,
                "lowest_score": f"{low_score:.1f}/{low_max:.0f}",
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
            score = _safe_float(section.get("raw_score"))
            label = _clean_text(section.get("label"))
            if score is None or not label:
                continue
            scores.append((score, label))
        if scores:
            highest = max(score for score, _ in scores)
            lowest, lowest_label = min(scores, key=lambda item: item[0])
            if highest - lowest >= 8:
                sections.append({"label": lowest_label, "score": f"{lowest:.2f}".rstrip('0').rstrip('.')})
        if sections:
            content["sections"] = sections
        return {k: v for k, v in content.items() if v is not None}

    if collection == "essay_entries":
        content = {
            "essay_identifier": entry.get("essay_identifier"),
            "text_excerpt": _truncate_text(entry.get("raw_text"), max_words=300),
        }
        return {k: v for k, v in content.items() if v is not None}

    return _clean_entry(entry, collection)


def _build_entity_cache(canonical: dict[str, Any], entity_id_map: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    compact_mode = settings.LLM_PAYLOAD_MODE == "compact"
    entity_cache: dict[str, dict[str, Any]] = {}
    collection_cursors: dict[str, int] = {}
    for mapping in entity_id_map:
        entity_id = mapping.get("entity_id")
        collection = mapping.get("collection")
        if not entity_id or not collection:
            continue
        entries = canonical.get(collection, [])
        idx = collection_cursors.get(collection, 0)
        if idx < len(entries):
            entry = entries[idx]
            entity_cache[entity_id] = {
                "entity_id": entity_id,
                "collection": collection,
                "content": _compact_content(entry, collection) if compact_mode else _clean_entry(entry, collection),
            }
        collection_cursors[collection] = idx + 1
    return entity_cache


def _build_signal_snapshot(signal: dict[str, Any]) -> dict[str, Any]:
    return {
        "signal_id": signal.get("signal_id"),
        "theme_id": signal.get("theme_id"),
        "title": signal.get("title"),
        "core_observation": signal.get("core_observation"),
        "interview_opening": signal.get("interview_opening"),
        "referenced_entity_ids": signal.get("referenced_entity_ids", []),
        "supporting_det_signal_ids": signal.get("supporting_det_signal_ids", []),
        "supporting_fragment_ids": signal.get("supporting_fragment_ids", []),
    }


def _build_signal_evidence_pair(signal: dict[str, Any], entity_cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    evidence = []
    for entity_id in signal.get("referenced_entity_ids", []):
        cached = entity_cache.get(entity_id)
        if cached:
            evidence.append(cached)
    return {
        "signal": _build_signal_snapshot(signal),
        "evidence": evidence,
    }


def construct_focus_area_bundle(validated_call_1_output: dict, canonical: dict, entity_id_map: list) -> dict:
    validated_signals = validated_call_1_output.get("signals", [])
    validated_themes = validated_call_1_output.get("themes", [])
    entity_cache = _build_entity_cache(canonical, entity_id_map)
    signal_lookup = {signal.get("signal_id"): signal for signal in validated_signals if signal.get("signal_id")}

    theme_groups = []
    for theme in validated_themes:
        supporting_ids = [sig_id for sig_id in theme.get("supporting_signal_ids", []) if sig_id in signal_lookup]
        theme_groups.append({
            "theme": {
                "theme_id": theme.get("theme_id"),
                "title": theme.get("title"),
                "supporting_signal_ids": supporting_ids,
                "referenced_entity_ids": theme.get("referenced_entity_ids", []),
            },
            "signal_evidence_pairs": [
                _build_signal_evidence_pair(signal_lookup[sig_id], entity_cache)
                for sig_id in supporting_ids
            ],
        })

    app_id = canonical.get("identifiers", {}).get("application_id", "UNKNOWN")
    return {
        "application_id": app_id,
        "theme_signal_evidence_groups": theme_groups,
    }


def construct_question_bundle(
    validated_call_1_output: dict,
    validated_focus_areas_output: dict,
    canonical: dict,
    entity_id_map: list,
) -> dict:
    validated_signals = validated_call_1_output.get("signals", [])
    validated_themes = validated_call_1_output.get("themes", [])
    focus_areas = validated_focus_areas_output.get("focus_areas", [])
    entity_cache = _build_entity_cache(canonical, entity_id_map)
    signal_lookup = {signal.get("signal_id"): signal for signal in validated_signals if signal.get("signal_id")}
    theme_lookup = {theme.get("theme_id"): theme for theme in validated_themes if theme.get("theme_id")}

    question_focus_areas = []
    for focus_area in focus_areas:
        source_theme_ids = [theme_id for theme_id in focus_area.get("source_theme_ids", []) if theme_id in theme_lookup]
        source_signal_ids = [signal_id for signal_id in focus_area.get("source_signal_ids", []) if signal_id in signal_lookup]
        question_focus_areas.append({
            "focus_area": focus_area,
            "themes": [theme_lookup[theme_id] for theme_id in source_theme_ids],
            "signals": [
                _build_signal_evidence_pair(signal_lookup[signal_id], entity_cache)
                for signal_id in source_signal_ids
            ],
        })

    app_id = canonical.get("identifiers", {}).get("application_id", "UNKNOWN")
    return {
        "application_id": app_id,
        "focus_areas": question_focus_areas,
    }


def construct_bundle(validated_call_1_output: dict, canonical: dict, entity_id_map: list) -> dict:
    return construct_focus_area_bundle(validated_call_1_output, canonical, entity_id_map)
