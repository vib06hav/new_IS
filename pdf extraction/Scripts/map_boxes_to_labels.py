import fitz
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar

# Step 1: Get all redaction box coordinates from the original PDF
print("=== REDACTION BOX COORDINATES (Original Dummy App 3) ===\n")
doc = fitz.open('Original PDF/Dummy App (3).pdf')
boxes = []
for page in doc:
    page.clean_contents()
    for d in page.get_drawings():
        if "f" in d.get("type", ""):
            fill = d.get("fill")
            if fill and all(c < 0.1 for c in fill):
                rect = d["rect"]
                if rect.width > 2.0 and rect.height > 2.0:
                    boxes.append((page.number, rect.x0, rect.y0, rect.x1, rect.y1, rect.width, rect.height))
doc.close()

for i, (pn, x0, y0, x1, y1, w, h) in enumerate(boxes):
    print(f"Box {i:2d} | Page {pn} | ({x0:6.1f}, {y0:6.1f}) -> ({x1:6.1f}, {y1:6.1f}) | {w:5.1f} x {h:5.1f}")

# Step 2: Get all text labels and their coordinates from the original PDF
print("\n\n=== TEXT LABELS NEAR REDACTION BOXES ===\n")

# pdfminer uses bottom-left origin, PyMuPDF uses top-left origin
# We need the page height to convert

doc = fitz.open('Original PDF/Dummy App (3).pdf')
page_heights = {}
for page in doc:
    page_heights[page.number] = page.rect.height
doc.close()

# Extract text with coordinates
for page_layout in extract_pages('Original PDF/Dummy App (3).pdf'):
    page_num = page_layout.pageid - 1  # 0-indexed
    page_h = page_heights.get(page_num, 841.89)
    
    # Get boxes on this page
    page_boxes = [(i, x0, y0, x1, y1) for i, (pn, x0, y0, x1, y1, w, h) in enumerate(boxes) if pn == page_num]
    
    if not page_boxes:
        continue
    
    print(f"\n--- Page {page_num} ---")
    
    # Collect all text elements
    texts = []
    for element in page_layout:
        if isinstance(element, LTTextContainer):
            text = element.get_text().strip()
            if text:
                # Convert pdfminer coords (bottom-left) to PyMuPDF coords (top-left)
                pm_y0 = page_h - element.y1  # top in PyMuPDF space
                pm_y1 = page_h - element.y0  # bottom in PyMuPDF space
                texts.append((element.x0, pm_y0, element.x1, pm_y1, text))
    
    # For each box, find nearest text labels
    for box_idx, bx0, by0, bx1, by1 in page_boxes:
        print(f"\n  Box {box_idx}: ({bx0:.1f}, {by0:.1f}) -> ({bx1:.1f}, {by1:.1f})")
        
        nearby = []
        for tx0, ty0, tx1, ty1, text in texts:
            # Check if text is to the left, above, or overlapping with the box
            # within a generous tolerance
            dx = 0
            dy = 0
            
            # Horizontal distance
            if tx1 < bx0:
                dx = bx0 - tx1  # text is to the left
            elif tx0 > bx1:
                dx = tx0 - bx1  # text is to the right
            
            # Vertical overlap/distance
            if ty1 < by0:
                dy = by0 - ty1  # text is above
            elif ty0 > by1:
                dy = ty0 - by1  # text is below
            
            dist = (dx**2 + dy**2)**0.5
            
            if dist < 100:  # within 100 points
                nearby.append((dist, text[:60], tx0, ty0))
        
        nearby.sort()
        for dist, text, tx, ty in nearby[:5]:
            direction = ""
            if tx + 50 < bx0:
                direction = "LEFT"
            elif tx > bx1 - 10:
                direction = "RIGHT"
            elif ty + 20 < by0:
                direction = "ABOVE"
            else:
                direction = "OVERLAP/SAME_ROW"
            print(f"    [{dist:5.1f}] {direction:15s} \"{text}\"")
