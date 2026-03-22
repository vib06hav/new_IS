from typing import Dict, Any, Tuple, List
import copy

def _assign_entity_ids(canonical_data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Deterministically assigns entity_ids to canonical entries based on array position.
    Returns:
    - annotated_canonical: A shallow copy of canonical with entity_ids injected into the lists
    - entity_id_map: A list of dicts {entity_id, collection, descriptor}
    """
    
    annotated = copy.deepcopy(canonical_data)
    entity_id_map = []
    
    def annotate(collection_name: str, prefix: str):
        collection = annotated.get(collection_name, [])
        for i, item in enumerate(collection, 1):
            
            if collection_name == "activity_entries":
                act_type = item.get("activity_type", "other")
                current_prefix = "LEAD" if act_type == "leadership" else "ACT"
                ent_id = f"{current_prefix}-{i:03d}"
            else:
                ent_id = f"{prefix}-{i:03d}"
                
            item["entity_id"] = ent_id
            
            # Extract descriptor
            descriptor = (
                item.get("activity_name") or 
                item.get("position_title") or 
                item.get("academic_level") or 
                item.get("test_name") or 
                item.get("essay_identifier") or 
                item.get("school_name") or
                "Unknown"
            )
            
            entity_id_map.append({
                "entity_id": ent_id,
                "collection": collection_name,
                "descriptor": descriptor
            })
                
    annotate("schooling_history", "SCH")
    annotate("academic_entries", "ACA")
    annotate("test_entries", "TEST")
    annotate("essay_entries", "ESS")
    annotate("activity_entries", "ACT")
    
    return annotated, entity_id_map


def _project_page_1(annotated: Dict[str, Any]) -> Dict[str, Any]:
    identifiers = annotated.get("identifiers", {})
    page_1 = {
        "identity": identifiers,
        "family_background": identifiers.get("family_background", None),
        "schooling_history": annotated.get("schooling_history", []),
        "academic_orientation": identifiers.get("declared_preferences", {})
    }
    return page_1


def _project_page_2(annotated: Dict[str, Any]) -> Dict[str, Any]:
    activities = annotated.get("activity_entries", [])
    
    extra = [a for a in activities if a.get("activity_type") in ("extracurricular", "other")]
    co_curr = [a for a in activities if a.get("activity_type") == "co_curricular"]
    lead = [a for a in activities if a.get("activity_type") == "leadership"]
    
    page_2 = {
        "academic_records": annotated.get("academic_entries", []),
        "standardized_tests": annotated.get("test_entries", []),
        "additional_tests": [], 
        "extracurricular_activities": extra,
        "co_curricular_activities": co_curr,
        "leadership_roles": lead
    }
    return page_2


def _compute_highlights(essay: Dict[str, Any], annotated: Dict[str, Any]) -> List[Dict[str, Any]]:
    highlights = []
    text = essay.get("full_text", essay.get("raw_text", ""))
    
    if not text:
        return highlights
        
    keyword_map = {}
    
    # academic
    for a in annotated.get("academic_entries", []):
        if a.get("board_name") and a["board_name"] in text:
            keyword_map[a["board_name"]] = a["entity_id"]
            
    # activities
    for a in annotated.get("activity_entries", []):
        if a.get("activity_name") and a["activity_name"] in text:
            keyword_map[a["activity_name"]] = a["entity_id"]
            
    # test
    for a in annotated.get("test_entries", []):
        if a.get("test_name") and a["test_name"] in text:
            keyword_map[a["test_name"]] = a["entity_id"]
            
    # schooling
    for a in annotated.get("schooling_history", []):
        if a.get("school_name") and a["school_name"] in text:
            keyword_map[a["school_name"]] = a["entity_id"]
            
    for kw, eid in keyword_map.items():
        if not kw: continue
        start = text.find(kw)
        if start != -1:
            end = start + len(kw)
            highlights.append({
                "start_char": start,
                "end_char": end,
                "referenced_entity_ids": [eid]
            })
            
    return highlights


def _project_page_3(annotated: Dict[str, Any]) -> Dict[str, Any]:
    essays = []
    
    for essay in annotated.get("essay_entries", []):
        essay_rep = {
            "entity_id": essay.get("entity_id", ""),
            "prompt": essay.get("essay_identifier", "Unknown"),
            "full_text": essay.get("raw_text", ""),
            "word_count": essay.get("word_count", 0),
            "highlights": _compute_highlights(essay, annotated)
        }
        essays.append(essay_rep)
        
    return {
        "essays": essays
    }


def project_ros(canonical_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
    """
    Deterministic projection layer.
    Returns: (page_1, page_2, page_3, annotated_canonical, entity_id_map)
    Does NOT call the LLM. Does NOT mutate canonical_data.
    """
    
    # 1. Deterministic Entity ID Assignment
    annotated_canonical, entity_id_map = _assign_entity_ids(canonical_data)
    
    # 2. Page Projections
    page_1 = _project_page_1(annotated_canonical)
    page_2 = _project_page_2(annotated_canonical)
    page_3 = _project_page_3(annotated_canonical)
    
    return page_1, page_2, page_3, annotated_canonical, entity_id_map
