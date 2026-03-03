from typing import List, Dict, Any
import uuid

def extract_essays(section_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract essays as a collection. Word count, character count.
    """
    entries = []
    confidence = 0.90
    
    current_entry = None
    
    for block in section_blocks:
        text = block.get("text", "")
        lines = text.split('\n')
        
        # New essay heuristic: Prompt:, Q1:, Essay 1:, etc.
        for line in lines:
            if "prompt:" in line.lower() or "question:" in line.lower() or "essay 1:" in line.lower() or "essay 2:" in line.lower():
                if current_entry:
                    # Finalize current
                    text_content = current_entry["raw_text"]
                    words = text_content.split()
                    current_entry["word_count"] = len(words)
                    current_entry["character_count"] = len(text_content)
                    entries.append(current_entry)
                
                current_entry = {
                    "entry_id": str(uuid.uuid4()),
                    "essay_identifier": line[:100], # First 100 chars as identifier
                    "raw_text": "",
                    "word_count": 0,
                    "character_count": 0,
                    "placeholder_flag": False,
                    "duplication_ratio": 0.0,
                    "short_response_flag": False,
                    "confidence_score": confidence
                }
            elif current_entry:
                current_entry["raw_text"] += line + "\n"
                
    if current_entry:
        text_content = current_entry["raw_text"]
        words = text_content.split()
        current_entry["word_count"] = len(words)
        current_entry["character_count"] = len(text_content)
        current_entry["short_response_flag"] = len(words) < 50
        current_entry["placeholder_flag"] = "todo" in text_content.lower() or len(text_content) < 10
        entries.append(current_entry)
        
    return {
        "essay_entries": entries,
        "confidence_score": confidence
    }
