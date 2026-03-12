import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def normalize_layout(blocks: List[Dict[str, Any]]) -> List[List[str]]:
    """
    Normalizes layout blocks into rows using deterministic coordinate rules.
    """
    if not blocks:
        return []

    # Group by page, skipping blocks without bbox
    pages_blocks = {}
    for b in blocks:
        if "bbox" not in b:
            continue
        pages_blocks.setdefault(b["page"], []).append(b)

    all_rows = []

    for page in sorted(pages_blocks.keys()):
        page_blocks = pages_blocks[page]
        
        # 1. Cluster columns by x-coordinate ranges
        column_clusters = []
        sorted_by_x = sorted(page_blocks, key=lambda b: b["bbox"][0])
        for b in sorted_by_x:
            x0, x1 = b["bbox"][0], b["bbox"][2]
            matched_cluster = None
            for cluster in column_clusters:
                c_x0, c_x1 = cluster["x0"], cluster["x1"]
                if abs(x0 - c_x0) < 20 or (x0 <= c_x1 and x1 >= c_x0):
                    matched_cluster = cluster
                    break
            if matched_cluster:
                matched_cluster["blocks"].append(b)
                matched_cluster["x0"] = min(matched_cluster["x0"], x0)
                matched_cluster["x1"] = max(matched_cluster["x1"], x1)
            else:
                column_clusters.append({"x0": x0, "x1": x1, "blocks": [b]})

        # 2. Merge multiline cells within each column cluster
        merged_blocks = []
        for cluster in column_clusters:
            cluster_blocks = cluster["blocks"]
            cluster_blocks.sort(key=lambda b: -b["bbox"][3])  # Top-to-bottom
            used = set()
            for i, b1 in enumerate(cluster_blocks):
                if i in used:
                    continue
                current_merged = {
                    "text": b1["text"],
                    "bbox": list(b1["bbox"]),
                    "page": b1["page"]
                }
                used.add(i)
                for j in range(i + 1, len(cluster_blocks)):
                    if j in used:
                        continue
                    b2 = cluster_blocks[j]
                    gap = current_merged["bbox"][1] - b2["bbox"][3]
                    # Only check vertical gap since they are in the same column cluster
                    if -5 <= gap < 20:
                        current_merged["text"] = current_merged["text"] + " " + b2["text"]
                        current_merged["bbox"][0] = min(current_merged["bbox"][0], b2["bbox"][0])
                        current_merged["bbox"][1] = min(current_merged["bbox"][1], b2["bbox"][1])
                        current_merged["bbox"][2] = max(current_merged["bbox"][2], b2["bbox"][2])
                        current_merged["bbox"][3] = max(current_merged["bbox"][3], b2["bbox"][3])
                        used.add(j)
                merged_blocks.append(current_merged)

        # 3. Group into rows by y-proximity
        # Sort merged blocks top-to-bottom by center Y
        merged_blocks.sort(key=lambda b: -(b["bbox"][1] + b["bbox"][3])/2)
        
        rows = [] # List of lists of blocks
        current_row = []
        current_row_y = None
        
        for b in merged_blocks:
            center_y = (b["bbox"][1] + b["bbox"][3]) / 2
            if current_row_y is None:
                current_row.append(b)
                current_row_y = center_y
            else:
                if abs(center_y - current_row_y) < 15:
                    current_row.append(b)
                else:
                    rows.append(current_row)
                    current_row = [b]
                    current_row_y = center_y
        if current_row:
            rows.append(current_row)
            
        # 3. Sort elements in each row left-to-right
        for row in rows:
            row.sort(key=lambda b: b["bbox"][0])
            all_rows.append([b["text"].replace("\n", " ").strip() for b in row])

    # 4. Debug logging
    logger.debug("LAYOUT_ROWS_START")
    for row in all_rows:
        logger.debug(str(row))
    logger.debug("LAYOUT_ROWS_END")
    
    return all_rows

