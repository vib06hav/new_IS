import fitz

doc = fitz.open('Output PDF/Dummy App (5)_v5.pdf')
total = 0
for page in doc:
    for d in page.get_drawings():
        if "f" in d.get("type", ""):
            fill = d.get("fill")
            if fill and all(c < 0.1 for c in fill):
                rect = d["rect"]
                if rect.width > 2.0 and rect.height > 2.0:
                    total += 1
                    print(f"Page {page.number}: ({rect.x0:.1f}, {rect.y0:.1f}, {rect.x1:.1f}, {rect.y1:.1f}) W={rect.width:.1f} H={rect.height:.1f}")
print(f"\nTotal surviving black boxes: {total}")
