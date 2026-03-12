import fitz
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

doc = fitz.open('Original PDF/Dummy App (3).pdf')
page_heights = {p.number: p.rect.height for p in doc}
doc.close()

large_boxes = [
    (0, 0, 188.3, 9.3, 569.4, 182.8, "Personal Details"),
    (1, 0, 299.0, 209.2, 440.8, 396.7, "Father details"),
    (2, 0, 299.8, 416.0, 404.4, 605.9, "Mother details"),
    (3, 1, 299.0, 307.6, 409.1, 490.4, "Sibling/address"),
    (4, 1, 299.8, 676.6, 541.5, 805.2, "Address cont"),
]

with open('Dumps/large_box_context.txt', 'w', encoding='utf-8') as f:
    for page_layout in extract_pages('Original PDF/Dummy App (3).pdf'):
        page_num = page_layout.pageid - 1
        page_h = page_heights.get(page_num, 841.89)
        
        page_texts = []
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                text = element.get_text().strip().replace('\n', ' ')
                if text:
                    pm_y0 = page_h - element.y1
                    pm_y1 = page_h - element.y0
                    page_texts.append((element.x0, pm_y0, element.x1, pm_y1, text))
        
        for box_idx, pn, bx0, by0, bx1, by1, desc in large_boxes:
            if pn != page_num:
                continue
            
            f.write(f"\n{'='*70}\nBox {box_idx}: {desc} | ({bx0:.0f},{by0:.0f})->({bx1:.0f},{by1:.0f})\n{'='*70}\n")
            
            # Find text with Y overlap with the box (same horizontal band)
            # but ANY X position (including far left labels)
            relevant = []
            for tx0, ty0, tx1, ty1, text in page_texts:
                # Y range must overlap with box Y range (with small margin)
                if ty1 > by0 - 5 and ty0 < by1 + 5:
                    relevant.append((ty0, tx0, tx1, ty1, text[:80]))
            
            relevant.sort()
            for ty, tx0, tx1, ty1, text in relevant:
                marker = ">>>" if tx0 < bx0 else "   "
                f.write(f"  {marker} Y={ty:6.1f} X=({tx0:6.1f}-{tx1:6.1f}) {text}\n")

print("Done - check Dumps/large_box_context.txt")
