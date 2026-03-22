from typing import List, Dict, Any
import uuid
import logging

logger = logging.getLogger(__name__)

def extract_essays(section_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract essays as a collection from a set of layout blocks using heuristic chunking.
    """
    entries = []
    confidence = 0.90

    # If this extractor is called with essay-section-scoped blocks, the "Essays"
    # header may already have been removed by the section detector. In that case
    # we should begin parsing immediately rather than waiting for a gate token
    # that will never arrive.
    contains_explicit_essay_header = any(
        str(block.get("text", "")).strip().lower() == "essays"
        for block in section_blocks
    )
    is_gate_open = not contains_explicit_essay_header
    pending_prompt = ""
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
        "co- curricular activities",
        "description",
        "consent",
        "honour pledge",
        "applicant name",
        "is there anything else you want to tell us"
    ]
    
    # Function to flush current essay
    def flush_essay():
        nonlocal current_text, current_identifier, pending_prompt
        text_to_flush = current_text.strip()
        word_count = len(text_to_flush.split())
        
        # If we have a pending prompt from fragmentation, use it as identifier
        if pending_prompt.strip():
            current_identifier = pending_prompt.strip()
            pending_prompt = ""
        
        # Only flush if there's substantial text and gate is open
        if is_gate_open and text_to_flush and word_count > 30:
            entries.append({
                "entry_id": str(uuid.uuid4()),
                "essay_identifier": current_identifier[:200],
                "raw_text": text_to_flush,
                "word_count": word_count,
                "placeholder_flag": False,
                "short_response_flag": word_count < 50,
                "confidence_score": confidence
            })
            logger.debug(
                "Essay extracted: identifier='%s', words=%s",
                current_identifier[:80],
                word_count
            )
        current_text = ""
        current_identifier = "Unidentified Section"

    for block in section_blocks:
        text = block.get("text", "").strip()
        lower_text = text.lower()
        if not text: continue

        # 0. Gate Check
        if not is_gate_open:
            if lower_text == "essays":
                is_gate_open = True
                logger.info("Essay Gate OPENED.")
            continue
        
        # 1. Detect and Switch Context for specific headers
        if any(exc in lower_text for exc in EXCLUDED_PROMPTS):
            flush_essay()
            current_identifier = "Excluded: " + text
            continue
        
        # 2. Skip short boilerplate
        if len(text.split()) < 3 and text.lower() in ["no", "yes", "1.", "2.", "3."]:
            continue

        # 3. Detect Essay Prompt (Improved for multi-block)
        is_prompt_end = text.endswith("?") and len(text.split()) < 60
        is_prompt_start = "prompt:" in lower_text or \
                          lower_text.startswith("what excites you") or \
                          lower_text.startswith("share a time")

        if is_prompt_start or is_prompt_end:
            flush_essay()
            if is_prompt_start and not is_prompt_end:
                pending_prompt = text + " "
            else:
                current_identifier = (pending_prompt + text).strip()
                pending_prompt = ""
            continue
        
        # If we have a pending prompt fragment, keep accumulating
        if pending_prompt and len(text.split()) < 20:
            pending_prompt += text + " "
            continue

        # 4. Text Accumulation
        if not current_identifier.startswith("Excluded:"):
            current_text += text + " "
            
    # Final flush
    flush_essay()

    return {
        "essay_entries": entries,
        "confidence_score": confidence
    }
