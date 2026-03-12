import sys
import os
import fitz

# V4 - Multi-threshold batch generator with vertical leak fix
# Generates multiple PDFs with different settings for user comparison

HEAL_COLOR = (0, 0, 0)
HEAL_WIDTH = 0.5

def process_pdf(input_path, output_path, color_threshold=0.1, min_dimension=2.0, vert_leak_cap=None):
    """
    Process a PDF: remove black boxes and heal table lines.
    
    Args:
        color_threshold: Max RGB component value to consider "black" (0.1 = pure black only, 0.3 = dark gray too)
        min_dimension: Minimum width AND height to consider a rectangle a redaction box
        vert_leak_cap: Max height for vertical healing lines. None = use full box height.
                       Set to e.g. 30 to prevent tall vertical lines from leaking into adjacent tables.
    """
    label = f"thresh={color_threshold}, min_dim={min_dimension}, v_cap={vert_leak_cap}"
    print(f"\n--- Processing {input_path} [{label}] ---")
    doc = fitz.open(input_path)
    
    # PHASE 1: COLLECT MEMORY & CLEAN
    memory = []
    total_removed = 0
    
    for page in doc:
        drawings = page.get_drawings()
        boxes_on_page = []
        for d in drawings:
            if "f" in d["type"]:
                fill_color = d.get("fill")
                if fill_color and all(c < color_threshold for c in fill_color):
                    rect = d["rect"]
                    if rect.width > min_dimension and rect.height > min_dimension:
                        page.add_redact_annot(rect)
                        boxes_on_page.append(fitz.Rect(rect))
                        
        if boxes_on_page:
            memory.extend([(page.number, r) for r in boxes_on_page])
            print(f"  Page {page.number}: {len(boxes_on_page)} boxes")
            page.apply_redactions(images=0, graphics=1, text=1)
            total_removed += len(boxes_on_page)
            
    print(f"  -> Destroyed {total_removed} boxes")

    temp_path = output_path + ".tmp.pdf"
    doc.save(temp_path)
    doc.close()
    
    # PHASE 2: HEAL BROKEN TABLE LINES USING MEMORY
    doc = fitz.open(temp_path)
    total_h = 0
    total_v = 0
    
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
                # V4 FIX: If vert_leak_cap is set, limit the vertical line height
                draw_y0 = box_y0
                draw_y1 = box_y1
                if vert_leak_cap is not None:
                    box_height = box_y1 - box_y0
                    if box_height > vert_leak_cap:
                        # Find the closest horizontal line INSIDE the box to this vertical
                        # to figure out the actual table row height
                        closest_h_inside = []
                        for y, xmin, xmax in horiz_lines:
                            if box_y0 <= y <= box_y1:
                                closest_h_inside.append(y)
                        
                        if closest_h_inside:
                            # Find which end the vertical line connects to
                            for vx, vymin, vymax in vert_lines:
                                if abs(vx - x) < 1.0:
                                    if abs(vymax - box_y0) < 5.0:
                                        # Line connects to top of box, extend down to nearest h-line
                                        nearest_below = [h for h in closest_h_inside if h > box_y0]
                                        if nearest_below:
                                            draw_y1 = min(draw_y1, min(nearest_below) + vert_leak_cap)
                                    elif abs(vymin - box_y1) < 5.0:
                                        # Line connects to bottom of box, extend up to nearest h-line
                                        nearest_above = [h for h in closest_h_inside if h < box_y1]
                                        if nearest_above:
                                            draw_y0 = max(draw_y0, max(nearest_above) - vert_leak_cap)
                                    break
                
                if draw_v_line(x, draw_y0, draw_y1):
                    total_v += 1

    print(f"  -> Healed {total_h} H-borders, {total_v} V-borders")
    doc.save(output_path)
    doc.close()
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    print(f"  -> Saved: {output_path}")
    return total_removed, total_h, total_v


if __name__ == '__main__':
    input_pdf = "Original PDF/Dummy App (5).pdf"
    
    # Configuration variants to test
    configs = [
        {
            "name": "A_strict",
            "color_threshold": 0.1,
            "min_dimension": 2.0,
            "vert_leak_cap": 30.0,
            "desc": "Strict black only (< 0.1), vert cap 30pt"
        },
        {
            "name": "B_relaxed_color",
            "color_threshold": 0.2,
            "min_dimension": 2.0,
            "vert_leak_cap": 30.0,
            "desc": "Relaxed color (< 0.2), vert cap 30pt"
        },
        {
            "name": "C_very_relaxed",
            "color_threshold": 0.3,
            "min_dimension": 2.0,
            "vert_leak_cap": 30.0,
            "desc": "Very relaxed color (< 0.3), vert cap 30pt"
        },
        {
            "name": "D_strict_no_vcap",
            "color_threshold": 0.1,
            "min_dimension": 2.0,
            "vert_leak_cap": None,
            "desc": "Strict black (< 0.1), no vert cap (like V3)"
        },
    ]
    
    print("=" * 70)
    print("MULTI-THRESHOLD PDF GENERATION")
    print("=" * 70)
    
    results = []
    for cfg in configs:
        out_path = f"Output PDF/Dummy App (5)_{cfg['name']}.pdf"
        removed, h, v = process_pdf(
            input_pdf, out_path,
            color_threshold=cfg["color_threshold"],
            min_dimension=cfg["min_dimension"],
            vert_leak_cap=cfg["vert_leak_cap"]
        )
        results.append((cfg["name"], cfg["desc"], removed, h, v))
    
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    for name, desc, removed, h, v in results:
        print(f"  {name:20s} | {desc:45s} | Boxes={removed:3d} | H={h:3d} V={v:3d}")
    print("=" * 70)
    print("\nCheck 'Output PDF/' for all generated files.")
