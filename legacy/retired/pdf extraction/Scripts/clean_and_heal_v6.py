import sys
import os
import fitz

# V6 - Hybrid: apply_redactions for what it can handle + direct white overlay for survivors
# Also includes iterative checking and memory-based healing

HEAL_COLOR = (0, 0, 0)
HEAL_WIDTH = 0.5

def find_black_boxes(page, color_threshold=0.1, min_dim=2.0):
    """Find black-filled rectangles on a single page."""
    results = []
    for d in page.get_drawings():
        if "f" in d.get("type", ""):
            fill = d.get("fill")
            if fill and all(c < color_threshold for c in fill):
                rect = d["rect"]
                if rect.width > min_dim and rect.height > min_dim:
                    results.append(fitz.Rect(rect))
    return results


def process_pdf(input_path, output_path, color_threshold=0.1, min_dim=2.0, vert_leak_cap=30.0):
    print(f"--- Processing {input_path} (V6 Hybrid) ---")
    
    all_memory = []  # Accumulated (page_num, rect) across all passes
    
    # =========================================================================
    # PHASE 1: PRIMARY STRIPPING (apply_redactions)
    # =========================================================================
    doc = fitz.open(input_path)
    total_pass1 = 0
    
    for page in doc:
        boxes = find_black_boxes(page, color_threshold, min_dim)
        if boxes:
            for rect in boxes:
                page.add_redact_annot(rect)
                all_memory.append((page.number, rect))
            page.apply_redactions(images=0, graphics=1, text=1)
            total_pass1 += len(boxes)
    
    print(f"  Pass 1 (redaction): Removed {total_pass1} boxes")
    
    # Save and reopen to check survivors
    temp1 = output_path + ".tmp1.pdf"
    doc.save(temp1)
    doc.close()
    
    # =========================================================================
    # PHASE 2: SURVIVOR ELIMINATION (white overlay + content stream cleanup)
    # =========================================================================
    doc = fitz.open(temp1)
    total_pass2 = 0
    
    for page in doc:
        survivors = find_black_boxes(page, color_threshold, min_dim)
        if survivors:
            for rect in survivors:
                all_memory.append((page.number, rect))
                # Draw a white filled rectangle directly on top
                shape = page.new_shape()
                shape.draw_rect(rect)
                shape.finish(color=(1, 1, 1), fill=(1, 1, 1), width=0)
                shape.commit()
                total_pass2 += 1
            
            # Also try to clean up the underlying stream
            page.clean_contents()
    
    print(f"  Pass 2 (overlay): Covered {total_pass2} stubborn boxes")
    
    # Save temp for healing
    temp2 = output_path + ".tmp2.pdf"
    doc.save(temp2)
    doc.close()
    
    # Clean up temp1
    if os.path.exists(temp1):
        os.remove(temp1)
    
    # =========================================================================
    # PHASE 3: HEAL BROKEN TABLE LINES USING ACCUMULATED MEMORY
    # =========================================================================
    doc = fitz.open(temp2)
    total_h = 0
    total_v = 0
    
    page_memory = {}
    for p_num, rect in all_memory:
        if p_num not in page_memory:
            page_memory[p_num] = []
        page_memory[p_num].append(rect)
        
    for page in doc:
        if page.number not in page_memory:
            continue
            
        redaction_boxes = page_memory[page.number]
        drawings = page.get_drawings()
        
        horiz_lines = []
        vert_lines = []
        
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
        
        drawn_lines = set()
        
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
        
        for orig_rect in redaction_boxes:
            box_x0 = orig_rect.x0
            box_y0 = orig_rect.y0
            box_x1 = orig_rect.x1
            box_y1 = orig_rect.y1
            
            # HORIZONTAL HEALING
            h_y_values = set()
            for y, xmin, xmax in horiz_lines:
                if not (box_y0 - 3 <= y <= box_y1 + 3):
                    continue
                touches_left = abs(xmax - box_x0) < 5.0
                touches_right = abs(xmin - box_x1) < 5.0
                if touches_left or touches_right:
                    h_y_values.add(round(y, 1))
            
            for y in h_y_values:
                if draw_h_line(y, box_x0, box_x1):
                    total_h += 1
            
            # VERTICAL HEALING (with leak cap)
            v_x_values = set()
            for x, ymin, ymax in vert_lines:
                if not (box_x0 - 3 <= x <= box_x1 + 3):
                    continue
                touches_top = abs(ymax - box_y0) < 5.0
                touches_bottom = abs(ymin - box_y1) < 5.0
                if touches_top or touches_bottom:
                    v_x_values.add(round(x, 1))
            
            for x in v_x_values:
                draw_y0 = box_y0
                draw_y1 = box_y1
                if vert_leak_cap is not None and (box_y1 - box_y0) > vert_leak_cap:
                    closest_h_inside = [y for y, _, _ in horiz_lines if box_y0 <= y <= box_y1]
                    if closest_h_inside:
                        for vx, vymin, vymax in vert_lines:
                            if abs(vx - x) < 1.0:
                                if abs(vymax - box_y0) < 5.0:
                                    nearest_below = [h for h in closest_h_inside if h > box_y0]
                                    if nearest_below:
                                        draw_y1 = min(draw_y1, min(nearest_below) + vert_leak_cap)
                                elif abs(vymin - box_y1) < 5.0:
                                    nearest_above = [h for h in closest_h_inside if h < box_y1]
                                    if nearest_above:
                                        draw_y0 = max(draw_y0, max(nearest_above) - vert_leak_cap)
                                break
                
                if draw_v_line(x, draw_y0, draw_y1):
                    total_v += 1

    print(f"  -> Healed {total_h} H-borders, {total_v} V-borders")
    doc.save(output_path)
    doc.close()
    
    # Clean up temp2
    if os.path.exists(temp2):
        os.remove(temp2)
    
    # FINAL VERIFY: Check for visually remaining blacks
    doc = fitz.open(output_path)
    visible_survivors = 0
    for page in doc:
        for d in page.get_drawings():
            if "f" in d.get("type", ""):
                fill = d.get("fill")
                if fill and all(c < 0.1 for c in fill):
                    rect = d["rect"]
                    if rect.width > 2.0 and rect.height > 2.0:
                        visible_survivors += 1
    doc.close()
    
    print(f"  -> Remaining visually black boxes: {visible_survivors}")
    print(f"  -> Saved: {output_path}\n")


if __name__ == '__main__':
    if len(sys.argv) > 2:
        process_pdf(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python clean_and_heal_v6.py <input.pdf> <output.pdf>")
