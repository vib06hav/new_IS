import fitz
doc = fitz.open('Output PDF/Dummy App (5)_memory_healed.pdf')
page = doc[5]
for d in page.get_drawings():
    for item in d['items']:
        if item[0] == 'l':
            p1, p2 = item[1], item[2]
            if abs(p1.y - p2.y) < 1.0 and 270 < p1.y < 350:
                print(f'Y={p1.y:.2f}, X={min(p1.x, p2.x):.2f} to {max(p1.x, p2.x):.2f}, color={d.get("color")}')
