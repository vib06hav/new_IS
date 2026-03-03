import re
from typing import Dict, Any
import copy
import logging

logger = logging.getLogger(__name__)

def compress_text(text: str) -> str:
    """Deterministically compress text by normalizing whitespace."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def build_synthesis_projection(canonical_data: Dict[str, Any]) -> str:
    """
    Apply strictly deterministic projection, flattening, and compression
    to canonical data for the LLM synthesis boundary. Applies hard token guard
    with fallback truncation layers.
    """
    
    # Apply truncation layers 0 to 8 
    # 0 = No truncation (baseline)
    # 1 = Truncate Activity descriptions
    # 2 = Truncate Essay raw_text
    # 3 = Truncate Timeline entries
    # 4 = Remove Cross-reference details
    # 5 = Remove Subject-level granularity
    # 6 = Remove predicted_score_raw
    # 7 = Remove percentile
    # 8 = Remove rank
    for level in range(9):
        prompt_text = _render_projection(canonical_data, truncation_level=level)
        tokens = len(prompt_text) // 4
        if tokens <= 3000:
            if level > 0:
                logger.info(f"LLM Projection applied truncation level {level} to meet token guard ({tokens} tokens estimated).")
            return prompt_text
            
    # Exhausted all truncations and still too long
    logger.error("LLM Projection exceeded 3000 tokens even at max truncation level.")
    raise ValueError("LLM projection exceeds safe threshold even after all truncations.")

def _render_projection(data: Dict[str, Any], truncation_level: int) -> str:
    # Create a safe copy to play with for this level
    working_data = copy.deepcopy(data)
    
    lines = []
    
    # 1. SNAPSHOT INPUT (Identifiers)
    lines.append("SNAPSHOT INPUT")
    identifiers = working_data.get("identifiers", {})
    if "full_name" in identifiers:
        lines.append(f"- Name: {identifiers['full_name']}")
    if "declared_preferences" in identifiers:
        lines.append(f"- Preferences: {identifiers['declared_preferences']}")
    if "demographic_flags" in identifiers:
        lines.append(f"- Demographic Flags: {identifiers['demographic_flags']}")
    lines.append("")
        
    # 2. ACADEMIC ENTRIES
    lines.append("ACADEMIC ENTRIES")
    for group in working_data.get("academic_entries", []):
        lines.append(f"- Level: {group.get('academic_level', 'Unknown')}")
        if group.get("board_name"):
            lines.append(f"  Board: {group['board_name']}")
        if group.get("academic_year"):
            lines.append(f"  Year: {group['academic_year']}")
        if group.get("marking_scheme_raw"):
            lines.append(f"  Scheme: {group['marking_scheme_raw']}")
        if group.get("score_raw"):
            lines.append(f"  Score: {group['score_raw']}")
            
        if truncation_level < 6 and group.get("predicted_score_raw"):
            lines.append(f"  Predicted Score: {group['predicted_score_raw']}")
            
        sub_entries = group.get("subject_entries", [])
        if sub_entries and truncation_level < 5:
            lines.append("  Subjects:")
            for sub in sub_entries:
                sub_line = f"    - {sub.get('subject_name', 'Unknown')}: {sub.get('score_raw', '')}"
                if truncation_level < 6 and sub.get('predicted_score_raw'):
                    sub_line += f" (Predicted: {sub['predicted_score_raw']})"
                lines.append(sub_line)
    lines.append("")
    
    # 3. TEST ENTRIES
    lines.append("TEST ENTRIES")
    for test in working_data.get("test_entries", []):
        lines.append(f"- Test: {test.get('test_name', 'Unknown')}")
        if test.get("test_date"):
            lines.append(f"  Date: {test['test_date']}")
        if test.get("total_score"):
            lines.append(f"  Total Score: {test['total_score']}")
        if truncation_level < 7 and test.get("percentile"):
            lines.append(f"  Percentile: {test['percentile']}")
        if truncation_level < 8 and test.get("rank"):
            lines.append(f"  Rank: {test['rank']}")
        if test.get("result_status"):
            lines.append(f"  Status: {test['result_status']}")
            
        sections = test.get("sectional_scores", [])
        if sections and isinstance(sections, list):
            lines.append("  Sections:")
            for sec in sections:
                if isinstance(sec, dict):
                    k = sec.get("label", "Unknown")
                    v = sec.get("raw_score", "Unknown")
                    lines.append(f"    - {k}: {v}")
    lines.append("")
    
    # 4. ESSAYS
    lines.append("ESSAYS")
    for essay in working_data.get("essay_entries", []):
        lines.append(f"- Essay Identifier: {essay.get('essay_identifier', 'Unknown')}")
        raw = compress_text(essay.get("raw_text", ""))
        
        # Apply truncation_level 2 logic: Max 2000 per essay if >1
        if truncation_level >= 2:
            raw = raw[:2000]
            
        lines.append(f"  Content: {raw}")
    lines.append("")
    
    # 5. ACTIVITIES
    lines.append("ACTIVITIES")
    for act in working_data.get("activity_entries", []):
        lines.append(f"- Activity: {act.get('activity_name', 'Unknown')}")
        if act.get("category"):
            lines.append(f"  Category: {act['category']}")
        if act.get("level"):
            lines.append(f"  Level: {act['level']}")
        if act.get("duration"):
            lines.append(f"  Duration: {act['duration']}")
            
        desc = compress_text(act.get("description_raw", ""))
        
        # Apply truncation_level 1 logic: Max 500 per activity if >=1
        if truncation_level >= 1:
            desc = desc[:500]
            
        lines.append(f"  Description: {desc}")
    lines.append("")
    
    # 6. TIMELINE
    # Apply truncation_level 3 logic: remove all timeline entries
    if truncation_level < 3:
        lines.append("TIMELINE")
        for tl in working_data.get("timeline_entries", []):
            lines.append(f"  {tl.get('year', 'Unknown')}: {tl.get('event_label', 'Unknown')} ({tl.get('source_type', 'Unknown')})")
        lines.append("")
    
    # 7. STRUCTURAL NOTES (Integrity + Cross References)
    lines.append("STRUCTURAL NOTES")
    
    if truncation_level < 4:
        cross_refs = working_data.get("cross_references", {})
        entity_map = cross_refs.get("entity_map", []) if isinstance(cross_refs, dict) else []
        if entity_map:
            lines.append("  Cross References:")
            for xr in entity_map:
                if isinstance(xr, dict):
                    src_refs = xr.get('source_references', [])
                    if isinstance(src_refs, list) and src_refs:
                        stypes = [r.get('source_type', 'Unknown') for r in src_refs if isinstance(r, dict)]
                        stype_str = ", ".join(stypes) if stypes else "Unknown"
                    else:
                        stype_str = "Unknown"
                    lines.append(f"  - Entity: {xr.get('entity_token', 'Unknown')} (Source: {stype_str})")
                
    integrity = working_data.get("integrity_report", {})
    anomalies = integrity.get("anomalies", [])
    if anomalies:
        lines.append("  Integrity Anomalies:")
        for an in anomalies:
            lines.append(f"  - Type: {an.get('anomaly_type', 'Unknown')} - {an.get('description', '')}")
            
    lines.append("")

    return "\n".join(lines).strip()
