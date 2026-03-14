import re

def build_projection(canonical: dict, entity_id_map: list, deterministic_signals: list) -> dict:
    """
    Agent 13: Canonical projection builder for LLM Call 1.
    Constructs a cleaned view of the canonical representation.
    Applies null omission, parse artifact detection, and field inclusion rules.
    """
    
    # 1. Applicant Context
    identifiers = canonical.get("identifiers", {})
    context = {
        "full_name": identifiers.get("full_name"),
        "preferred_major": identifiers.get("preferred_major")
    }
    
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
    
    # 2. Academic Profile
    academic_profile = []
    for entry in canonical.get("academic_entries", []):
        ent_id = next((e["entity_id"] for e in entity_id_map if e.get("collection") == "academic_entries" and e.get("descriptor") == entry.get("academic_level")), None)
        if not ent_id:
            continue
            
        aca_entry = {
            "entity_id": ent_id,
            "level": entry.get("academic_level"),
            "school_name": entry.get("school_name"),
            "board_name": entry.get("board_name"),
            "year": entry.get("academic_year"),
            "grading_mode": entry.get("grading_mode"),
            "overall_score": entry.get("score_raw")
        }
        
        if entry.get("predicted_score_raw") is not None:
            aca_entry["predicted_score_raw"] = entry.get("predicted_score_raw")
            
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
        
        sections = []
        for s in entry.get("sectional_scores", []):
            cleaned_sec = {
                "label": s.get("label"),
                "score": s.get("raw_score")
            }
            sections.append({k: v for k, v in cleaned_sec.items() if v is not None})
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
            
        essay_profile.append({
            "entity_id": ent_id,
            "prompt": entry.get("essay_identifier"),
            "text": entry.get("raw_text")
        })

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
        # Match using name, then type as fallback descriptor
        desc = entry.get("activity_name") or entry.get("activity_type")
        ent_id = next((e["entity_id"] for e in entity_id_map if e.get("collection") == "activity_entries" and e.get("descriptor") == desc), None)
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
            
        # Sparse drop check: must have name, position, or achievement
        if not any(k in act_entry for k in ["name", "position", "achievement"]):
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
