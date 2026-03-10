from typing import List, Dict, Any
import uuid

def extract_essays(section_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract essays as a collection from a set of layout blocks using heuristic chunking.
    """
    entries = []
    confidence = 0.90
    
    current_identifier = "Essay"
    current_text = ""
    
    for block in section_blocks:
        text = block.get("text", "").strip()
        if not text or text.lower() == "essays": continue
        
        # If block looks like a question or instruction
        if text.endswith("?") or 10 < len(text.split()) < 40 or "prompt:" in text.lower():
            if current_text and len(current_text.split()) > 30:
                entries.append({
                    "entry_id": str(uuid.uuid4()),
                    "essay_identifier": current_identifier[:100],
                    "raw_text": current_text,
                    "word_count": len(current_text.split()),
                    "character_count": len(current_text),
                    "placeholder_flag": False,
                    "duplication_ratio": 0.0,
                    "short_response_flag": len(current_text.split()) < 50,
                    "confidence_score": confidence
                })
                current_text = ""
            current_identifier = text
        else:
            current_text += text + "\n"
            
    if current_text and len(current_text.split()) > 20:
        entries.append({
            "entry_id": str(uuid.uuid4()),
            "essay_identifier": current_identifier[:100],
            "raw_text": current_text.strip(),
            "word_count": len(current_text.split()),
            "character_count": len(current_text),
            "placeholder_flag": False,
            "duplication_ratio": 0.0,
            "short_response_flag": len(current_text.split()) < 50,
            "confidence_score": confidence
        })

    return {
        "essay_entries": entries,
        "confidence_score": confidence
    }
