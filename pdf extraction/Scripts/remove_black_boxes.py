import sys
import fitz

def remove_black_boxes(pdf_path, output_path):
    print(f"Processing {pdf_path} to remove black boxes...")
    doc = fitz.open(pdf_path)
    
    for page in doc:
        drawings = page.get_drawings()
        boxes_removed = 0
        for d in drawings:
            # Check if it's a fill
            if "f" in d["type"]:
                fill_color = d.get("fill")
                # Check if it's black (or very dark)
                if fill_color and all(c < 0.1 for c in fill_color):
                    rect = d["rect"]
                    # Check if it's a large box (area > some threshold, to avoid small lines)
                    if rect.width > 20 and rect.height > 20:
                        # Adding a redaction annotation
                        annot = page.add_redact_annot(rect, fill=(1, 1, 1)) # fill with white
                        annot.update()
                        boxes_removed += 1
        
        if boxes_removed > 0:
            print(f"Found {boxes_removed} large black boxes on page {page.number}. Applying redactions...")
            # Try applying with default which strips text and might strip underlying graphics depending on version
            page.apply_redactions()

    doc.save(output_path)
    print(f"Saved cleaned PDF to {output_path}")

if __name__ == '__main__':
    remove_black_boxes(sys.argv[1], sys.argv[2])
