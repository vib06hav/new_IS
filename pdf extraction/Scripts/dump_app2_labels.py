from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
import fitz

pdf_path = 'Original PDF/Dummy App (2).pdf'
doc = fitz.open(pdf_path)
page_heights = {p.number: p.rect.height for p in doc}
doc.close()

with open('Dumps/app2_full_labels.txt', 'w', encoding='utf-8') as f:
    for page_layout in extract_pages(pdf_path):
        page_num = page_layout.pageid - 1
        page_h = page_heights.get(page_num, 841.89)
        f.write(f"\n--- Page {page_num} ---\n")
        texts = []
        for el in page_layout:
            if isinstance(el, LTTextContainer):
                t = el.get_text().strip().replace('\n', ' ')
                if t:
                    y0 = page_h - el.y1
                    texts.append((y0, el.x0, t[:80]))
        texts.sort()
        for y, x, t in texts:
            f.write(f"Y={y:6.1f} X={x:6.1f} {t}\n")

print("Done")
