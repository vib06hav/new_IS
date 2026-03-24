import re
from typing import List, Dict, Any
from app.utils.form_vocab import SECTION_HEADERS

# Build lookup set from centralized registry
KNOWN_SECTIONS = list(SECTION_HEADERS)

def detect_sections(blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Groups ordered blocks into labeled sections.
    """
    sections = []
    current_section = {
        "label": "document_start",
        "blocks": []
    }
    
    confidence = 0.90
    
    for block in blocks:
        text = block["text"]
        # Fuzzy matching heuristic: short, capitalized strings
        lines = text.split('\n')
        first_line = lines[0].strip()
        
        # Heuristic for section header: short text, title case or upper case, potentially matching known headers
        is_header = False
        if len(first_line) < 60:
            # Clean first_line of common prefixes like "1. ", "Activity 1:"
            cleaned_line = re.sub(r'^(?:\d+\.|\w+\s+\d+:?)\s*', '', first_line).strip()
            
            if cleaned_line and any(cleaned_line.lower() == known.lower() for known in KNOWN_SECTIONS):
                is_header = True
            elif first_line.isupper() and 2 < len(first_line.split()) < 6 and first_line not in ["YES", "NO", "NA"]:
                # Potential unknown section
                is_header = True
        
        if is_header:
            if current_section["blocks"] or current_section["label"] != "document_start":
                sections.append(current_section)
            current_section = {
                "label": first_line,
                "blocks": []
            }
            # Add remaining lines of the block if any
            if len(lines) > 1:
                remaining_text = "\n".join(lines[1:]).strip()
                if remaining_text:
                    # Preserve coordinates for the remaining text
                    current_section["blocks"].append({
                        "page": block["page"], 
                        "text": remaining_text,
                        "bbox": block["bbox"]
                    })
        else:
            current_section["blocks"].append(block)
            
    if current_section["blocks"] or current_section["label"] != "document_start":
        sections.append(current_section)
        
    return {
        "sections": sections,
        "confidence_score": confidence
    }
