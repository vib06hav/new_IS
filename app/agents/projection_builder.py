import re

from app.config import settings
from app.utils.form_vocab import is_stop_word

def build_projection(canonical: dict, entity_id_map: list, deterministic_signals: list) -> dict:
    """
    Agent 13: Canonical projection builder for LLM Call 1.
    Constructs a cleaned view of the canonical representation.
    Applies null omission, parse artifact detection, and field inclusion rules.
    """
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
                current_max = _safe_float(entry.get("max_score_raw")) or 100.0
                prev_max = _safe_float(previous_entry.get("max_score_raw")) or 100.0
                
                current_p = (current_score / current_max) * 100
                prev_p = (previous_score / prev_max) * 100
                diff_p = current_p - prev_p
                
                if diff_p <= -7:
                    notes.append(
                        f"Performance dipped from {previous_entry.get('academic_level')} to {entry.get('academic_level')} by {abs(diff_p):.1f} percentage points"
                    )
                elif diff_p >= 7:
                    notes.append(
                        f"Performance improved from {previous_entry.get('academic_level')} to {entry.get('academic_level')} by {diff_p:.1f} percentage points"
                    )

            subjects = entry.get("subject_entries", []) or []
            subject_scores = []
            for subject in subjects:
                score = _safe_float(subject.get("score_raw"))
                mx = _safe_float(subject.get("max_score_raw")) or 100.0
                if score is not None:
                    subject_scores.append((score, _clean_text(subject.get("subject_name")), mx))
            if subject_scores:
                lowest_score, lowest_subject, lowest_max = min(subject_scores, key=lambda item: (item[0]/item[2])*100)
                lowest_p = (lowest_score / lowest_max) * 100
                if lowest_subject and lowest_p <= 80:
                    notes.append(
                        f"{entry.get('academic_level')} includes a lower subject score in {lowest_subject} ({lowest_score:.1f}/{lowest_max:.0f})"
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

        for score, label in section_scores:
            cleaned_sec = {"label": label, "score": f"{score:.2f}".rstrip("0").rstrip(".")}
            sections.append({k: v for k, v in cleaned_sec.items() if v is not None})
        return sections

    academic_entries = canonical.get("academic_entries", [])
    academic_summary = _build_academic_summary(academic_entries)

    # 1. Applicant Context
    identifiers = canonical.get("identifiers", {})
    context = {"preferred_major": identifiers.get("preferred_major")}
    context["full_name"] = identifiers.get("full_name")
    
    family = identifiers.get("family_background", {})
    context_family = {}
    if family:
        for parent_key in ["father", "mother"]:
            if parent_key in family and isinstance(family[parent_key], dict):
                parent_data = family[parent_key]
                cleaned_parent = {k: v for k, v in parent_data.items() if v is not None}
                if cleaned_parent:
                    context_family[parent_key] = cleaned_parent
    
    if context_family:
        context["family_background"] = context_family

    geo = identifiers.get("geographic_context", {})
    if isinstance(geo, dict):
        cleaned_geo = {k: v for k, v in geo.items() if v is not None}
        if cleaned_geo:
            context["geographic_context"] = cleaned_geo
    
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
            "overall_score": entry.get("score_raw"),
            "max_score": entry.get("max_score_raw")
        }

        aca_entry["school_name"] = entry.get("school_name")
        aca_entry["board_name"] = entry.get("board_name")
        
        if entry.get("predicted_score_raw") is not None:
            aca_entry["predicted_score_raw"] = entry.get("predicted_score_raw")
            
        subjects = []
        for sub in entry.get("subject_entries", []):
            name = sub.get("subject_name", "").lower()
            score_str = sub.get("score_raw")
            
            # Logic for "Interesting" subjects
            is_interesting = False
            if "math" in name or "physics" in name:
                is_interesting = True
            
            if score_str:
                try:
                    score_val = float(score_str)
                    if score_val <= 80 or score_val >= 99: # Include poor or excellent performance
                        is_interesting = True
                except ValueError:
                    pass
            
            if is_interesting:
                s_entry = {
                    "subject": sub.get("subject_name"),
                    "score": sub.get("score_raw"),
                    "max_score": sub.get("max_score_raw")
                }
                if sub.get("predicted_score_raw") is not None:
                    s_entry["predicted_score"] = sub.get("predicted_score_raw")
                cleaned_s = {k: v for k, v in s_entry.items() if v is not None}
                if cleaned_s:
                    subjects.append(cleaned_s)
        
        if subjects:
            aca_entry["subjects_concise"] = subjects
            
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
            "prompt": entry.get("essay_identifier"),
            "text": _truncate_text(entry.get("raw_text"), max_words=1000)
        }
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
        
        # Use centralized stop-word check instead of a local blocklist
        if is_stop_word(s_text):
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
    projection = {
        "applicant_context": {k: v for k, v in context.items() if v is not None},
        "academic_profile": academic_profile,
        "test_profile": test_profile,
        "essay_profile": essay_profile,
        "activity_profile": activity_profile,
        "entity_id_map": entity_id_map,
        "deterministic_signals": deterministic_signals
    }
    if academic_summary:
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
