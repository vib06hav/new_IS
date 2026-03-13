import fitz
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def get_vertical_lines(pdf_path: str, page_num: int, y_min_pdf: float, y_max_pdf: float) -> List[float]:
    """
    Finds vertical grid lines (table dividers) within a specific vertical range on a page.
    """
    v_lines = []
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_num - 1]
        height = page.rect.height
        
        y_top_fitz = height - y_max_pdf
        y_bottom_fitz = height - y_min_pdf
        
        drawings = page.get_drawings()
        for d in drawings:
            # Check if the drawing overlaps with our vertical range
            # We use a generous overlap check
            rect = d.get("rect")
            if not rect:
                continue
                
            # If drawing is entirely above or entirely below, skip
            if rect.y1 < y_top_fitz - 5 or rect.y0 > y_bottom_fitz + 5:
                continue
                
            for item in d.get("items", []):
                if item[0] == "l": # line
                    p1, p2 = item[1], item[2]
                    # Vertical lines
                    if abs(p1.x - p2.x) < 2:
                        # Ensure the line itself covers at least some of our range
                        l_y_min = min(p1.y, p2.y)
                        l_y_max = max(p1.y, p2.y)
                        # Does this line exist within our y-range?
                        if not (l_y_max < y_top_fitz or l_y_min > y_bottom_fitz):
                            v_lines.append(p1.x)
                elif item[0] == "re": # rect
                    r = item[1]
                    if r.width < 5:
                        if not (r.y1 < y_top_fitz or r.y0 > y_bottom_fitz):
                            v_lines.append(r.x0)
                            v_lines.append(r.x1)
        doc.close()
    except Exception as e:
        logger.error(f"Error extracting grid lines: {e}")
        return []

    if not v_lines:
        return []
        
    v_lines.sort()
    unique_lines = []
    if v_lines:
        unique_lines.append(v_lines[0])
        for x in v_lines[1:]:
            # Use a slightly larger clustering threshold
            if x - unique_lines[-1] > 1.5:
                unique_lines.append(x)
    
    return [round(x, 2) for x in unique_lines]

def get_page_heights(pdf_path: str) -> Dict[int, float]:
    """
    Returns a dictionary mapping 1-indexed page numbers to their heights.
    """
    heights = {}
    try:
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):
            heights[i + 1] = float(page.rect.height)
        doc.close()
    except Exception as e:
        logger.error(f"Error getting page heights: {e}")
    return heights
