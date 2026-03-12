import fitz

def check(path, label):
    print(f"--- {label}: {path} ---")
    doc = fitz.open(path)
    page = doc[5]
    for d in page.get_drawings():
        # Look for horizontal shapes at Y around 277, 282, 309 (the row dividers)
        for item in d['items']:
            if item[0] == 'l':
                p1, p2 = item[1], item[2]
                y = (p1.y + p2.y) / 2
                if abs(p1.y - p2.y) < 1.0 and 270 < y < 350:
                    if min(p1.x, p2.x) < 100 or max(p1.x, p2.x) > 500: # Outer edges or long lines
                        print(f"  Line Y={y:.2f}, X={min(p1.x, p2.x):.2f}-{max(p1.x, p2.x):.2f}, color={d.get('color')}, fill={d.get('fill')}")
            elif item[0] == 're':
                r = item[1]
                y = (r.y0 + r.y1) / 2
                if r.height < 2.0 and 270 < y < 350:
                    print(f"  RectLine Y={y:.2f}, X={r.x0:.2f}-{r.x1:.2f}, color={d.get('color')}, fill={d.get('fill')}")

check('Original PDF/Dummy App (5).pdf', 'ORIGINAL')
check('Output PDF/Dummy App (5)_memory_healed.pdf', 'HEALED')
