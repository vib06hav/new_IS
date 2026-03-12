import fitz

for name in ['memory_healed', 'v3', 'A_strict', 'v7']:
    path = f'Output PDF/Dummy App (5)_{name}.pdf'
    try:
        doc = fitz.open(path)
        count = 0
        for page in doc:
            for d in page.get_drawings():
                if "f" in d.get("type", ""):
                    fill = d.get("fill")
                    if fill and all(c < 0.1 for c in fill):
                        rect = d["rect"]
                        if rect.width > 2.0 and rect.height > 2.0:
                            count += 1
        doc.close()
        print(f'{name:20s}: {count} black boxes remaining')
    except Exception as e:
        print(f'{name:20s}: ERROR - {e}')
