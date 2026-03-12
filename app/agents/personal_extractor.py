from typing import List, Dict, Any

def extract_personal_info(section_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extracts labeled personal fields strictly based on layout bounding boxes.
    Because PDF miner splits labels and values into separate layout blocks,
    we find the block containing the label, then find the corresponding block
    to its right on the same horizontal plane (Y-overlap).
    """
    identifiers = {
        "full_name": None,
        "date_of_birth": None,
        "family_background": {
            "father": {"name": None, "education": None, "field_of_employment": None, "organization": None, "designation": None},
            "mother": {"name": None, "education": None, "field_of_employment": None, "organization": None, "designation": None}
        },
        "declared_preferences": {},
        "demographic_flags": {}
    }
    
    confidence = 0.85
    
    # Helper to find text on the same row to the right of a given block
    def find_value_for_label(label_block: Dict[str, Any]) -> str:
        label_y0, label_y1 = label_block["bbox"][1], label_block["bbox"][3]
        label_x1 = label_block["bbox"][2]
        page = label_block["page"]
        
        candidates = []
        for b in section_blocks:
            if b["page"] != page:
                continue
            if b == label_block:
                continue
            b_y0, b_y1 = b["bbox"][1], b["bbox"][3]
            b_x0 = b["bbox"][0]
            
            # Check Y overlap (allow small vertical drift)
            vertical_overlap = min(label_y1, b_y1) - max(label_y0, b_y0)
            if vertical_overlap > 0 or abs(label_y0 - b_y0) < 5:
                # Must be strictly to the right
                if b_x0 > label_x1:
                    candidates.append(b)
                    
        # Sort candidates left-to-right
        candidates.sort(key=lambda b: b["bbox"][0])
        
        # Filter out candidates that are purely the label repeated or common headers
        for c in candidates:
            c_text_lower = c["text"].strip().lower()
            label_lower = label_block["text"].strip().lower()
            if c_text_lower != label_lower and c_text_lower not in ["organization", "designation"]:
                return c["text"].strip()
                
        return None

    # First pass: identify labels and grab their corresponding values
    for block in section_blocks:
        text = block.get("text", "").strip()
        lower_text = text.lower()
        
        # If the block contains colon directly, handle it
        if ":" in text and len(text.split(":")) > 1:
            val = text.split(":", 1)[1].strip()
            if not val:
                val = find_value_for_label(block)
        else:
            val = find_value_for_label(block)
            
        if not val:
            continue
            
        # Map to canonical schema
        if lower_text == "name" or lower_text == "full name":
            if not identifiers["full_name"]:  # Only set the first 'Name' found (avoid mother/father name override)
                if not "father" in val.lower() and not "mother" in val.lower():
                    identifiers["full_name"] = val
        elif lower_text == "date of birth" or lower_text == "dob":
            if not identifiers["date_of_birth"]:
                identifiers["date_of_birth"] = val
        elif lower_text == "major" or lower_text == "intended major":
             identifiers["declared_preferences"]["major"] = val
        elif lower_text == "first generation":
             identifiers["demographic_flags"]["first_generation"] = (val.lower() == "yes" or val.lower() == "true")
             
    # Second pass: Father/Mother details sections
    # Group blocks that belong to each parent's section using spatial boundaries
    sorted_blocks = sorted(section_blocks, key=lambda b: (b["page"], -b["bbox"][3], b["bbox"][0]))
    
    # Find parent header positions — require short, exact text match
    # to avoid matching instruction text like "Please provide the details..."
    parent_headers = []  # list of (context, page, y_bottom)
    for block in sorted_blocks:
        text = block.get("text", "").strip()
        lower_text = text.lower()
        # Must be a short label, not a long instruction sentence
        if len(text) < 25:
            if lower_text == "father details":
                parent_headers.append(("father", block["page"], block["bbox"][1]))
            elif lower_text in ("mother details", "mother details\u200b"):
                parent_headers.append(("mother", block["page"], block["bbox"][1]))
    
    # For each parent header, collect blocks that belong to its section.
    # Father's data can span page 1 (Name, DOB, Mobile) AND page 2 (education, 
    # occupation, organization) — everything above the Mother Details header.
    # Mother's data is on page 2 below Mother Details header.
    PARENT_LABELS = {
        "name", "highest degree attained", "education",
        "field of employment", "occupation", "organization", "designation",
        "mobile number", "email address", "date of birth",
        "nationality", "educational institute (last attended)",
    }
    
    # Sort headers by (page, -Y) so we process them top-to-bottom
    parent_headers.sort(key=lambda h: (h[1], -h[2]))
    
    for i, (context, hdr_page, hdr_y) in enumerate(parent_headers):
        # Determine boundary: everything from this header down to the next header
        next_context = parent_headers[i + 1] if i + 1 < len(parent_headers) else None
        
        section = []
        for b in section_blocks:
            bp = b["page"]
            by = (b["bbox"][1] + b["bbox"][3]) / 2
            
            if next_context:
                next_page, next_y = next_context[1], next_context[2]
                # Include blocks that are:
                # - On the header page with Y < header Y (below header)
                # - On pages between header and next header
                # - On the next header's page with Y > next header Y (above next header)
                if bp == hdr_page and by < hdr_y:
                    section.append(b)
                elif bp > hdr_page and bp < next_page:
                    section.append(b)
                elif bp == next_page and by > next_y:
                    section.append(b)
            else:
                # Last header: collect blocks below on same page AND the next page,
                # bounded by known section headers (Sibling Details, Address Details, etc.)
                BOUNDARY_LABELS = {
                    "sibling details", "address details", "address details:",
                    "class 9th / equivalent", "class 9th", "languages known",
                }
                next_page = hdr_page + 1
                if bp == hdr_page and by < hdr_y:
                    section.append(b)
                elif bp == next_page:
                    # Stop before boundary sections on the next page
                    btext = b.get("text", "").strip().lower()
                    if btext not in BOUNDARY_LABELS:
                        section.append(b)
        
        for block in section:
            text = block.get("text", "").strip()
            lower_text = text.lower()
            
            # Match labels with tolerance for trailing hyphens/spaces (e.g. "Organization -")
            clean_label = lower_text.strip(" -:")
            
            if clean_label not in PARENT_LABELS:
                continue
                
            val = find_value_for_label(block)
            if not val:
                continue
                
            if clean_label == "name":
                identifiers["family_background"][context]["name"] = val
            elif clean_label in ("highest degree attained", "education"):
                identifiers["family_background"][context]["education"] = val
            elif clean_label in ("field of employment", "occupation"):
                identifiers["family_background"][context]["field_of_employment"] = val
            elif clean_label == "organization":
                identifiers["family_background"][context]["organization"] = val
            elif clean_label == "designation":
                identifiers["family_background"][context]["designation"] = val

    return {
        "identifiers": identifiers,
        "confidence_score": confidence
    }
