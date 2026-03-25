import fitz

doc = fitz.open('Original PDF/Dummy App (5).pdf')

with open('Dumps/fill_diagnostic.txt', 'w', encoding='utf-8') as f:
    for page in doc:
        f.write(f"\n=== Page {page.number} ===\n")
        drawings = page.get_drawings()
        for d in drawings:
            if "f" in d.get("type", ""):
                fill = d.get("fill")
                rect = d["rect"]
                w, h = rect.width, rect.height
                if w > 2.0 and h > 2.0:
                    f.write(f"  Rect({rect.x0:.1f}, {rect.y0:.1f}, {rect.x1:.1f}, {rect.y1:.1f}) "
                            f"W={w:.1f} H={h:.1f} fill={fill} color={d.get('color')}\n")

print("Done - check Dumps/fill_diagnostic.txt")
