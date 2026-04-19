# Graph Report - C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app  (2026-04-18)

## Corpus Check
- 76 files · ~37,633 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 524 nodes · 1042 edges · 27 communities detected
- Extraction: 69% EXTRACTED · 31% INFERRED · 0% AMBIGUOUS · INFERRED: 326 edges (avg confidence: 0.77)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]

## God Nodes (most connected - your core abstractions)
1. `run_pipeline()` - 25 edges
2. `get_application_or_404()` - 21 edges
3. `LLMClientError` - 17 edges
4. `run_synthesis_pipeline()` - 16 edges
5. `get_storage_service()` - 16 edges
6. `get_assignment_for_application()` - 15 edges
7. `upload_application()` - 13 edges
8. `build_application_list_item()` - 13 edges
9. `answer_report_question()` - 12 edges
10. `extract_layout_blocks()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `enforce_csrf()` --calls--> `ensure_csrf_protection()`  [INFERRED]
  C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app\main.py → C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app\security\csrf.py
- `persist_final_report_export()` --calls--> `storage_key_for_final_report_export()`  [INFERRED]
  C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app\final_report_exports.py → C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app\storage\service.py
- `retry_application()` --calls--> `sync_final_report_export()`  [INFERRED]
  C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app\api\admin.py → C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app\final_report_exports.py
- `generate_final_report()` --calls--> `sync_final_report_export()`  [INFERRED]
  C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app\api\admin.py → C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app\final_report_exports.py
- `get_application_final_report_export()` --calls--> `final_report_export_stream()`  [INFERRED]
  C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app\api\applications.py → C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app\final_report_exports.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (58): assemble_canonical(), Canonical Structure Assembler.     Merges all extracted collections into the fi, BaseModel, build_assignment_list_item(), AcademicEntry, ActivityEntry, AgentScore, Anomaly (+50 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (39): Application, assemble_ros_v1(), Deterministic ROS assembly.     Merges Pages 1-3 (from projection), Call 1 theme, Base, construct_bundle(), Agent 15: Theme-first signal-evidence bundle constructor.     Groups validated i, CanonicalRecord, detect_cross_sections() (+31 more)

### Community 2 - "Community 2"
Cohesion: 0.12
Nodes (43): assign_application(), generate_final_report(), _get_interviewer_or_400(), hide_application(), list_applications(), list_assignments(), reassign_application(), retry_application() (+35 more)

### Community 3 - "Community 3"
Cohesion: 0.1
Nodes (26): delete_application(), _delete_application_with_related_data(), remove_application_from_queue(), derive_display_id(), get_application_source_pdf(), _handle_application_insert_integrity_error(), staged_upload_file(), upload_application() (+18 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (31): Assignment, get_current_user(), build_interviewer_list_item(), register(), create_access_token(), decode_access_token(), get_password_hash(), verify_password() (+23 more)

### Community 5 - "Community 5"
Cohesion: 0.1
Nodes (33): get_llm_capacity(), _apply_response_format(), _clean_json_response(), _extract_openai_compatible_text(), generate(), _generate_aicredits(), _generate_openai_compatible(), _get_braintrust_logger() (+25 more)

### Community 6 - "Community 6"
Cohesion: 0.09
Nodes (23): extract_additional_info(), dedupe_near_overlapping_blocks(), Collapse near-identical overlapping text blocks created by edited PDFs., _empty_family_background(), extract_family_background(), _find_value_for_label(), _all_field_labels(), _extract_candidate() (+15 more)

### Community 7 - "Community 7"
Cohesion: 0.15
Nodes (29): LLMRequestOptions, answer_report_question(), build_report_chat_context(), _build_report_chat_messages(), _build_report_chat_repair_messages(), _build_selected_pages(), detect_operation(), _detect_operation_from() (+21 more)

### Community 8 - "Community 8"
Cohesion: 0.12
Nodes (22): _allowed_origins(), clear_csrf_cookie(), ensure_csrf_protection(), generate_csrf_token(), _is_allowed_loopback_origin(), _origin_from_url(), request_uses_session_cookie(), set_csrf_cookie() (+14 more)

### Community 9 - "Community 9"
Cohesion: 0.11
Nodes (18): build_essay_fragments(), _paragraph_spans(), _sentence_group_spans(), _trim_span(), Exception, bootstrap_dev_admin(), enforce_csrf(), stop_background_workers() (+10 more)

### Community 10 - "Community 10"
Cohesion: 0.1
Nodes (21): _apply_spatial_metadata(), extract_academic_records(), Extract academic records using precise spatial layout blocks.     Clusters block, Aligns metadata blocks to anchors using distance-ranked pairing., is_stop_word(), Form Vocabulary Registry for the AG Interview Standardiser.  This is the SINGLE, Returns True if the given text is a known form label (stop word)     that should, build_layout_rows() (+13 more)

### Community 11 - "Community 11"
Cohesion: 0.17
Nodes (23): get_prohibited_terms(), get_version(), PolicyConfig, Configuration for the policy guard. Externalized rules to ensure no     hardcod, _append_text_violations(), _backfill_signal_references(), _first_present(), _normalize_question_group_output() (+15 more)

### Community 12 - "Community 12"
Cohesion: 0.18
Nodes (16): _build_block_ir(), _build_header_candidates(), _build_issue_ir(), _build_layout_issues(), _build_page_stats(), _enrich_block(), extract_layout_blocks(), Extracts ordered text blocks from a PDF using pdfminer.six.     Returns page me (+8 more)

### Community 13 - "Community 13"
Cohesion: 0.19
Nodes (10): extract_activities(), _looks_like_descriptive_text(), _normalize_activity_entry(), Extract activities using a Grid-Line based spatial approach with Dynamic Column, is_valid_activity(), Centralized validation for activity entries.     Filters out common hallucinatio, get_page_heights(), get_vertical_lines() (+2 more)

### Community 14 - "Community 14"
Cohesion: 0.36
Nodes (8): _assign_entity_ids(), _compute_highlights(), _project_page_1(), _project_page_2(), _project_page_3(), project_ros(), Deterministic projection layer.     Returns: (page_1, page_2, page_3, annotated, Deterministically assigns entity_ids to canonical entries based on array positio

### Community 15 - "Community 15"
Cohesion: 0.38
Nodes (3): acquire(), CapacityFullError, GenerationJobLimiter

### Community 16 - "Community 16"
Cohesion: 0.47
Nodes (5): build_synthesis_projection(), compress_text(), Apply strictly deterministic projection, flattening, and compression     to can, Deterministically compress text by normalizing whitespace., _render_projection()

### Community 17 - "Community 17"
Cohesion: 0.6
Nodes (3): check_writable_dir(), _looks_like_placeholder_secret(), Settings

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (0): 

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (0): 

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (0): 

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **44 isolated node(s):** `Extract academic records using precise spatial layout blocks.     Clusters block`, `Aligns metadata blocks to anchors using distance-ranked pairing.`, `Extract activities using a Grid-Line based spatial approach with Dynamic Column`, `Agent 15: Theme-first signal-evidence bundle constructor.     Groups validated i`, `Cross-Section Entity Detector. Token-filtered entity detection.` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 18`** (2 nodes): `database.py`, `get_db()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `version.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_pipeline()` connect `Community 1` to `Community 0`, `Community 6`, `Community 10`, `Community 12`, `Community 13`, `Community 14`?**
  _High betweenness centrality (0.334) - this node is a cross-community bridge._
- **Why does `run_synthesis_pipeline()` connect `Community 1` to `Community 2`, `Community 11`, `Community 14`?**
  _High betweenness centrality (0.220) - this node is a cross-community bridge._
- **Why does `extract_layout_blocks()` connect `Community 12` to `Community 1`, `Community 10`, `Community 3`, `Community 6`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `run_pipeline()` (e.g. with `extract_layout_blocks()` and `normalize_layout()`) actually correct?**
  _`run_pipeline()` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `get_application_or_404()` (e.g. with `retry_application()` and `generate_final_report()`) actually correct?**
  _`get_application_or_404()` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `LLMClientError` (e.g. with `ReportChatRoute` and `ReportChatError`) actually correct?**
  _`LLMClientError` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `run_synthesis_pipeline()` (e.g. with `project_ros()` and `detect_signals()`) actually correct?**
  _`run_synthesis_pipeline()` has 13 INFERRED edges - model-reasoned connections that need verification._