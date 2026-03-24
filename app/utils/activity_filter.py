
import re
from typing import Dict, Any
from app.utils.form_vocab import is_stop_word

def is_valid_activity(entry: Dict[str, Any]) -> bool:
    """
    Centralized validation for activity entries.
    Filters out common hallucinations, form prompts, and metadata artifacts.
    """
    # 1. Stop-word check: reject any position_title that is a known form label
    pos = str(entry.get("position_title") or "").strip()
    if pos and is_stop_word(pos):
        return False
    # Additional context-specific blocklist for activity positions
    activity_blocklist = ["Friends/Family", "Reference", "Email", "Mobile"]
    if pos and any(term.lower() in pos.lower() for term in activity_blocklist):
        return False
    
    # 2. Roles & Responsibilities form prompt check
    roles = str(entry.get("roles_and_responsibilities") or "").strip()
    if roles:
        # Catch common form questions or prompt remnants
        prompts = ["In what capacity", "Is there anything", "Mobile Number", "Email Address", "know you?"]
        if "?" in roles or any(p.lower() in roles.lower() for p in prompts):
            return False
            
        # Catch stop-word terms if they appear alone in roles
        if is_stop_word(roles):
            return False
    
    # 3. Duration artifact check
    dur = entry.get("duration")
    if dur is not None:
        # A valid duration must contain at least one digit
        # This catches things like "Mobile Number" or "Is there anything else" in the duration field
        if not re.search(r"-?\d+\.?\d*", str(dur)):
            return False
            
    # 4. Identity check
    name = str(entry.get("activity_name") or "").strip()
    if not name and not pos:
        return False
        
    return True
