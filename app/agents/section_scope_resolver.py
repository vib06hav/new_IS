from typing import Any, Dict, List, Optional

from app.utils.text_normalization import normalize_label


def _rows_for_section(section: Dict[str, Any], layout_rows: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    if not layout_rows:
        return []

    start = section.get("start_row_index")
    end = section.get("end_row_index")
    if start is None or end is None:
        return []

    return [
        row
        for row in layout_rows
        if start <= row.get("row_index", -1) <= end
    ]


def _resolve_section_type(section: Dict[str, Any], parser_engine_version: str) -> Optional[str]:
    section_type = section.get("section_type")
    label = section.get("label", "").lower()

    if parser_engine_version != "v1":
        return section_type

    if "personal" in label:
        return "personal_details"
    if any(kw in label for kw in ["parent", "father", "mother"]):
        return "parent_details"
    if "address" in label:
        return "address_details"
    if "extra" in label and "curricul" in label:
        return "extracurricular"
    if "co" in label and "curricul" in label:
        return "co_curricular"
    if "leadership" in label:
        return "leadership"
    if any(kw in label for kw in ["class", "academic", "education", "degree", "school"]):
        return "academics"
    if any(kw in label for kw in ["test", "jee", "sat", "act", "examination", "percentile", "score"]):
        return "standardized_tests"
    if "essay" in label:
        return "essays"
    if "additional" in label:
        return "additional_information"

    return section_type


def _build_section_slice(
    section: Dict[str, Any],
    section_type: Optional[str],
    layout_rows: Optional[List[Dict[str, Any]]],
) -> Dict[str, Any]:
    section_rows = _rows_for_section(section, layout_rows)
    row_blocks: List[Dict[str, Any]] = []
    for row in section_rows:
        row_blocks.extend(row.get("blocks", []))

    return {
        "label": section.get("label"),
        "normalized_label": normalize_label(section.get("label", "")),
        "section_type": section_type,
        "blocks": row_blocks or section.get("blocks", []),
        "rows": section_rows,
        "start_row_index": section.get("start_row_index"),
        "end_row_index": section.get("end_row_index"),
    }


def resolve_section_scopes(
    section_data: Dict[str, Any],
    parser_engine_version: str,
    layout_rows: Optional[List[Dict[str, Any]]],
) -> Dict[str, Any]:
    section_map: Dict[str, List[Dict[str, Any]]] = {}
    section_slices: Dict[str, List[Dict[str, Any]]] = {}
    academic_rows: List[Dict[str, Any]] = []
    test_rows: List[Dict[str, Any]] = []

    for section in section_data.get("sections", []):
        resolved_type = _resolve_section_type(section, parser_engine_version)
        section_slice = _build_section_slice(section, resolved_type, layout_rows)

        if resolved_type:
            section_map.setdefault(resolved_type, []).extend(section.get("blocks", []))
            section_slices.setdefault(resolved_type, []).append(section_slice)

        if resolved_type == "academics":
            academic_rows.extend(section_slice["rows"])
        elif resolved_type == "standardized_tests":
            test_rows.extend(section_slice["rows"])

    return {
        "section_map": section_map,
        "section_slices": section_slices,
        "academic_rows": academic_rows,
        "test_rows": test_rows,
    }
