import sys
import fitz
import re

def strip_black_boxes(pdf_path, output_path):
    print(f"Processing {pdf_path} to physically strip black boxes from the stream without touching table lines...")
    doc = fitz.open(pdf_path)
    
    # In PyMuPDF cleaned streams, a filled black rectangle is almost always:
    # 0 0 0 rg
    # x y w h re
    # f (or some variant of fill)
    #
    # Crucially, table lines use `S` (stroke) or `B` (fill and stroke) but usually just `S`
    # We want to delete the `re` path IF AND ONLY IF it is followed by `f` (fill) and preceded by `0 0 0 rg` (black).
    # Small redaction boxes might just be width > 5, height > 8. Table lines are width < 2 or height < 2.
    
    for page in doc:
        page.clean_contents()
        xref = page.get_contents()[0]
        stream = doc.xref_stream(xref).decode("latin-1")
        
        def replacer(match):
            w = float(match.group(1))
            h = float(match.group(2))
            
            # Table lines drawn as rectangles usually have one dimension very small (e.g. w=0.5 or h=0.5)
            # Real redaction boxes will be at least a few points wide and tall.
            # State/District redactions are usually around 10-15 pts high and 20-50 pts wide.
            if w > 2.0 and h > 2.0:
                print(f"Stripped rectangle {w}x{h}")
                return b"" # remove
            return match.group(0) # keep (it's a line/stroke masquerading as a tiny filled rect)
            
        # We need to flexibly match the fill operator. It might be just `f`, `f*`, `B`, `b` etc.
        # But commonly for redactions, it's `f` or `f*`.
        # Also need to handle multiple `re` commands before an `f`.
        # This is tricky with simple regex because a single `0 0 0 rg` might apply to many `re` before an `f`.
        # 
        # Better heuristic: just look for `w h re` and if they are big enough AND we know they are black fills...
        # Actually, let's just wipe large rectangles regardless of color if they are fills, 
        # because the ONLY large filled rectangles in this document are redactions or the background (which is white, but often just a single massive box that we can ignore or safely delete).
        # Wait, deleting the background white box might turn the PDF transparent, which is fine for pdfminer.
        
        # New regex: match any `w h re` directly followed by `W* f* 0` or similar fill commands, or just within a fill block.
        # Let's stick to the relatively safe black-only regex, but make it handle multiple `re` commands by splitting the stream.
        pass

    # Instead of brittle regex on the stream, let's use PyMuPDF's redaction feature again,
    # BUT we will use the `graphics=fitz.PDF_REDACT_GRAPHICS_REMOVE` equivalent (which strips from stream)
    # Oh wait, we had an AttributeError on that in the previous run because of the PyMuPDF version (or missing constants).
    
    print("Checking fitz redaction constants...")
    for k in dir(fitz):
        if 'REDACT' in k:
            print(k, getattr(fitz, k))

if __name__ == '__main__':
    strip_black_boxes(sys.argv[1], sys.argv[2])
