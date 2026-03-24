from typing import List, Dict, Any


def group_blocks_into_rows(
    blocks: List[Dict[str, Any]],
    y_threshold: float = 12.0,
) -> List[List[Dict[str, Any]]]:
    """
    Deterministically group PDF layout blocks into left-to-right rows per page.

    The returned rows preserve the original block dictionaries so extractors can
    continue using bbox-based alignment after row reconstruction.
    """
    if not blocks:
        return []

    blocks_by_page: Dict[int, List[Dict[str, Any]]] = {}
    for block in blocks:
        if "bbox" not in block or "page" not in block:
            continue
        blocks_by_page.setdefault(block["page"], []).append(block)

    all_rows: List[List[Dict[str, Any]]] = []
    for page in sorted(blocks_by_page):
        page_blocks = sorted(
            blocks_by_page[page],
            key=lambda b: -((b["bbox"][1] + b["bbox"][3]) / 2),
        )

        page_rows: List[List[Dict[str, Any]]] = []
        current_row: List[Dict[str, Any]] = []
        current_y = None

        for block in page_blocks:
            center_y = (block["bbox"][1] + block["bbox"][3]) / 2
            if current_y is None or abs(center_y - current_y) < y_threshold:
                current_row.append(block)
                current_y = center_y if current_y is None else current_y
            else:
                page_rows.append(sorted(current_row, key=lambda b: b["bbox"][0]))
                current_row = [block]
                current_y = center_y

        if current_row:
            page_rows.append(sorted(current_row, key=lambda b: b["bbox"][0]))

        all_rows.extend(page_rows)

    return all_rows


def build_layout_rows(
    blocks: List[Dict[str, Any]],
    y_threshold: float = 12.0,
) -> List[Dict[str, Any]]:
    """
    Build a shared row representation on top of grouped layout blocks.
    """
    rows = []
    for row_index, row_blocks in enumerate(group_blocks_into_rows(blocks, y_threshold=y_threshold)):
        texts = [str(block.get("text", "")).strip() for block in row_blocks if str(block.get("text", "")).strip()]
        row_text = " ".join(texts).strip()
        x0 = min(block["bbox"][0] for block in row_blocks)
        x1 = max(block["bbox"][2] for block in row_blocks)
        y0 = min(block["bbox"][1] for block in row_blocks)
        y1 = max(block["bbox"][3] for block in row_blocks)
        sparse = len(row_blocks) <= 1 or len(row_text.split()) <= 2
        uppercase_like = row_text.isupper() if row_text else False
        keyword_hits = sum(
            1
            for token in ["details", "information", "activities", "academic", "tests", "essays", "references", "declaration"]
            if token in row_text.lower()
        )
        candidate_header_score = min(1.0, (0.35 if uppercase_like else 0.0) + (0.15 * keyword_hits) + (0.2 if sparse else 0.0))

        rows.append({
            "row_index": row_index,
            "page": row_blocks[0]["page"],
            "blocks": row_blocks,
            "text": row_text,
            "x_span": [x0, x1],
            "y_span": [y0, y1],
            "is_sparse": sparse,
            "candidate_header_score": round(candidate_header_score, 2),
            "table_context_id": None,
        })

    return rows
