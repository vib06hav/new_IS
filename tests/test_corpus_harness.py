import json

from tests.corpus_harness import diff_corpus_versions, dump_pdf_artifacts, load_manifest, run_corpus, PDF_DIR


def test_deterministic_parser_matches_corpus_manifest():
    manifest = {entry["pdf"]: entry for entry in load_manifest()}
    results = run_corpus()

    assert len(results) == len(manifest)

    for result in results:
        expected = manifest[result["pdf"]]
        assert result["pages"] == expected["pages"]
        assert result["full_name"] == expected["full_name"]
        assert result["preferred_major"] == expected["preferred_major"]
        assert result["academic_entries"] == expected["academic_entries"]
        assert result["test_entries"] == expected["test_entries"]
        assert result["essay_entries"] == expected["essay_entries"]
        assert result["activity_entries"] == expected["activity_entries"]
        assert result["anomalies"] <= expected["max_anomalies"]
        for section_type in expected["required_section_types"]:
            assert section_type in result["section_types"]
        for forbidden_label in expected.get("forbidden_section_labels", []):
            assert forbidden_label not in result["section_labels"]


def test_dump_pdf_artifacts_writes_stage_files(tmp_path):
    pdf_path = sorted(PDF_DIR.glob("*.pdf"))[0]

    written = dump_pdf_artifacts(pdf_path, tmp_path)

    expected_keys = {
        "layout_data",
        "normalized_rows",
        "section_data",
        "personal_data",
        "academic_data",
        "test_data",
        "essay_data",
        "activity_data",
        "cross_section_data",
        "integrity_data",
        "summary",
    }
    assert expected_keys == set(written)

    summary = json.loads(written["summary"].read_text(encoding="utf-8"))
    assert summary["pdf"] == pdf_path.name
    assert written["academic_data"].name == "05_academic_records.json"


def test_diff_corpus_versions_returns_structured_comparison():
    diffs = diff_corpus_versions("v1", "v2")

    assert len(diffs) == len(list(PDF_DIR.glob("*.pdf")))
    assert all({"pdf", "version_a", "version_b", "changed_fields"} <= diff.keys() for diff in diffs)
