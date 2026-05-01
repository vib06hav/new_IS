import sys
import os
import fitz

# V3 - Robust Table Geometry Restoration
# Fixes: invisible (white) lines, duplicate lines, white-box occlusion

# Standard line properties for all healed lines
HEAL_COLOR = (0, 0, 0)  # Solid black
HEAL_WIDTH = 0.5         # Thin, matching original table strokes

def process_pdf_smart(input_path, output_path):
    print(f"--- Processing {input_path} with Bounding Box Memory (V3) ---")
    doc = fitz.open(input_path)
    
    # =========================================================================
    # PHASE 1: COLLECT MEMORY & CLEAN
    # =========================================================================
    memory = []  # Store tuple of (page_num, fitz.Rect)
    total_removed = 0
    
    for page in doc:
        drawings = page.get_drawings()
        boxes_on_page = []
        for d in drawings:
            if "f" in d["type"]:
                fill_color = d.get("fill")
                if fill_color and all(c < 0.1 for c in fill_color):
                    rect = d["rect"]
                    if rect.width > 2.0 and rect.height > 2.0:
                        # V3 FIX: Do NOT fill with white. Use no fill so the
                        # white rectangle doesn't occlude our healed lines later.
                        page.add_redact_annot(rect)
                        boxes_on_page.append(fitz.Rect(rect))
                        
        if boxes_on_page:
            memory.extend([(page.number, r) for r in boxes_on_page])
            print(f"  Page {page.number}: Saving boundaries for {len(boxes_on_page)} boxes & removing...")
            # graphics=1 = PDF_REDACT_LINE_ART_REMOVE (deep stream removal)
            page.apply_redactions(images=0, graphics=1, text=1)
            total_removed += len(boxes_on_page)
            
    print(f"  -> Total redaction boxes destroyed: {total_removed}")

    temp_path = output_path + ".tmp.pdf"
    doc.save(temp_path)
    doc.close()
    
    # =========================================================================
    # PHASE 2: HEAL BROKEN TABLE LINES USING MEMORY
    # =========================================================================
    doc = fitz.open(temp_path)
    total_h = 0
    total_v = 0
    
    # Group memory by page
    page_memory = {}
    for p_num, rect in memory:
        if p_num not in page_memory:
            page_memory[p_num] = []
        page_memory[p_num].append(rect)
        
    for page in doc:
        if page.number not in page_memory:
            continue
            
        redaction_boxes = page_memory[page.number]
        drawings = page.get_drawings()
        
        # Collect all horizontal and vertical line segments on this page
        horiz_lines = []  # (y, xmin, xmax)
        vert_lines = []   # (x, ymin, ymax)
        
        for d in drawings:
            dtype = d.get("type", "")
            if "s" not in dtype and "f" not in dtype:
                continue
            for item in d["items"]:
                if item[0] == "l": 
                    p1, p2 = item[1], item[2]
                    if abs(p1.y - p2.y) < 1.0:
                        horiz_lines.append(((p1.y + p2.y) / 2, min(p1.x, p2.x), max(p1.x, p2.x)))
                    elif abs(p1.x - p2.x) < 1.0:
                        vert_lines.append(((p1.x + p2.x) / 2, min(p1.y, p2.y), max(p1.y, p2.y)))
                elif item[0] == "re": 
                    rect = item[1]
                    if rect.height < 2.0 and rect.width > 2.0:
                        horiz_lines.append((rect.y0 + rect.height / 2, rect.x0, rect.x1))
                    elif rect.width < 2.0 and rect.height > 2.0:
                        vert_lines.append((rect.x0 + rect.width / 2, rect.y0, rect.y1))
        
        # V3 FIX: Deduplication set - track what we've drawn to avoid double-striking
        drawn_lines = set()  # Store rounded tuples: ("H", round(y,1), round(x0,1), round(x1,1))
        
        def draw_h_line(y, x0, x1):
            key = ("H", round(y, 1), round(x0, 1), round(x1, 1))
            if key in drawn_lines:
                return False
            drawn_lines.add(key)
            page.draw_line(fitz.Point(x0, y), fitz.Point(x1, y), color=HEAL_COLOR, width=HEAL_WIDTH)
            return True
        
        def draw_v_line(x, y0, y1):
            key = ("V", round(x, 1), round(y0, 1), round(y1, 1))
            if key in drawn_lines:
                return False
            drawn_lines.add(key)
            page.draw_line(fitz.Point(x, y0), fitz.Point(x, y1), color=HEAL_COLOR, width=HEAL_WIDTH)
            return True
        
        # Now, heal only using memory boxes
        for orig_rect in redaction_boxes:
            box_x0 = orig_rect.x0
            box_y0 = orig_rect.y0
            box_x1 = orig_rect.x1
            box_y1 = orig_rect.y1
            
            # -----------------------------------------------------------------
            # HEAL HORIZONTAL LINES
            # -----------------------------------------------------------------
            # Find horizontal lines whose Y sits within the box's vertical range
            # AND whose X endpoint touches the left or right edge of the box.
            
            h_y_values = set()  # Collect unique Y values that need bridging
            
            for y, xmin, xmax in horiz_lines:
                if not (box_y0 - 3 <= y <= box_y1 + 3):
                    continue
                    
                # Does this line's right end touch the box's left edge?
                touches_left = abs(xmax - box_x0) < 5.0
                # Does this line's left end touch the box's right edge?
                touches_right = abs(xmin - box_x1) < 5.0
                
                if touches_left or touches_right:
                    # Round to 1 decimal to group nearly-identical Y values
                    h_y_values.add(round(y, 1))
            
            for y in h_y_values:
                if draw_h_line(y, box_x0, box_x1):
                    total_h += 1
            
            # -----------------------------------------------------------------
            # HEAL VERTICAL LINES
            # -----------------------------------------------------------------
            # Find vertical lines whose X sits within the box's horizontal range
            # AND whose Y endpoint touches the top or bottom edge of the box.
            
            v_x_values = set()  # Collect unique X values that need bridging
            
            for x, ymin, ymax in vert_lines:
                if not (box_x0 - 3 <= x <= box_x1 + 3):
                    continue
                
                # Does this line's bottom end touch the box's top edge?
                touches_top = abs(ymax - box_y0) < 5.0
                # Does this line's top end touch the box's bottom edge?
                touches_bottom = abs(ymin - box_y1) < 5.0
                
                if touches_top or touches_bottom:
                    v_x_values.add(round(x, 1))
            
            for x in v_x_values:
                if draw_v_line(x, box_y0, box_y1):
                    total_v += 1

    print(f"  -> Healed {total_h} horizontal borders and {total_v} vertical borders.")
    doc.save(output_path)
    doc.close()
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    print(f"  -> Output saved to {output_path}\n")

if __name__ == '__main__':
    if len(sys.argv) > 2:
        process_pdf_smart(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python clean_and_heal_memory.py <input.pdf> <output.pdf>")
