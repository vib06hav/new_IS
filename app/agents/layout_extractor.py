import os
import logging
from typing import List, Dict, Any
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

logger = logging.getLogger(__name__)

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

    def clean_text(t: str) -> str:
        if not t: return t
        # Strip zero-width space and decompose common PDF ligatures
        t = t.replace("\u200b", "")
        t = t.replace("\ufb00", "ff").replace("\ufb01", "fi").replace("\ufb02", "fl")
        t = t.replace("\ufb03", "ffi").replace("\ufb04", "ffl")
        return t

    try:
        for page_layout in extract_pages(pdf_path):
            page_count += 1
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text = element.get_text().strip()
                    if text:
                        blocks.append({
                            "page": page_count,
                            "text": clean_text(text),
                            "bbox": element.bbox,  # (x0, y0, x1, y1)
                        })
    except Exception as e:
        return {"blocks": [], "page_count": 0, "confidence_score": 0.0, "error": str(e)}

    # Simple OCR anomaly check: if no text from layout but pages exist
    if page_count > 0 and len(blocks) == 0:
        confidence = 0.1 # Likely a scanned PDF without text layer
        
    raw_text = "\n".join([b["text"] for b in blocks])
    logger.debug("RAW_PDF_TEXT_START")
    logger.debug(raw_text)
    logger.debug("RAW_PDF_TEXT_END")
        
    return {
        "blocks": blocks,
        "page_count": page_count,
        "confidence_score": confidence
    }
