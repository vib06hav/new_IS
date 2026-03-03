import os
from typing import List, Dict, Any
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

def extract_layout_blocks(pdf_path: str) -> Dict[str, Any]:
    """
    Extracts ordered text blocks from a PDF using pdfminer.six.
    Returns page metadata and blocks.
    """
    if not os.path.exists(pdf_path):
        return {"blocks": [], "page_count": 0, "confidence_score": 0.0, "error": "File not found"}

    blocks = []
    page_count = 0
    confidence = 0.95  # Base confidence for native PDF extraction

    try:
        for page_layout in extract_pages(pdf_path):
            page_count += 1
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text = element.get_text().strip()
                    if text:
                        blocks.append({
                            "page": page_count,
                            "text": text,
                            "bbox": element.bbox,  # (x0, y0, x1, y1)
                        })
    except Exception as e:
        return {"blocks": [], "page_count": 0, "confidence_score": 0.0, "error": str(e)}

    # Simple OCR anomaly check: if no text from layout but pages exist
    if page_count > 0 and len(blocks) == 0:
        confidence = 0.1 # Likely a scanned PDF without text layer
        
    return {
        "blocks": blocks,
        "page_count": page_count,
        "confidence_score": confidence
    }
