import fitz

# Quick count of black fill boxes detected at each threshold
doc = fitz.open('Original PDF/Dummy App (5).pdf')

thresholds = [0.1, 0.2, 0.3]
for t in thresholds:
    count = 0
    for page in doc:
        for d in page.get_drawings():
            if "f" in d.get("type", ""):
                fill = d.get("fill")
                if fill and all(c < t for c in fill):
                    rect = d["rect"]
                    if rect.width > 2.0 and rect.height > 2.0:
                        count += 1
    print(f"Threshold < {t}: {count} boxes detected")
doc.close()
