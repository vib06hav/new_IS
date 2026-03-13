from typing import List, Dict, Any
import re

def detect_cross_sections(
    academic_entries: List[Dict],
    test_entries: List[Dict],
    essay_entries: List[Dict],
    activity_entries: List[Dict]
) -> Dict[str, Any]:
    """
    Cross-Section Entity Detector. Token-filtered entity detection.
    """
    confidence = 0.95
    entity_map = {}
    
    # Collect all tokens from proper nouns or specific capitalized words
    def extract_tokens(text: str) -> List[str]:
        if not text:
            return []
        # Find capitalized words > 3 chars as potential entities
        tokens = re.findall(r'\b[A-Z][a-z]{3,}\b', text)
        return list(set(tokens))

    # Map sources
    sources = []
    for entry in academic_entries:
        sources.append(("academic", entry["entry_id"], entry.get("academic_level", "")))
        for subj in entry.get("subject_entries", []):
            sources.append(("academic", entry["entry_id"], subj.get("subject_name", "")))
            
    for entry in test_entries:
        sources.append(("test", entry["entry_id"], entry.get("test_name", "")))
        
    for entry in essay_entries:
        sources.append(("essay", entry["entry_id"], entry.get("raw_text", "")))
        
    for entry in activity_entries:
        # Use all potential text fields for entity detection, safely handling None
        parts = [
            entry.get("activity_name"),
            entry.get("position_title"),
            entry.get("achievement"),
            entry.get("roles_and_responsibilities"),
            entry.get("description_raw")
        ]
        text = " ".join([str(p) for p in parts if p])
        sources.append(("activity", entry["entry_id"], text))

    for s_type, s_id, text in sources:
        for token in extract_tokens(text):
            if token not in entity_map:
                entity_map[token] = []
            entity_map[token].append({"source_type": s_type, "entry_id": s_id})
            
    # Filter to tokens that appear in more than 1 source
    final_entities = []
    for token, refs in entity_map.items():
        if len(refs) > 1:
            # Deduplicate refs
            unique_refs = []
            seen = set()
            for r in refs:
                k = (r["source_type"], r["entry_id"])
                if k not in seen:
                    seen.add(k)
                    unique_refs.append(r)
            if len(unique_refs) > 1:
                final_entities.append({
                    "entity_token": token,
                    "source_references": unique_refs
                })
                
    return {
        "entity_map": final_entities,
        "confidence_score": confidence
    }
