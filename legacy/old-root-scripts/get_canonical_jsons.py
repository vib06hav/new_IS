
import os
import json
import sys
import uuid
from typing import Dict, Any

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.agents.layout_extractor import extract_layout_blocks
from app.agents.section_detector import detect_sections
from app.agents.personal_extractor import extract_personal_info
from app.agents.academic_extractor import extract_academic_records
from app.agents.test_extractor import extract_test_records
from app.agents.essay_extractor import extract_essays
from app.agents.activity_extractor import extract_activities
from app.agents.cross_section_detector import detect_cross_sections
from app.agents.integrity_analyzer import analyze_integrity
from app.agents.assembler import assemble_canonical
from app.utils.layout_normalizer import normalize_layout
from app.utils.sanitizer import sanitize_for_json

def get_canonical_for_pdf(pdf_path: str, application_id: str) -> Dict[str, Any]:
    # Agent 1: Layout Extraction
    layout_data = extract_layout_blocks(pdf_path)
    if not layout_data.get("blocks") and layout_data.get("page_count", 0) == 0:
        return {"error": f"Could not extract layout from {pdf_path}"}

    # Layout Normalization
    layout_data["normalized_rows"] = normalize_layout(layout_data["blocks"])

    # Agent 2: Section Boundary Detection
    section_data = detect_sections(layout_data["blocks"])

    # Extract Blocks (simulating orchestrator logic where needed)
    test_blocks = []
    essay_blocks = []
    for section in section_data.get("sections", []):
        label = section.get("label", "").lower()
        blocks = section.get("blocks", [])
        if any(kw in label for kw in ["test", "jee", "sat", "act", "examination"]):
            test_blocks.extend(blocks)
        elif "essay" in label:
            essay_blocks.extend(blocks)

    test_rows = normalize_layout(test_blocks) if test_blocks else layout_data["normalized_rows"]
    essay_blocks_to_pass = essay_blocks if essay_blocks else layout_data["blocks"]

    # Agent 3: Personal Information
    personal_data = extract_personal_info(layout_data["blocks"])

    # Agent 4: Academic Records
    academic_data = extract_academic_records(layout_data["blocks"])

    # Agent 5: Standardized Tests
    test_data = extract_test_records(test_blocks if test_blocks else layout_data["blocks"])

    # Agent 6: Essays
    essay_data = extract_essays(essay_blocks_to_pass)

    # Agent 7: Activities
    activity_data = extract_activities(layout_data["blocks"], pdf_path)

    # Agent 8: Cross-Section Entity Detection
    cross_section_data = detect_cross_sections(
        academic_data.get("academic_entries", []),
        test_data.get("test_entries", []),
        essay_data.get("essay_entries", []),
        activity_data.get("activity_entries", [])
    )

    # Agent 10: Integrity Analyzer
    integrity_data = analyze_integrity(
        personal_data.get("identifiers", {}),
        academic_data.get("academic_entries", []),
        essay_data.get("essay_entries", []),
        activity_data.get("activity_entries", [])
    )

    # Agent 11: Canonical Structure Assembler
    canonical_data = assemble_canonical(
        application_id=application_id,
        layout_meta=layout_data,
        section_meta=section_data,
        identifiers_data=personal_data,
        academic_data=academic_data,
        test_data=test_data,
        essay_data=essay_data,
        activity_data=activity_data,
        cross_section_data=cross_section_data,
        integrity_data=integrity_data
    )
    
    return sanitize_for_json(canonical_data)

def run_extraction():
    pdf_dir = os.path.join("tests", "pdfs")
    output_dir = os.path.join("tests", "canonical_results")
    os.makedirs(output_dir, exist_ok=True)

    pdfs = [
        "Dummy App (1)_v8_filled.pdf",
        "Dummy App (2)_v8_filled.pdf",
        "Dummy App (3)_v8_filled.pdf",
        "Dummy App (5)_v8_filled.pdf",
        "Dummy App (8)_v8_filled.pdf"
    ]

    for pdf_name in pdfs:
        pdf_path = os.path.join(pdf_dir, pdf_name)
        app_id = str(uuid.uuid4())
        print(f"Processing {pdf_name} (App ID: {app_id})...")
        try:
            canonical_data = get_canonical_for_pdf(pdf_path, app_id)
            output_filename = pdf_name.replace(".pdf", "_canonical.json")
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(canonical_data, f, indent=2, ensure_ascii=False)
            
            print(f"Saved to {output_path}")
        except Exception as e:
            print(f"Error processing {pdf_name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_extraction()
