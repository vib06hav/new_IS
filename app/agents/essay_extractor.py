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
    
    EXCLUDED_PROMPTS = [
        "is there anything else which you would like to share with us",
        "help us understand you better",
        "upload your file",
        "additional information",
        "preferred major",
        "declaration",
        "extra- curricular activities",
        "leadership role at school",
        "co- curricular activities"
    ]
    
    # Function to flush current essay
    def flush_essay():
        nonlocal current_text, current_identifier
        text_to_flush = current_text.strip()
        word_count = len(text_to_flush.split())
        
        # Only flush if there's substantial text
        if text_to_flush and word_count > 30:
            entries.append({
                "entry_id": str(uuid.uuid4()),
                "essay_identifier": current_identifier[:200],
                "raw_text": text_to_flush,
                "word_count": word_count,
                "placeholder_flag": False,
                "short_response_flag": word_count < 50,
                "confidence_score": confidence
            })
        current_text = ""
        current_identifier = "Unidentified Section"

    for block in section_blocks:
        text = block.get("text", "").strip()
        lower_text = text.lower()
        if not text or lower_text == "essays": continue
        
        # 1. Detect and Switch Context for specific headers
        if any(exc in lower_text for exc in EXCLUDED_PROMPTS):
            flush_essay()
            # If it's a known header, we might want to skip subsequent text
            current_identifier = "Excluded: " + text
            continue
        
        # 2. Skip short boilerplate
        if len(text.split()) < 3 and text.lower() in ["no", "yes", "description", "1.", "2.", "3."]:
            continue

        # 3. Detect Essay Prompt
        is_prompt = (text.endswith("?") and len(text.split()) < 60) or \
                    "prompt:" in lower_text or \
                    lower_text.startswith("what excites you") or \
                    lower_text.startswith("share a time")

        if is_prompt:
            # If we were in an 'Excluded' zone, reset ID
            if "Excluded:" in current_identifier or "Unidentified" in current_identifier:
                current_text = ""
            
            flush_essay()
            current_identifier = text
        else:
            # Only append if we have a valid identifier (not in excluded zone)
            if not current_identifier.startswith("Excluded:"):
                current_text += text + " "
            
    # Final flush
    flush_essay()

    return {
        "essay_entries": entries,
        "confidence_score": confidence
    }
