import sys
import os
import fitz

# V5 - Iterative stripping + memory-based healing
# Runs multiple strip passes until ALL black boxes are gone

HEAL_COLOR = (0, 0, 0)
HEAL_WIDTH = 0.5

def find_black_boxes(doc, color_threshold=0.1, min_dim=2.0):
    """Find all black-filled rectangles across all pages."""
    results = []  # (page_number, fitz.Rect)
    for page in doc:
        for d in page.get_drawings():
            if "f" in d.get("type", ""):
                fill = d.get("fill")
                if fill and all(c < color_threshold for c in fill):
                    rect = d["rect"]
                    if rect.width > min_dim and rect.height > min_dim:
                        results.append((page.number, fitz.Rect(rect)))
    return results


def strip_pass(doc, color_threshold=0.1, min_dim=2.0):
    """Run one stripping pass. Returns list of (page_num, rect) for memory."""
    memory = []
    total = 0
    for page in doc:
        boxes = []
        for d in page.get_drawings():
            if "f" in d.get("type", ""):
                fill = d.get("fill")
                if fill and all(c < color_threshold for c in fill):
                    rect = d["rect"]
                    if rect.width > min_dim and rect.height > min_dim:
                        page.add_redact_annot(rect)
                        boxes.append(fitz.Rect(rect))
        
        if boxes:
            page.apply_redactions(images=0, graphics=1, text=1)
            memory.extend([(page.number, r) for r in boxes])
            total += len(boxes)
    
    return memory, total


def process_pdf(input_path, output_path, color_threshold=0.1, min_dim=2.0, vert_leak_cap=30.0):
    print(f"--- Processing {input_path} (V5 Iterative) ---")
    
    all_memory = []
    
    # PHASE 1: ITERATIVE STRIPPING
    # Keep stripping until no more black boxes remain
    current_path = input_path
    pass_num = 0
    total_removed = 0
    
    while True:
        pass_num += 1
        doc = fitz.open(current_path)
        
        # Check how many boxes exist
        remaining = find_black_boxes(doc, color_threshold, min_dim)
        print(f"  Pass {pass_num}: Found {len(remaining)} black boxes")
        
        if len(remaining) == 0:
            doc.close()
            break
        
        # Strip them
        memory, count = strip_pass(doc, color_threshold, min_dim)
        all_memory.extend(memory)
        total_removed += count
        
        # Save to temp and reopen for next pass
        temp = f"_temp_pass_{pass_num}.pdf"
        doc.save(temp)
        doc.close()
        
        # Clean up previous temp
        if current_path != input_path and os.path.exists(current_path):
            os.remove(current_path)
        current_path = temp
        
        # Safety valve
        if pass_num > 10:
            print("  WARNING: Hit max passes, some boxes may remain")
            break
    
    print(f"  -> Total destroyed across {pass_num} passes: {total_removed}")
    
    # PHASE 2: HEAL BROKEN TABLE LINES USING ACCUMULATED MEMORY
    doc = fitz.open(current_path)
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
    
    # Cleanup remaining temp
    if current_path != input_path and os.path.exists(current_path):
        os.remove(current_path)
        
    # VERIFY: Check for any surviving blacks
    doc = fitz.open(output_path)
    survivors = find_black_boxes(doc, color_threshold, min_dim)
    doc.close()
    
    if survivors:
        print(f"  !! WARNING: {len(survivors)} black boxes still survive!")
        for pn, r in survivors:
            print(f"     Page {pn}: ({r.x0:.1f}, {r.y0:.1f}, {r.x1:.1f}, {r.y1:.1f})")
    else:
        print(f"  -> VERIFIED: Zero black boxes remain!")
    
    print(f"  -> Saved: {output_path}\n")


if __name__ == '__main__':
    if len(sys.argv) > 2:
        process_pdf(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python clean_and_heal_v5.py <input.pdf> <output.pdf>")
