import fitz

# Check what black boxes survived the stripping in the V3 output
doc = fitz.open('Output PDF/Dummy App (5)_A_strict.pdf')

with open('Dumps/surviving_blacks.txt', 'w', encoding='utf-8') as f:
    for page in doc:
        f.write(f"\n=== Page {page.number} ===\n")
        drawings = page.get_drawings()
        count = 0
        for d in drawings:
            if "f" in d.get("type", ""):
                fill = d.get("fill")
                if fill and all(c < 0.1 for c in fill):
                    rect = d["rect"]
                    if rect.width > 2.0 and rect.height > 2.0:
                        count += 1
                        f.write(f"  SURVIVING BLACK: Rect({rect.x0:.1f}, {rect.y0:.1f}, {rect.x1:.1f}, {rect.y1:.1f}) "
                                f"W={rect.width:.1f} H={rect.height:.1f}\n")
        f.write(f"  Total surviving: {count}\n")

print("Done - check Dumps/surviving_blacks.txt")
