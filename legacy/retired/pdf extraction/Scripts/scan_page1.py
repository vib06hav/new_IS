from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
import fitz

doc = fitz.open('Original PDF/Dummy App (3).pdf')
ph = doc[1].rect.height
doc.close()

with open('Dumps/page1_labels.txt', 'w', encoding='utf-8') as f:
    for page_layout in extract_pages('Original PDF/Dummy App (3).pdf'):
        if page_layout.pageid - 1 != 1:
            continue
        texts = []
        for el in page_layout:
            if isinstance(el, LTTextContainer):
                t = el.get_text().strip().replace('\n', ' ')
                if t:
                    y0 = ph - el.y1
                    texts.append((y0, el.x0, t[:60]))
        texts.sort()
        for y, x, t in texts:
            if y < 320:
                f.write(f'Y={y:6.1f} X={x:6.1f} {t}\n')

print("Done")
