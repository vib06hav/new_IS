import re

from app.config import settings

def build_projection(canonical: dict, entity_id_map: list, deterministic_signals: list) -> dict:
    """
    Agent 13: Canonical projection builder for LLM Call 1.
    Constructs a cleaned view of the canonical representation.
    Applies null omission, parse artifact detection, and field inclusion rules.
    """
    compact_mode = settings.LLM_PAYLOAD_MODE == "compact"

    def _safe_float(value):
        if value is None:
            return None
        match = re.search(r"-?\d+\.?\d*", str(value))
        if not match:
            return None
        try:
            return float(match.group(0))
        except ValueError:
            return None

    def _clean_text(value):
        if value is None:
            return None
        cleaned = re.sub(r"\s+", " ", str(value)).strip()
        return cleaned or None

    def _truncate_text(value, max_words=45):
        cleaned = _clean_text(value)
        if not cleaned:
            return None
        words = cleaned.split()
        if len(words) <= max_words:
            return cleaned
        return " ".join(words[:max_words]) + "..."

    def _compact_parent(parent_data):
        compact_parent = {}
        for field in ["education", "field_of_employment", "designation", "organization"]:
            value = _clean_text(parent_data.get(field))
            if value:
                compact_parent[field] = value
        return compact_parent

    def _build_activity_summary(entry):
        parts = []
        for value in [
            _clean_text(entry.get("activity_name")),
            _clean_text(entry.get("position_title")),
            _clean_text(entry.get("activity_type")),
        ]:
            if value and value not in parts:
                parts.append(value)

        duration = _clean_text(entry.get("duration"))
        if duration and not is_artifact(duration, is_duration=True):
            parts.append(f"duration {duration}")

        level = _clean_text(entry.get("level"))
        if level:
            parts.append(level)

        detail = (
            _truncate_text(entry.get("achievement"), max_words=18)
            or _truncate_text(entry.get("roles_and_responsibilities"), max_words=18)
            or _truncate_text(entry.get("description_raw"), max_words=18)
        )
        if detail:
            parts.append(detail)

        if not parts:
            return None
        return "; ".join(parts)

    def _build_academic_summary(entries):
        if not entries:
            return None

        sorted_entries = sorted(
            entries,
            key=lambda item: (
                _safe_float(item.get("academic_year")) if _safe_float(item.get("academic_year")) is not None else 0.0,
                str(item.get("academic_level") or "")
            )
        )

        notes = []
        previous_entry = None
        previous_score = None

        for entry in sorted_entries:
            current_score = _safe_float(entry.get("score_raw"))
            if previous_entry:
                if entry.get("board_name") and previous_entry.get("board_name") and entry.get("board_name") != previous_entry.get("board_name"):
                    notes.append(
                        f"Board changed from {previous_entry.get('board_name')} to {entry.get('board_name')} between {previous_entry.get('academic_level')} and {entry.get('academic_level')}"
                    )
                if entry.get("school_name") and previous_entry.get("school_name") and entry.get("school_name") != previous_entry.get("school_name"):
                    notes.append(
                        f"School changed from {previous_entry.get('school_name')} to {entry.get('school_name')} between {previous_entry.get('academic_level')} and {entry.get('academic_level')}"
                    )
            if previous_score is not None and current_score is not None:
                diff = current_score - previous_score
                if diff <= -7:
                    notes.append(
                        f"Performance dipped from {previous_entry.get('academic_level')} to {entry.get('academic_level')} by {abs(diff):.1f} points"
                    )
                elif diff >= 7:
                    notes.append(
                        f"Performance improved from {previous_entry.get('academic_level')} to {entry.get('academic_level')} by {diff:.1f} points"
                    )

            subjects = entry.get("subject_entries", []) or []
            subject_scores = []
            for subject in subjects:
                score = _safe_float(subject.get("score_raw"))
                if score is not None:
                    subject_scores.append((score, _clean_text(subject.get("subject_name"))))
            if subject_scores:
                lowest_score, lowest_subject = min(subject_scores, key=lambda item: item[0])
                if lowest_subject and lowest_score <= 80:
                    notes.append(
                        f"{entry.get('academic_level')} includes a lower subject score in {lowest_subject} ({lowest_score:.1f})"
                    )

            previous_entry = entry
            previous_score = current_score if current_score is not None else previous_score

        unique_notes = []
        seen = set()
        for note in notes:
            if note not in seen:
                seen.add(note)
                unique_notes.append(note)
        return unique_notes

    def _build_test_sections(entry):
        sections = []
        section_scores = []
        for section in entry.get("sectional_scores", []) or []:
            score = _safe_float(section.get("raw_score"))
            if score is None:
                continue
            section_scores.append((score, _clean_text(section.get("label"))))

        if not section_scores:
            return sections

        if compact_mode:
            highest_score = max(score for score, _ in section_scores)
            lowest_score, lowest_label = min(section_scores, key=lambda item: item[0])
            if highest_score - lowest_score >= 8 and lowest_label:
                sections.append({"label": lowest_label, "score": f"{lowest_score:.2f}".rstrip("0").rstrip(".")})
            return sections

        for score, label in section_scores:
            cleaned_sec = {"label": label, "score": f"{score:.2f}".rstrip("0").rstrip(".")}
            sections.append({k: v for k, v in cleaned_sec.items() if v is not None})
        return sections

    academic_entries = canonical.get("academic_entries", [])
    academic_summary = _build_academic_summary(academic_entries)

    # 1. Applicant Context
    identifiers = canonical.get("identifiers", {})
    context = {"preferred_major": identifiers.get("preferred_major")}
    if not compact_mode:
        context["full_name"] = identifiers.get("full_name")
    
    family = identifiers.get("family_background", {})
    context_family = {}
    if family:
        for parent_key in ["father", "mother"]:
            if parent_key in family and isinstance(family[parent_key], dict):
                parent_data = family[parent_key]
                if compact_mode:
                    cleaned_parent = _compact_parent(parent_data)
                else:
                    cleaned_parent = {k: v for k, v in parent_data.items() if v is not None}
                if cleaned_parent:
                    context_family[parent_key] = cleaned_parent
    
    if context_family:
        context["family_background"] = context_family
    
    # 2. Academic Profile
    academic_profile = []
    for academic_index, entry in enumerate(academic_entries):
        ent_id = next((e["entity_id"] for e in entity_id_map if e.get("collection") == "academic_entries" and e.get("descriptor") == entry.get("academic_level")), None)
        if not ent_id:
            continue
            
        aca_entry = {
            "entity_id": ent_id,
            "level": entry.get("academic_level"),
            "year": entry.get("academic_year"),
            "grading_mode": entry.get("grading_mode"),
            "overall_score": entry.get("score_raw")
        }

        if not compact_mode:
            aca_entry["school_name"] = entry.get("school_name")
            aca_entry["board_name"] = entry.get("board_name")
        else:
            previous_entry = academic_entries[academic_index - 1] if academic_index > 0 else None
            if previous_entry is None or entry.get("school_name") != previous_entry.get("school_name"):
                aca_entry["school_name"] = entry.get("school_name")
            if previous_entry is None or entry.get("board_name") != previous_entry.get("board_name"):
                aca_entry["board_name"] = entry.get("board_name")
        
        if entry.get("predicted_score_raw") is not None:
            aca_entry["predicted_score_raw"] = entry.get("predicted_score_raw")
            
        if compact_mode:
            subjects = []
            subject_scores = []
            for sub in entry.get("subject_entries", []):
                score = _safe_float(sub.get("score_raw"))
                subject_name = _clean_text(sub.get("subject_name"))
                if score is None or not subject_name:
                    continue
                subject_scores.append((score, subject_name))
            if subject_scores:
                top_score, top_subject = max(subject_scores, key=lambda item: item[0])
                low_score, low_subject = min(subject_scores, key=lambda item: item[0])
                aca_entry["subject_summary"] = {
                    "highest_subject": top_subject,
                    "highest_score": f"{top_score:.2f}".rstrip("0").rstrip("."),
                    "lowest_subject": low_subject,
                    "lowest_score": f"{low_score:.2f}".rstrip("0").rstrip(".")
                }
        else:
            subjects = []
            for sub in entry.get("subject_entries", []):
                s_entry = {
                    "subject": sub.get("subject_name"),
                    "score": sub.get("score_raw")
                }
                if sub.get("predicted_score_raw") is not None:
                    s_entry["predicted_score"] = sub.get("predicted_score_raw")
                cleaned_s = {k: v for k, v in s_entry.items() if v is not None}
                if cleaned_s:
                    subjects.append(cleaned_s)
            if subjects:
                aca_entry["subjects"] = subjects
            
        cleaned_aca = {k: v for k, v in aca_entry.items() if v is not None}
        if cleaned_aca:
            academic_profile.append(cleaned_aca)

    # 3. Test Profile
    test_profile = []
    for entry in canonical.get("test_entries", []):
        ent_id = next((e["entity_id"] for e in entity_id_map if e.get("collection") == "test_entries" and e.get("descriptor") == entry.get("test_name")), None)
        if not ent_id:
            continue
            
        t_entry = {
            "entity_id": ent_id,
            "test_name": entry.get("test_name"),
            "total_score": entry.get("total_score")
        }
        
        sections = _build_test_sections(entry)
        if sections:
            t_entry["sections"] = sections
            
        if entry.get("percentile") is not None:
            t_entry["percentile"] = entry.get("percentile")
        if entry.get("rank") is not None:
            t_entry["rank"] = entry.get("rank")
            
        cleaned_t = {k: v for k, v in t_entry.items() if v is not None}
        if cleaned_t:
            test_profile.append(cleaned_t)

    # 4. Essay Profile
    essay_profile = []
    for entry in canonical.get("essay_entries", []):
        if entry.get("placeholder_flag") or not entry.get("raw_text"):
            continue
            
        ent_id = next((e["entity_id"] for e in entity_id_map if e.get("collection") == "essay_entries" and e.get("descriptor") == entry.get("essay_identifier")), None)
        if not ent_id:
            continue
            
        essay_entry = {
            "entity_id": ent_id,
            "text": _truncate_text(entry.get("raw_text"), max_words=120 if compact_mode else 1000)
        }
        if not compact_mode:
            essay_entry["prompt"] = entry.get("essay_identifier")
        essay_profile.append(essay_entry)

    # 5. Activity Profile (with Artifact Detection)
    def is_artifact(text, is_duration=False, is_position=False):
        if not text: return True
        s_text = str(text).strip()
        if not s_text: return True
        
        if is_duration:
            try:
                # Must be a numeric string
                float(re.findall(r"\d+\.?\d*", s_text)[0])
                return False
            except (ValueError, IndexError):
                return True
        
        # Generic blocklist for name/responsibilities
        blocklist = ["Organization", "Reference", "Position", "Role", "Title", "Name", "Duration", "Level"]
        if not is_position and s_text in blocklist:
            return True
            
        # Form label patterns
        labels = ["Mobile Number", "Email Address", "Date of Birth"]
        if any(label.lower() in s_text.lower() for label in labels):
            return True
            
        if "?" in s_text:
            return True
            
        return False

    activity_profile = []
    for entry in canonical.get("activity_entries", []):
        # Match using name, then position, then type as fallback descriptor
        desc_candidates = [entry.get("activity_name"), entry.get("position_title"), entry.get("activity_type")]
        ent_id = None
        for cand in desc_candidates:
            if not cand: continue
            ent_id = next((e["entity_id"] for e in entity_id_map if e.get("collection") == "activity_entries" and e.get("descriptor") == cand), None)
            if ent_id: break
            
        if not ent_id:
            continue
            
        act_entry = {
            "entity_id": ent_id,
            "type": entry.get("activity_type")
        }

        if compact_mode:
            summary = _build_activity_summary(entry)
            if not summary:
                continue
            act_entry["summary"] = summary
            activity_profile.append(act_entry)
            continue
        
        # Apply artifact checks
        name = entry.get("activity_name")
        if name and not is_artifact(name):
            act_entry["name"] = name
            
        pos = entry.get("position_title")
        if pos and not is_artifact(pos, is_position=True):
            act_entry["position"] = pos
            
        level = entry.get("level")
        if level:
            act_entry["level"] = level
            
        dur = entry.get("duration")
        if dur and not is_artifact(dur, is_duration=True):
            act_entry["duration_years"] = dur
            
        ach = entry.get("achievement")
        if ach:
            act_entry["achievement"] = ach
            
        resp = entry.get("roles_and_responsibilities")
        if resp and not is_artifact(resp):
            act_entry["responsibilities"] = resp

        desc = entry.get("description_raw")
        if desc:
            act_entry["description"] = desc
            
        # Sparse drop check: must have name, position, achievement, or responsibilities/description
        if not any(k in act_entry for k in ["name", "position", "achievement", "responsibilities", "description"]):
            continue
            
        activity_profile.append(act_entry)

    # 6. Construct final projection
    projection_entity_map = entity_id_map
    if compact_mode:
        referenced_ids = set()
        for section_name in ["academic_profile", "test_profile", "essay_profile", "activity_profile"]:
            for entry in locals().get(section_name, []):
                if isinstance(entry, dict) and entry.get("entity_id"):
                    referenced_ids.add(entry["entity_id"])
        for signal in deterministic_signals:
            for entity_id in signal.get("referenced_entity_ids", []) or []:
                if entity_id:
                    referenced_ids.add(entity_id)
        compact_map = []
        seen = set()
        for entry in entity_id_map:
            entity_id = entry.get("entity_id")
            if entity_id not in referenced_ids or entity_id in seen:
                continue
            seen.add(entity_id)
            compact_entry = {"entity_id": entity_id}
            descriptor = entry.get("descriptor")
            if descriptor:
                compact_entry["descriptor"] = descriptor
            compact_map.append(compact_entry)
        projection_entity_map = compact_map

    projection = {
        "applicant_context": {k: v for k, v in context.items() if v is not None},
        "academic_profile": academic_profile,
        "test_profile": test_profile,
        "essay_profile": essay_profile,
        "activity_profile": activity_profile,
        "entity_id_map": projection_entity_map,
        "deterministic_signals": deterministic_signals
    }
    if compact_mode and academic_summary:
        projection["academic_summary"] = academic_summary
    
    # Internal Verification
    entity_ids_in_map = {e["entity_id"] for e in entity_id_map}
    
    def verify_no_metadata(obj):
        if isinstance(obj, dict):
            metadata_keys = {"entry_id", "confidence_score", "placeholder_flag", "short_response_flag", "result_status", "extraction_confidence", "marking_scheme_raw"}
            for k, v in obj.items():
                if k in metadata_keys:
                    raise RuntimeError(f"Internal metadata found in projection: {k}")
                # We relax null check for descriptors in the entity_id_map as they might be null in source
                if v is None and k != "descriptor":
                    raise RuntimeError(f"Null field found in projection: {k}")
                if k == "entity_id" and v not in entity_ids_in_map:
                    raise RuntimeError(f"Invented entity ID found in projection: {v}")
                verify_no_metadata(v)
        elif isinstance(obj, list):
            for item in obj:
                verify_no_metadata(item)

    verify_no_metadata(projection)
    
    if not projection.get("deterministic_signals"):
        raise RuntimeError("deterministic_signals is missing or empty in projection")

    return projection
