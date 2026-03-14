import re

def construct_bundle(validated_signals: list, canonical: dict, entity_id_map: list) -> dict:
    """
    Agent 15: Signal–evidence bundle constructor.
    Pairs validated interpreted signals with their canonical evidence.
    Includes only non-null relevant fields, omitting internal metadata or artifacts.
    """

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
                    "content": clean_entry(entry, coll)
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
