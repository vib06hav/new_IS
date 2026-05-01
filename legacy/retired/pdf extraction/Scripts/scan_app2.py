import fitz
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

# Scan Dummy App (2) for box positions and nearby labels
pdf_path = 'Original PDF/Dummy App (2).pdf'
doc = fitz.open(pdf_path)
page_heights = {p.number: p.rect.height for p in doc}

# Get all boxes
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

output_path = 'Dumps/app2_mapping.txt'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write("=== BOX COORDINATES ===\n")
    for i, (pn, x0, y0, x1, y1, w, h) in enumerate(boxes):
        size = "LARGE" if w > 80 or h > 80 else "small"
        f.write(f"Box {i:2d} | Page {pn} | ({x0:6.1f}, {y0:6.1f}) -> ({x1:6.1f}, {y1:6.1f}) | {w:5.1f} x {h:5.1f} [{size}]\n")
    
    # Now scan labels near each box
    f.write("\n=== LABEL CONTEXT ===\n")
    
    for page_layout in extract_pages(pdf_path):
        page_num = page_layout.pageid - 1
        page_h = page_heights.get(page_num, 841.89)
        
        page_texts = []
        for el in page_layout:
            if isinstance(el, LTTextContainer):
                t = el.get_text().strip().replace('\n', ' ')
                if t:
                    pm_y0 = page_h - el.y1
                    page_texts.append((pm_y0, el.x0, el.x1, t[:60]))
        page_texts.sort()
        
        page_boxes = [(i, x0, y0, x1, y1) for i, (pn, x0, y0, x1, y1, w, h) in enumerate(boxes) if pn == page_num]
        if not page_boxes:
            continue
        
        f.write(f"\n--- Page {page_num} ---\n")
        
        for box_idx, bx0, by0, bx1, by1 in page_boxes:
            bw = bx1 - bx0
            bh = by1 - by0
            f.write(f"\n  Box {box_idx} ({bx0:.0f},{by0:.0f})->({bx1:.0f},{by1:.0f}) [{bw:.0f}x{bh:.0f}]\n")
            
            # Find text in the same Y band, especially to the LEFT
            for ty, tx0, tx1, text in page_texts:
                if ty > by0 - 5 and ty < by1 + 5 and tx0 < bx0:
                    f.write(f"    Y={ty:6.1f} X={tx0:6.1f} {text}\n")

print(f"Done - check {output_path}")
