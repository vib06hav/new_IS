import fitz

def check(path, label, f):
    f.write(f"\n=== {label}: {path} ===\n")
    doc = fitz.open(path)
    page = doc[5]
    d_objs = page.get_drawings()
    count = 0
    for d in d_objs:
        for item in d['items']:
            if item[0] in ('l', 're'):
                rect = d['rect']
                y_center = (rect.y0 + rect.y1) / 2
                if 220 < y_center < 380:
                    item_type = item[0]
                    if item_type == 'l':
                        p1, p2 = item[1], item[2]
                        details = f"L: ({p1.x:.1f}, {p1.y:.1f}) -> ({p2.x:.1f}, {p2.y:.1f})"
                    else:
                        r = item[1]
                        details = f"R: {r}"
                    
                    f.write(f"  {details} | color={d.get('color')} | fill={d.get('fill')} | width={d.get('width')}\n")
                    count += 1
    f.write(f"Found {count} items in range.\n")

with open('Dumps/geometry_dump.txt', 'w', encoding='utf-8') as f:
    check('Original PDF/Dummy App (5).pdf', 'ORIGINAL', f)
    check('Output PDF/Dummy App (5)_memory_healed.pdf', 'HEALED', f)
