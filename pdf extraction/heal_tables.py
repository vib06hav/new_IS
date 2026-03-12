import sys
import fitz

def heal_broken_lines(pdf_path, output_path):
    print(f"Healing broken table lines in {pdf_path}...")
    doc = fitz.open(pdf_path)
    
    total_horizontal_healed = 0
    total_vertical_healed = 0
    
    for page in doc:
        drawings = page.get_drawings()
        
        horiz_lines = []
        vert_lines = []
        
        for d in drawings:
            # Look at strokes and filled thin rects
            if "s" in d.get("type", "") or "f" in d.get("type", ""):
                for item in d["items"]:
                    if item[0] == "l": 
                        p1, p2 = item[1], item[2]
                        # Horizontal
                        if abs(p1.y - p2.y) < 1.0:
                            y = (p1.y + p2.y) / 2
                            min_x = min(p1.x, p2.x)
                            max_x = max(p1.x, p2.x)
                            horiz_lines.append((y, min_x, max_x, d.get("color", (0,0,0)), d.get("width", 0.5)))
                        # Vertical
                        elif abs(p1.x - p2.x) < 1.0:
                            x = (p1.x + p2.x) / 2
                            min_y = min(p1.y, p2.y)
                            max_y = max(p1.y, p2.y)
                            vert_lines.append((x, min_y, max_y, d.get("color", (0,0,0)), d.get("width", 0.5)))
                    
                    elif item[0] == "re": 
                        rect = item[1]
                        # Thin horizontal rect
                        if rect.height < 2.0:
                            y = rect.y0 + rect.height / 2
                            horiz_lines.append((y, rect.x0, rect.x1, d.get("color", (0,0,0)), d.get("width", 0.5) or rect.height))
                        # Thin vertical rect (usually < 2.0 width)
                        elif rect.width < 2.0:
                            x = rect.x0 + rect.width / 2
                            vert_lines.append((x, rect.y0, rect.y1, d.get("color", (0,0,0)), d.get("width", 0.5) or rect.width))
        
        # HEAL HORIZONTAL LINES
        from collections import defaultdict
        horiz_lines.sort(key=lambda x: x[0]) # sort by Y
        h_groups = []
        for line in horiz_lines:
            y, xmin, xmax, color, width = line
            placed = False
            for g in h_groups:
                if abs(g["coord"] - y) < 1.5:
                    g["lines"].append((xmin, xmax, color, width))
                    placed = True
                    break
            if not placed:
                h_groups.append({"coord": y, "lines": [(xmin, xmax, color, width)]})
                
        for g in h_groups:
            y = g["coord"]
            lines_in_group = sorted(g["lines"], key=lambda x: x[0]) # sort by X min
            for i in range(len(lines_in_group) - 1):
                cur_line = lines_in_group[i]
                nxt_line = lines_in_group[i+1]
                
                gap_start = cur_line[1] # max_x of current
                gap_end = nxt_line[0]   # min_x of next
                
                gap_width = gap_end - gap_start
                # Only heal clear gaps typical of a redaction dropout (e.g., 2 to 400 points)
                # But don't bridge completely unrelated elements.
                if 2.0 < gap_width < 400.0:
                    color = cur_line[2] or (0,0,0)
                    width = cur_line[3] or 0.5
                    p1 = fitz.Point(gap_start, y)
                    p2 = fitz.Point(gap_end, y)
                    # We might want to use draw_line but sometimes it needs to be an exact shape. 
                    # draw_line works fine for pdfminer.
                    page.draw_line(p1, p2, color=color, width=width)
                    total_horizontal_healed += 1

        # HEAL VERTICAL LINES
        vert_lines.sort(key=lambda x: x[0]) # sort by X
        v_groups = []
        for line in vert_lines:
            x, ymin, ymax, color, width = line
            placed = False
            for g in v_groups:
                if abs(g["coord"] - x) < 1.5:
                    g["lines"].append((ymin, ymax, color, width))
                    placed = True
                    break
            if not placed:
                v_groups.append({"coord": x, "lines": [(ymin, ymax, color, width)]})
                
        for g in v_groups:
            x = g["coord"]
            lines_in_group = sorted(g["lines"], key=lambda x: x[0]) # sort by Y min
            for i in range(len(lines_in_group) - 1):
                cur_line = lines_in_group[i]
                nxt_line = lines_in_group[i+1]
                
                gap_start = cur_line[1] # max_y of current
                gap_end = nxt_line[0]   # min_y of next
                
                gap_height = gap_end - gap_start
                # Typically vertical table cell borders aren't huge, maybe up to 100 points
                if 2.0 < gap_height < 300.0:
                    color = cur_line[2] or (0,0,0)
                    width = cur_line[3] or 0.5
                    p1 = fitz.Point(x, gap_start)
                    p2 = fitz.Point(x, gap_end)
                    page.draw_line(p1, p2, color=color, width=width)
                    total_vertical_healed += 1

        print(f"Page {page.number} - Healed {total_horizontal_healed} H-lines, {total_vertical_healed} V-lines")

    doc.save(output_path)
    print(f"Saved fully healed PDF to {output_path}")

if __name__ == '__main__':
    heal_broken_lines(sys.argv[1], sys.argv[2])
