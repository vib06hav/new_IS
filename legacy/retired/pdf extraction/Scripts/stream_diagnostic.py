import fitz
import re

doc = fitz.open('Original PDF/Dummy App (5).pdf')

with open('Dumps/stream_diagnostic.txt', 'w', encoding='utf-8') as f:
    for page in doc:
        f.write(f"\n=== Page {page.number} ===\n")
        
        # Get the raw content stream(s)
        xref = page.xref
        # A page can have multiple content streams
        stream = page.read_contents()
        if not stream:
            f.write("  No stream found\n")
            continue
            
        text = stream.decode('latin-1', errors='replace')
        
        # Find all rectangle fill operations
        # Pattern: x y w h re ... f (fill) or f* (fill even-odd)
        # The color is set before by "0 0 0 rg" (RGB) or "0 g" (gray)
        
        # Let's find ALL rect+fill sequences and their preceding color setting
        # Split stream into operations
        lines = text.split('\n')
        
        current_fill_color = None
        rect_count = 0
        black_rect_count = 0
        
        for line in lines:
            line = line.strip()
            
            # Check for color setting
            if line.endswith(' rg'):
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        r, g, b = float(parts[0]), float(parts[1]), float(parts[2])
                        current_fill_color = (r, g, b)
                    except:
                        pass
            elif line.endswith(' g') and not line.endswith('rg'):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        gray = float(parts[0])
                        current_fill_color = (gray, gray, gray)
                    except:
                        pass
            
            # Check for rectangle definition followed by fill
            # Sometimes it's on one line, sometimes split across lines
            if ' re' in line:
                rect_match = re.search(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+re', line)
                if rect_match:
                    x = float(rect_match.group(1))
                    y = float(rect_match.group(2))
                    w = float(rect_match.group(3))
                    h = float(rect_match.group(4))
                    rect_count += 1
                    
                    if current_fill_color and all(c < 0.1 for c in current_fill_color):
                        if abs(w) > 5 and abs(h) > 5:
                            black_rect_count += 1
                            f.write(f"  BLACK RECT: x={x:.1f} y={y:.1f} w={w:.1f} h={h:.1f} "
                                    f"fill={current_fill_color}\n")
        
        f.write(f"  Total rects in stream: {rect_count}\n")
        f.write(f"  Black filled rects (>5x5): {black_rect_count}\n")
        
        # Also count what get_drawings finds
        drawings = page.get_drawings()
        gd_black = 0
        for d in drawings:
            if "f" in d.get("type", ""):
                fill = d.get("fill")
                if fill and all(c < 0.1 for c in fill):
                    rect = d["rect"]
                    if rect.width > 5 and rect.height > 5:
                        gd_black += 1
        f.write(f"  get_drawings() black filled rects (>5x5): {gd_black}\n")

print("Done - check Dumps/stream_diagnostic.txt")
