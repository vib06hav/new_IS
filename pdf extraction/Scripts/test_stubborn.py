import fitz

def test_stubborn(input_path):
    """Strip black boxes WITHOUT white fill, then count survivors."""
    print(f"\n--- Testing: {input_path} ---")
    
    doc = fitz.open(input_path)
    
    # Count originals first
    orig_count = 0
    for page in doc:
        page.clean_contents()
        for d in page.get_drawings():
            if "f" in d.get("type", ""):
                fill = d.get("fill")
                if fill and all(c < 0.1 for c in fill):
                    rect = d["rect"]
                    if rect.width > 2.0 and rect.height > 2.0:
                        orig_count += 1
    doc.close()
    
    # Now strip WITHOUT white fill
    doc = fitz.open(input_path)
    for page in doc:
        page.clean_contents()
        boxes = []
        for d in page.get_drawings():
            if "f" in d.get("type", ""):
                fill = d.get("fill")
                if fill and all(c < 0.1 for c in fill):
                    rect = d["rect"]
                    if rect.width > 2.0 and rect.height > 2.0:
                        page.add_redact_annot(rect)  # NO fill parameter
                        boxes.append(rect)
        if boxes:
            page.apply_redactions(images=0, graphics=1, text=1)
    
    # Save to temp, reopen, count survivors
    temp = "_test_stubborn.pdf"
    doc.save(temp)
    doc.close()
    
    doc = fitz.open(temp)
    survivors = []
    for page in doc:
        page.clean_contents()
        for d in page.get_drawings():
            if "f" in d.get("type", ""):
                fill = d.get("fill")
                if fill and all(c < 0.1 for c in fill):
                    rect = d["rect"]
                    if rect.width > 2.0 and rect.height > 2.0:
                        survivors.append((page.number, rect))
    doc.close()
    
    import os
    if os.path.exists(temp):
        os.remove(temp)
    
    print(f"  Original black boxes:  {orig_count}")
    print(f"  Survivors after strip: {len(survivors)}")
    for pn, r in survivors:
        print(f"    Page {pn}: ({r.x0:.1f}, {r.y0:.1f}, {r.x1:.1f}, {r.y1:.1f}) W={r.width:.1f} H={r.height:.1f}")
    
    return orig_count, len(survivors)


# Test on multiple PDFs
results = []
for i in [3, 5, 1, 7, 10]:
    path = f"Original PDF/Dummy App ({i}).pdf"
    try:
        orig, surv = test_stubborn(path)
        results.append((i, orig, surv))
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append((i, -1, -1))

print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)
for i, orig, surv in results:
    status = "CLEAN" if surv == 0 else f"STUBBORN ({surv})"
    print(f"  Dummy App ({i:2d}): {orig:3d} boxes -> {surv:3d} survivors  [{status}]")
