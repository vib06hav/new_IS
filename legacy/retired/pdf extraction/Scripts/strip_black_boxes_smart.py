import sys
import fitz

def strip_black_boxes_smart(pdf_path, output_path):
    print(f"Processing {pdf_path} to remove redactions and preserve grids...")
    doc = fitz.open(pdf_path)
    
    total_removed = 0
    for page in doc:
        drawings = page.get_drawings()
        boxes_removed = 0
        for d in drawings:
            if "f" in d["type"]:
                fill_color = d.get("fill")
                if fill_color and all(c < 0.1 for c in fill_color):
                    rect = d["rect"]
                    
                    # Smallest redaction box might just be a small cell, but table lines are usually < 2 pts thick.
                    if rect.width > 2.0 and rect.height > 2.0:
                        page.add_redact_annot(rect, fill=(1, 1, 1))
                        boxes_removed += 1

        if boxes_removed > 0:
            print(f"Applying {boxes_removed} redactions on page {page.number}...")
            # 1 = PDF_REDACT_LINE_ART_REMOVE
            page.apply_redactions(images=0, graphics=1, text=1)
            total_removed += boxes_removed

    doc.save(output_path)
    print(f"Saved clean PDF to {output_path} (Removed {total_removed} boxes)")

if __name__ == '__main__':
    strip_black_boxes_smart(sys.argv[1], sys.argv[2])
