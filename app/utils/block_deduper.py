from typing import Any, Dict, List

from app.utils.text_normalization import normalize_pdf_text


def dedupe_near_overlapping_blocks(
    blocks: List[Dict[str, Any]],
    *,
    position_tolerance: float = 2.0,
) -> List[Dict[str, Any]]:
    """
    Collapse near-identical overlapping text blocks created by edited PDFs.
    """
    deduped: List[Dict[str, Any]] = []

    for block in blocks:
        page = block.get("page")
        bbox = block.get("bbox")
        text = normalize_pdf_text(str(block.get("text", "") or ""))
        if not bbox or not text:
            deduped.append(block)
            continue

        duplicate = False
        for existing in deduped:
            existing_bbox = existing.get("bbox")
            existing_text = normalize_pdf_text(str(existing.get("text", "") or ""))
            if (
                existing.get("page") == page
                and existing_bbox
                and existing_text == text
                and abs(existing_bbox[0] - bbox[0]) <= position_tolerance
                and abs(existing_bbox[1] - bbox[1]) <= position_tolerance
                and abs(existing_bbox[2] - bbox[2]) <= position_tolerance
                and abs(existing_bbox[3] - bbox[3]) <= position_tolerance
            ):
                duplicate = True
                break

        if not duplicate:
            deduped.append(block)

    return deduped
