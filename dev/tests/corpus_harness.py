import json
import os
from pathlib import Path
from typing import Any, Dict, List

from app.config import settings
from app.agents.academic_extractor import extract_academic_records
from app.agents.activity_extractor import extract_activities
from app.agents.additional_info_extractor import extract_additional_info
from app.agents.cross_section_detector import detect_cross_sections
from app.agents.essay_extractor import extract_essays
from app.agents.family_extractor import extract_family_background
from app.agents.integrity_analyzer import analyze_integrity
from app.agents.layout_extractor import extract_layout_blocks
from app.agents.personal_extractor import extract_personal_info
from app.agents.geographic_extractor import extract_geographic_context
from app.agents.section_scope_resolver import resolve_section_scopes
from app.agents.section_detector import detect_sections
from app.agents.test_extractor import extract_test_records
from app.utils.layout_normalizer import normalize_layout


PDF_DIR = Path(__file__).resolve().parent / "pdfs"
MANIFEST_PATH = Path(__file__).resolve().parent / "corpus_manifest.json"
ARTIFACT_STAGE_FILES = {
    "layout_data": "01_layout_raw.json",
    "normalized_rows": "02_layout_normalized.json",
    "section_data": "03_sections.json",
    "personal_data": "04_personal_info.json",
    "academic_data": "05_academic_records.json",
    "test_data": "06_test_records.json",
    "essay_data": "07_essays.json",
    "activity_data": "08_activities.json",
    "cross_section_data": "09_cross_section.json",
    "integrity_data": "10_integrity_analysis.json",
}


def _merge_activity_results(*results: Dict[str, Any]) -> Dict[str, Any]:
    activity_entries: List[Dict[str, Any]] = []
    confidences: List[float] = []
    preferred_major = None

    for result in results:
        if not result:
            continue
        activity_entries.extend(result.get("activity_entries", []))
        if result.get("confidence_score") is not None:
            confidences.append(result.get("confidence_score", 0.0))
        if not preferred_major and result.get("preferred_major"):
            preferred_major = result["preferred_major"]

    return {
        "activity_entries": activity_entries,
        "preferred_major": preferred_major,
        "confidence_score": (sum(confidences) / len(confidences)) if confidences else 0.0,
    }

def _run_deterministic_pipeline_stages(pdf_path: Path, parser_engine_version: str = "v2") -> Dict[str, Any]:
    layout_data = extract_layout_blocks(str(pdf_path))
    layout_data["normalized_rows"] = normalize_layout(layout_data["blocks"])
    section_data = detect_sections(layout_data["blocks"], rows=layout_data.get("rows"))
    scopes = resolve_section_scopes(section_data, parser_engine_version, layout_data.get("rows", []))
    section_map = scopes["section_map"]
    section_slices = scopes["section_slices"]
    parent_sections = section_slices.get("parent_details", [])
    address_sections = section_slices.get("address_details", [])
    academic_rows = scopes["academic_rows"]
    test_rows = scopes["test_rows"]

    personal_scope = section_map.get("personal_details", []) or layout_data["blocks"]
    personal_data = extract_personal_info(personal_scope)
    family_data = extract_family_background(parent_sections)
    personal_data.setdefault("identifiers", {})["family_background"] = family_data["family_background"]
    personal_data["confidence_score"] = max(
        personal_data.get("confidence_score", 0.0),
        family_data.get("confidence_score", 0.0),
    )
    geographic_data = extract_geographic_context(address_sections)
    if geographic_data.get("geographic_context"):
        personal_data.setdefault("identifiers", {})["geographic_context"] = geographic_data["geographic_context"]
        personal_data["confidence_score"] = max(
            personal_data.get("confidence_score", 0.0),
            geographic_data.get("confidence_score", 0.0),
        )

    if section_map.get("additional_information"):
        additional_info_data = extract_additional_info(section_map["additional_information"], all_blocks=layout_data["blocks"])
        preferred_major = additional_info_data.get("preferred_major")
        if preferred_major:
            identifiers = personal_data.setdefault("identifiers", {})
            identifiers.setdefault("declared_preferences", {})
            identifiers["preferred_major"] = identifiers.get("preferred_major") or preferred_major
            identifiers["declared_preferences"]["major"] = (
                identifiers["declared_preferences"].get("major") or preferred_major
            )

    academic_data = extract_academic_records(section_map.get("academics", []) or layout_data["blocks"], rows=academic_rows or None)
    test_data = extract_test_records(section_map.get("standardized_tests", []) or layout_data["blocks"], rows=test_rows or None)
    essay_data = extract_essays(section_map.get("essays", []) or layout_data["blocks"])

    if any(section_map.get(key) for key in ("extracurricular", "co_curricular", "leadership")):
        activity_data = _merge_activity_results(
            extract_activities(section_map.get("extracurricular", []), str(pdf_path), forced_section="extracurricular")
            if section_map.get("extracurricular")
            else {},
            extract_activities(section_map.get("co_curricular", []), str(pdf_path), forced_section="co_curricular")
            if section_map.get("co_curricular")
            else {},
            extract_activities(section_map.get("leadership", []), str(pdf_path), forced_section="leadership")
            if section_map.get("leadership")
            else {},
        )
    else:
        activity_data = extract_activities(layout_data["blocks"], str(pdf_path))

    cross_section_data = detect_cross_sections(
        academic_data.get("academic_entries", []),
        test_data.get("test_entries", []),
        essay_data.get("essay_entries", []),
        activity_data.get("activity_entries", []),
    )

    integrity_data = analyze_integrity(
        personal_data.get("identifiers", {}),
        academic_data.get("academic_entries", []),
        essay_data.get("essay_entries", []),
        activity_data.get("activity_entries", []),
        layout_meta=layout_data,
        section_meta=section_data,
    )

    return {
        "layout_data": layout_data,
        "normalized_rows": layout_data["normalized_rows"],
        "section_data": section_data,
        "personal_data": personal_data,
        "academic_data": academic_data,
        "test_data": test_data,
        "essay_data": essay_data,
        "activity_data": activity_data,
        "cross_section_data": cross_section_data,
        "integrity_data": integrity_data,
        "parser_engine_version": parser_engine_version,
    }


def run_deterministic_parser(pdf_path: Path, parser_engine_version: str = "v2") -> Dict[str, Any]:
    stages = _run_deterministic_pipeline_stages(pdf_path, parser_engine_version=parser_engine_version)
    layout_data = stages["layout_data"]
    section_data = stages["section_data"]
    personal_data = stages["personal_data"]
    academic_data = stages["academic_data"]
    test_data = stages["test_data"]
    essay_data = stages["essay_data"]
    activity_data = stages["activity_data"]
    cross_section_data = stages["cross_section_data"]
    integrity_data = stages["integrity_data"]

    return {
        "pdf": pdf_path.name,
        "parser_engine_version": parser_engine_version,
        "pages": layout_data["page_count"],
        "blocks": len(layout_data["blocks"]),
        "section_labels": [section.get("label") for section in section_data.get("sections", [])],
        "section_types": [section.get("section_type") for section in section_data.get("sections", []) if section.get("section_type")],
        "full_name": personal_data.get("identifiers", {}).get("full_name"),
        "preferred_major": personal_data.get("identifiers", {}).get("preferred_major"),
        "academic_entries": len(academic_data.get("academic_entries", [])),
        "test_entries": len(test_data.get("test_entries", [])),
        "essay_entries": len(essay_data.get("essay_entries", [])),
        "activity_entries": len(activity_data.get("activity_entries", [])),
        "cross_entities": len(cross_section_data.get("entity_map", [])),
        "anomalies": len(integrity_data.get("anomalies", [])),
        "integrity_confidence": integrity_data.get("confidence_score"),
    }


def load_manifest() -> List[Dict[str, Any]]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def run_corpus() -> List[Dict[str, Any]]:
    parser_engine_version = settings.PARSER_ENGINE_VERSION
    return [run_deterministic_parser(pdf_path, parser_engine_version=parser_engine_version) for pdf_path in sorted(PDF_DIR.glob("*.pdf"))]


def dump_pdf_artifacts(pdf_path: Path, output_dir: Path, parser_engine_version: str = "v2") -> Dict[str, Path]:
    stages = _run_deterministic_pipeline_stages(pdf_path, parser_engine_version=parser_engine_version)
    pdf_dir = output_dir / parser_engine_version / pdf_path.stem
    pdf_dir.mkdir(parents=True, exist_ok=True)

    written_files: Dict[str, Path] = {}
    for stage_key, filename in ARTIFACT_STAGE_FILES.items():
        target = pdf_dir / filename
        target.write_text(json.dumps(stages[stage_key], indent=2, ensure_ascii=False), encoding="utf-8")
        written_files[stage_key] = target

    summary_path = pdf_dir / "summary.json"
    summary_path.write_text(
        json.dumps(run_deterministic_parser(pdf_path, parser_engine_version=parser_engine_version), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    written_files["summary"] = summary_path
    return written_files


def dump_corpus_artifacts(output_dir: Path, parser_engine_version: str = "v2") -> Dict[str, Dict[str, Path]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results: Dict[str, Dict[str, Path]] = {}
    for pdf_path in sorted(PDF_DIR.glob("*.pdf")):
        results[pdf_path.name] = dump_pdf_artifacts(pdf_path, output_dir, parser_engine_version=parser_engine_version)
    return results


def diff_corpus_versions(version_a: str = "v1", version_b: str = "v2") -> List[Dict[str, Any]]:
    diffs: List[Dict[str, Any]] = []
    for pdf_path in sorted(PDF_DIR.glob("*.pdf")):
        left = run_deterministic_parser(pdf_path, parser_engine_version=version_a)
        right = run_deterministic_parser(pdf_path, parser_engine_version=version_b)
        changed_fields = {}
        for key in [
            "full_name",
            "preferred_major",
            "academic_entries",
            "test_entries",
            "essay_entries",
            "activity_entries",
            "cross_entities",
            "anomalies",
            "integrity_confidence",
            "section_types",
        ]:
            if left.get(key) != right.get(key):
                changed_fields[key] = {version_a: left.get(key), version_b: right.get(key)}
        diffs.append({
            "pdf": pdf_path.name,
            "version_a": version_a,
            "version_b": version_b,
            "changed_fields": changed_fields,
        })
    return diffs
