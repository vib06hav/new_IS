import fitz
import re

doc = fitz.open('Original PDF/Dummy App (5).pdf')

# Dump full content streams for pages 1 and 2 (where survivors live)
for pn in [1, 2]:
    page = doc[pn]
    stream = page.read_contents()
    text = stream.decode('latin-1', errors='replace')
    
    with open(f'Dumps/page{pn}_stream.txt', 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Page {pn}: stream dumped ({len(text)} chars)")

doc.close()
