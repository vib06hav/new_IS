import sys
import os
import fitz

def process_pdf(input_path, output_path):
    print(f"--- Processing {input_path} ---")
    doc = fitz.open(input_path)
    
    # PHASE 1: REMOVE REDACTION BOXES (BLACK FILLS)
    total_removed = 0
    for page in doc:
        drawings = page.get_drawings()
        boxes_removed = 0
        for d in drawings:
            if "f" in d["type"]:
                fill_color = d.get("fill")
                if fill_color and all(c < 0.1 for c in fill_color):
                    rect = d["rect"]
                    # Redaction boxes are generally >= 2.0 layout points.
                    # Table borders (if drawn as thin rectangles) are typically < 1.0 points.
                    if rect.width > 2.0 and rect.height > 2.0:
                        page.add_redact_annot(rect, fill=(1, 1, 1))
                        boxes_removed += 1

        if boxes_removed > 0:
            print(f"  Page {page.number}: Removing {boxes_removed} redaction boxes...")
            page.apply_redactions(images=0, graphics=1, text=1)
            total_removed += boxes_removed
            
    print(f"  -> Total redaction boxes completely destroyed: {total_removed}")

    # The document must be saved and reopened because the drawing paths are completely 
    # re-evaluated and reconstructed after a graphics-removal redaction.
    temp_path = "temp_stripped.pdf"
    doc.save(temp_path)
    doc.close()
    
    # PHASE 2: HEAL BROKEN TABLE LINES
    doc = fitz.open(temp_path)
    total_h = 0
    total_v = 0
    
    for page in doc:
        drawings = page.get_drawings()
        horiz_lines = []
        vert_lines = []
        
        for d in drawings:
            if "s" in d.get("type", "") or "f" in d.get("type", ""):
                for item in d["items"]:
                    if item[0] == "l": 
                        p1, p2 = item[1], item[2]
                        if abs(p1.y - p2.y) < 1.0:
                            horiz_lines.append(((p1.y + p2.y) / 2, min(p1.x, p2.x), max(p1.x, p2.x), d.get("color", (0,0,0)), d.get("width", 0.5)))
                        elif abs(p1.x - p2.x) < 1.0:
                            vert_lines.append(((p1.x + p2.x) / 2, min(p1.y, p2.y), max(p1.y, p2.y), d.get("color", (0,0,0)), d.get("width", 0.5)))
                    
                    elif item[0] == "re": 
                        rect = item[1]
                        if rect.height < 2.0:
                            horiz_lines.append((rect.y0 + rect.height / 2, rect.x0, rect.x1, d.get("color", (0,0,0)), d.get("width", 0.5) or rect.height))
                        elif rect.width < 2.0:
                            vert_lines.append((rect.x0 + rect.width / 2, rect.y0, rect.y1, d.get("color", (0,0,0)), d.get("width", 0.5) or rect.width))
        
        # HEAL HORIZONTAL LINES
        horiz_lines.sort(key=lambda x: x[0]) 
        h_groups = []
        for line in horiz_lines:
            placed = False
            for g in h_groups:
                if abs(g["coord"] - line[0]) < 1.5:
                    g["lines"].append(line)
                    placed = True
                    break
            if not placed:
                h_groups.append({"coord": line[0], "lines": [line]})
                
        for g in h_groups:
            y = g["coord"]
            lines_in_group = sorted(g["lines"], key=lambda x: x[1]) 
            for i in range(len(lines_in_group) - 1):
                gap_start = lines_in_group[i][2] 
                gap_end = lines_in_group[i+1][1]   
                gap_width = gap_end - gap_start
                # Only bridge reasonable structural gaps
                if 2.0 < gap_width < 400.0:
                    page.draw_line(fitz.Point(gap_start, y), fitz.Point(gap_end, y), color=lines_in_group[i][3], width=lines_in_group[i][4])
                    total_h += 1

        # HEAL VERTICAL LINES
        vert_lines.sort(key=lambda x: x[0])
        v_groups = []
        for line in vert_lines:
            placed = False
            for g in v_groups:
                if abs(g["coord"] - line[0]) < 1.5:
                    g["lines"].append(line)
                    placed = True
                    break
            if not placed:
                v_groups.append({"coord": line[0], "lines": [line]})
                
        for g in v_groups:
            x = g["coord"]
            lines_in_group = sorted(g["lines"], key=lambda x: x[1])
            for i in range(len(lines_in_group) - 1):
                gap_start = lines_in_group[i][2]
                gap_end = lines_in_group[i+1][1]
                gap_height = gap_end - gap_start
                if 2.0 < gap_height < 300.0:
                    page.draw_line(fitz.Point(x, gap_start), fitz.Point(x, gap_end), color=lines_in_group[i][3], width=lines_in_group[i][4])
                    total_v += 1

    print(f"  -> Regenerated {total_h} broken horizontal borders and {total_v} broken vertical borders.")
    doc.save(output_path)
    doc.close()
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    print(f"  -> Structure perfectly restored into {output_path}!\n")

if __name__ == '__main__':
    if len(sys.argv) > 2:
        process_pdf(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python clean_and_heal.py <input.pdf> <output.pdf>")
