# Graph Report - C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser  (2026-04-19)

## Corpus Check
- 165 files · ~211,740 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 884 nodes · 1466 edges · 106 communities detected
- Extraction: 73% EXTRACTED · 27% INFERRED · 0% AMBIGUOUS · INFERRED: 399 edges (avg confidence: 0.77)
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
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 91|Community 91]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 95|Community 95]]
- [[_COMMUNITY_Community 96|Community 96]]
- [[_COMMUNITY_Community 97|Community 97]]
- [[_COMMUNITY_Community 98|Community 98]]
- [[_COMMUNITY_Community 99|Community 99]]
- [[_COMMUNITY_Community 100|Community 100]]
- [[_COMMUNITY_Community 101|Community 101]]
- [[_COMMUNITY_Community 102|Community 102]]
- [[_COMMUNITY_Community 103|Community 103]]
- [[_COMMUNITY_Community 104|Community 104]]
- [[_COMMUNITY_Community 105|Community 105]]

## God Nodes (most connected - your core abstractions)
1. `apiRequest()` - 34 edges
2. `run_pipeline()` - 25 edges
3. `get_application_or_404()` - 21 edges
4. `LLMClientError` - 17 edges
5. `run_synthesis_pipeline()` - 16 edges
6. `get_assignment_for_application()` - 15 edges
7. `get_canonical_for_pdf()` - 14 edges
8. `extract_layout_blocks()` - 14 edges
9. `upload_application()` - 14 edges
10. `build_application_list_item()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `enforce_csrf()` --calls--> `ensure_csrf_protection()`  [INFERRED]
  C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app\main.py → C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app\security\csrf.py
- `analyze_integrity()` --calls--> `has_mojibake()`  [INFERRED]
  C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app\agents\integrity_analyzer.py → C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app\utils\text_normalization.py
- `login()` --calls--> `client_ip()`  [INFERRED]
  C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app\auth\router.py → C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app\security\rate_limit.py
- `get_canonical_for_pdf()` --calls--> `extract_layout_blocks()`  [INFERRED]
  C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\get_canonical_jsons.py → C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app\agents\layout_extractor.py
- `get_canonical_for_pdf()` --calls--> `detect_sections()`  [INFERRED]
  C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\get_canonical_jsons.py → C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app\agents\section_detector.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (69): _apply_response_format(), _clean_json_response(), _extract_openai_compatible_text(), generate(), _generate_aicredits(), _generate_openai_compatible(), _get_braintrust_logger(), get_llm_capacity_snapshot() (+61 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (54): apiRequest(), askReportChat(), assignApplication(), completeInterviewWorkspace(), createInterviewer(), createInterviewWorkspace(), deactivateInterviewer(), deleteApplication() (+46 more)

### Community 2 - "Community 2"
Cohesion: 0.04
Nodes (51): Application, assemble_ros_v1(), Deterministic ROS assembly.     Merges Pages 1-3 (from projection), Call 1 theme, Base, construct_bundle(), Agent 15: Theme-first signal-evidence bundle constructor.     Groups validated i, CanonicalRecord, detect_cross_sections() (+43 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (57): assemble_canonical(), Canonical Structure Assembler.     Merges all extracted collections into the fi, BaseModel, build_assignment_list_item(), AcademicEntry, ActivityEntry, AgentScore, Anomaly (+49 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (39): derive_display_id(), _handle_application_insert_integrity_error(), staged_upload_file(), upload_application(), validate_uploaded_pdf(), write_upload_with_limit(), check_writable_dir(), _looks_like_placeholder_secret() (+31 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (48): assign_application(), delete_application(), _delete_application_with_related_data(), generate_final_report(), _get_interviewer_or_400(), hide_application(), list_applications(), list_assignments() (+40 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (29): get_llm_capacity(), acquire(), CapacityFullError, GenerationJobLimiter, acquire(), BaseLockBackend, CoordinationManager, get_coordination_manager() (+21 more)

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (38): extract_additional_info(), dedupe_near_overlapping_blocks(), Collapse near-identical overlapping text blocks created by edited PDFs., _empty_family_background(), extract_family_background(), _find_value_for_label(), _all_field_labels(), _extract_candidate() (+30 more)

### Community 8 - "Community 8"
Cohesion: 0.09
Nodes (34): Assignment, get_current_user(), build_interviewer_list_item(), create_access_token(), decode_access_token(), get_password_hash(), bootstrap_admin_user(), build_public_profile_image_url() (+26 more)

### Community 9 - "Community 9"
Cohesion: 0.07
Nodes (31): _apply_spatial_metadata(), extract_academic_records(), Extract academic records using precise spatial layout blocks.     Clusters block, Aligns metadata blocks to anchors using distance-ranked pairing., extract_activities(), _looks_like_descriptive_text(), _normalize_activity_entry(), Extract activities using a Grid-Line based spatial approach with Dynamic Column (+23 more)

### Community 10 - "Community 10"
Cohesion: 0.09
Nodes (15): build_essay_fragments(), _paragraph_spans(), _sentence_group_spans(), _trim_span(), build_projection(), Agent 13: Canonical projection builder for LLM Call 1.     Constructs a cleaned, Protocol, client_ip() (+7 more)

### Community 11 - "Community 11"
Cohesion: 0.15
Nodes (25): get_prohibited_terms(), get_version(), PolicyConfig, Configuration for the policy guard. Externalized rules to ensure no     hardcod, _append_text_violations(), _backfill_signal_references(), _first_present(), _normalize_question_group_output() (+17 more)

### Community 12 - "Community 12"
Cohesion: 0.15
Nodes (23): _allowed_origins(), clear_csrf_cookie(), ensure_csrf_protection(), generate_csrf_token(), _is_allowed_loopback_origin(), _origin_from_url(), request_uses_session_cookie(), set_csrf_cookie() (+15 more)

### Community 13 - "Community 13"
Cohesion: 0.1
Nodes (2): buildItemAnnotationTitle(), getItemAnnotation()

### Community 14 - "Community 14"
Cohesion: 0.13
Nodes (14): buildPopupFeatures(), openInterviewPopup(), openInterviewPopupPlaceholder(), addQuestion(), handleLaunch(), handlePublish(), handleSave(), removeQuestion() (+6 more)

### Community 15 - "Community 15"
Cohesion: 0.14
Nodes (8): loadSession(), getSession(), signOut(), getCsrfToken(), readCookie(), loadSession(), checkSession(), handleSignOut()

### Community 16 - "Community 16"
Cohesion: 0.2
Nodes (0): 

### Community 17 - "Community 17"
Cohesion: 0.47
Nodes (5): build_synthesis_projection(), compress_text(), Apply strictly deterministic projection, flattening, and compression     to can, Deterministically compress text by normalizing whitespace., _render_projection()

### Community 18 - "Community 18"
Cohesion: 0.53
Nodes (5): addCustomQuestion(), cycleQuestionStatus(), handleFinish(), updateQuestion(), updateTheme()

### Community 19 - "Community 19"
Cohesion: 0.5
Nodes (2): ReportsDashboardSandboxPlayground(), usePolling()

### Community 20 - "Community 20"
Cohesion: 0.5
Nodes (2): Badge(), cn()

### Community 21 - "Community 21"
Cohesion: 0.5
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 0.5
Nodes (0): 

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (2): Reveal(), useScrollReveal()

### Community 24 - "Community 24"
Cohesion: 0.67
Nodes (0): 

### Community 25 - "Community 25"
Cohesion: 0.67
Nodes (0): 

### Community 26 - "Community 26"
Cohesion: 0.67
Nodes (0): 

### Community 27 - "Community 27"
Cohesion: 0.67
Nodes (0): 

### Community 28 - "Community 28"
Cohesion: 0.67
Nodes (0): 

### Community 29 - "Community 29"
Cohesion: 0.67
Nodes (0): 

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (0): 

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (0): 

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (0): 

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (0): 

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (0): 

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (0): 

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (0): 

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (0): 

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (0): 

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (0): 

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (0): 

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (0): 

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (0): 

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (0): 

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (0): 

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (0): 

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (0): 

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (0): 

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (0): 

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (0): 

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (0): 

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (0): 

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (0): 

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (0): 

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (0): 

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (0): 

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (0): 

### Community 66 - "Community 66"
Cohesion: 1.0
Nodes (0): 

### Community 67 - "Community 67"
Cohesion: 1.0
Nodes (0): 

### Community 68 - "Community 68"
Cohesion: 1.0
Nodes (0): 

### Community 69 - "Community 69"
Cohesion: 1.0
Nodes (0): 

### Community 70 - "Community 70"
Cohesion: 1.0
Nodes (0): 

### Community 71 - "Community 71"
Cohesion: 1.0
Nodes (0): 

### Community 72 - "Community 72"
Cohesion: 1.0
Nodes (0): 

### Community 73 - "Community 73"
Cohesion: 1.0
Nodes (0): 

### Community 74 - "Community 74"
Cohesion: 1.0
Nodes (0): 

### Community 75 - "Community 75"
Cohesion: 1.0
Nodes (0): 

### Community 76 - "Community 76"
Cohesion: 1.0
Nodes (0): 

### Community 77 - "Community 77"
Cohesion: 1.0
Nodes (0): 

### Community 78 - "Community 78"
Cohesion: 1.0
Nodes (0): 

### Community 79 - "Community 79"
Cohesion: 1.0
Nodes (0): 

### Community 80 - "Community 80"
Cohesion: 1.0
Nodes (0): 

### Community 81 - "Community 81"
Cohesion: 1.0
Nodes (0): 

### Community 82 - "Community 82"
Cohesion: 1.0
Nodes (0): 

### Community 83 - "Community 83"
Cohesion: 1.0
Nodes (0): 

### Community 84 - "Community 84"
Cohesion: 1.0
Nodes (0): 

### Community 85 - "Community 85"
Cohesion: 1.0
Nodes (1): Run migrations in 'offline' mode.      This configures the context with just a U

### Community 86 - "Community 86"
Cohesion: 1.0
Nodes (1): Run migrations in 'online' mode.      In this scenario we need to create an Engi

### Community 87 - "Community 87"
Cohesion: 1.0
Nodes (1): create_canonical_records_table  Revision ID: 6ea7523611f4 Revises: a3ba4d865b1f

### Community 88 - "Community 88"
Cohesion: 1.0
Nodes (1): add final report export fields  Revision ID: a1b2c3d4e5f7 Revises: f1a2b3c4d5

### Community 89 - "Community 89"
Cohesion: 1.0
Nodes (1): create_applications_table  Revision ID: a3ba4d865b1f Revises: ad9fb8d26e40 Creat

### Community 90 - "Community 90"
Cohesion: 1.0
Nodes (1): add_display_id_to_applications  Revision ID: a8b7c6d5e4f3 Revises: f7a9c1d2e3b4

### Community 91 - "Community 91"
Cohesion: 1.0
Nodes (1): create_users_table  Revision ID: ad9fb8d26e40 Revises: fe57dd6ef27e Create Date:

### Community 92 - "Community 92"
Cohesion: 1.0
Nodes (1): create_synthesis_records_table  Revision ID: ae34404b0e2f Revises: 6ea7523611f4

### Community 93 - "Community 93"
Cohesion: 1.0
Nodes (1): create processing jobs table  Revision ID: b2c3d4e5f6a8 Revises: a1b2c3d4e5f7

### Community 94 - "Community 94"
Cohesion: 1.0
Nodes (1): target_state_foundation  Revision ID: b3c1f2d4e5f6 Revises: ae34404b0e2f Create

### Community 95 - "Community 95"
Cohesion: 1.0
Nodes (1): rename file_path to storage_key  Revision ID: c3d4e5f6a7b9 Revises: b2c3d4e5f

### Community 96 - "Community 96"
Cohesion: 1.0
Nodes (1): drop_synthesis_records  Revision ID: c4d5e6f7a8b9 Revises: b3c1f2d4e5f6 Create D

### Community 97 - "Community 97"
Cohesion: 1.0
Nodes (1): replace_drafts_with_final_reports  Revision ID: c7d8e9f0a1b2 Revises: f9b8c7d

### Community 98 - "Community 98"
Cohesion: 1.0
Nodes (1): restore_last_activity_default  Revision ID: d1e2f3a4b5c6 Revises: c7d8e9f0a1b

### Community 99 - "Community 99"
Cohesion: 1.0
Nodes (1): add_review_package_to_canonical_records  Revision ID: d2f4e6a8b9c1 Revises: c4d5

### Community 100 - "Community 100"
Cohesion: 1.0
Nodes (1): add processing job retry fields  Revision ID: d4e5f6a7b8c0 Revises: c3d4e5f6a

### Community 101 - "Community 101"
Cohesion: 1.0
Nodes (1): create_interview_workspaces_table  Revision ID: e3f4a5b6c7d8 Revises: d1e2f3a

### Community 102 - "Community 102"
Cohesion: 1.0
Nodes (1): add profile image fields to users  Revision ID: f1a2b3c4d5e6 Revises: e3f4a5b

### Community 103 - "Community 103"
Cohesion: 1.0
Nodes (1): add_hidden_state_to_applications  Revision ID: f7a9c1d2e3b4 Revises: d2f4e6a8b9c

### Community 104 - "Community 104"
Cohesion: 1.0
Nodes (1): add_last_activity_and_interviewer_hide_state  Revision ID: f9b8c7d6e5a4 Revises:

### Community 105 - "Community 105"
Cohesion: 1.0
Nodes (1): enable_uuid_extension  Revision ID: fe57dd6ef27e Revises:  Create Date: 2026-03-

## Knowledge Gaps
- **81 isolated node(s):** `Builds the Stage 1.7 Call 2 prompt messages.     Instructs the LLM to generate i`, `Agent 16: Interview generator (LLM Call 2).     Makes exactly one LLM call to pr`, `Builds the Stage 1.7 Call 1 prompt messages.     Instructs the LLM to perform cr`, `Agent 14: Signal interpreter (LLM Call 1).     Makes exactly one LLM call to int`, `Fallback redis error when the redis package is unavailable.` (+76 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 30`** (2 nodes): `database.py`, `get_db()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (2 nodes): `layout.tsx`, `RootLayout()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (2 nodes): `layout.tsx`, `AdminLayout()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (2 nodes): `page.tsx`, `AdminIndexPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (2 nodes): `page.tsx`, `AdminLoginPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (2 nodes): `page.tsx`, `DesignLabAdminInterviewersPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (2 nodes): `page.tsx`, `DesignLabAdminProfilePage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (2 nodes): `page.tsx`, `DesignLabAdminUploadPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (2 nodes): `page.tsx`, `DesignLabPublishedReportPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (2 nodes): `page.tsx`, `DesignLabReportsDashboardPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (2 nodes): `page.tsx`, `DesignLabReportsDashboardPlaygroundPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (2 nodes): `layout.tsx`, `InterviewerLayout()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (2 nodes): `page.tsx`, `InterviewerIndexPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (2 nodes): `page.tsx`, `InterviewerLoginPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (2 nodes): `JsonSection.tsx`, `JsonSection()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (2 nodes): `SynthesisReportSection.tsx`, `if()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (2 nodes): `handlePointerDown()`, `AdminReportCard.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (2 nodes): `AdminDesignLabNavbar()`, `AdminDesignLabNavbar.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (2 nodes): `AdminInterviewersSandbox()`, `AdminInterviewersSandbox.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (2 nodes): `AdminProfileSandbox()`, `AdminProfileSandbox.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (2 nodes): `InterviewerReportCard.tsx`, `handlePointerDown()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (2 nodes): `AdminShell()`, `AdminShell.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (2 nodes): `InterviewerNavbar.tsx`, `InterviewerNavbar()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (2 nodes): `InterviewerShell.tsx`, `InterviewerShell()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (2 nodes): `cn()`, `button.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (2 nodes): `separator.tsx`, `cn()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (2 nodes): `Button()`, `Button.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (2 nodes): `EmptyState.tsx`, `EmptyState()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (2 nodes): `HeroPanel.tsx`, `HeroPanel()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (2 nodes): `Loader.tsx`, `Loader()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (2 nodes): `StatusBadge.tsx`, `StatusBadge()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (2 nodes): `upload-queue.spec.ts`, `login()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `version.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 66`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 67`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 68`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 69`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 70`** (1 nodes): `next-env.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 71`** (1 nodes): `next.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 72`** (1 nodes): `playwright.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 73`** (1 nodes): `postcss.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 74`** (1 nodes): `tailwind.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 75`** (1 nodes): `LoginForm.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 76`** (1 nodes): `ReviewPackageSection.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 77`** (1 nodes): `PublishedReportPreviewSandbox.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 78`** (1 nodes): `FinalInterviewReportSection.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 79`** (1 nodes): `Card.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 80`** (1 nodes): `SegmentedControl.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 81`** (1 nodes): `types.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 82`** (1 nodes): `adminInterviewersMock.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 83`** (1 nodes): `interviewerMock.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 84`** (1 nodes): `reportsDashboardMock.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 85`** (1 nodes): `Run migrations in 'offline' mode.      This configures the context with just a U`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 86`** (1 nodes): `Run migrations in 'online' mode.      In this scenario we need to create an Engi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 87`** (1 nodes): `create_canonical_records_table  Revision ID: 6ea7523611f4 Revises: a3ba4d865b1f`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 88`** (1 nodes): `add final report export fields  Revision ID: a1b2c3d4e5f7 Revises: f1a2b3c4d5`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 89`** (1 nodes): `create_applications_table  Revision ID: a3ba4d865b1f Revises: ad9fb8d26e40 Creat`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 90`** (1 nodes): `add_display_id_to_applications  Revision ID: a8b7c6d5e4f3 Revises: f7a9c1d2e3b4`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 91`** (1 nodes): `create_users_table  Revision ID: ad9fb8d26e40 Revises: fe57dd6ef27e Create Date:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 92`** (1 nodes): `create_synthesis_records_table  Revision ID: ae34404b0e2f Revises: 6ea7523611f4`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 93`** (1 nodes): `create processing jobs table  Revision ID: b2c3d4e5f6a8 Revises: a1b2c3d4e5f7`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 94`** (1 nodes): `target_state_foundation  Revision ID: b3c1f2d4e5f6 Revises: ae34404b0e2f Create`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 95`** (1 nodes): `rename file_path to storage_key  Revision ID: c3d4e5f6a7b9 Revises: b2c3d4e5f`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 96`** (1 nodes): `drop_synthesis_records  Revision ID: c4d5e6f7a8b9 Revises: b3c1f2d4e5f6 Create D`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 97`** (1 nodes): `replace_drafts_with_final_reports  Revision ID: c7d8e9f0a1b2 Revises: f9b8c7d`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 98`** (1 nodes): `restore_last_activity_default  Revision ID: d1e2f3a4b5c6 Revises: c7d8e9f0a1b`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 99`** (1 nodes): `add_review_package_to_canonical_records  Revision ID: d2f4e6a8b9c1 Revises: c4d5`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 100`** (1 nodes): `add processing job retry fields  Revision ID: d4e5f6a7b8c0 Revises: c3d4e5f6a`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 101`** (1 nodes): `create_interview_workspaces_table  Revision ID: e3f4a5b6c7d8 Revises: d1e2f3a`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 102`** (1 nodes): `add profile image fields to users  Revision ID: f1a2b3c4d5e6 Revises: e3f4a5b`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 103`** (1 nodes): `add_hidden_state_to_applications  Revision ID: f7a9c1d2e3b4 Revises: d2f4e6a8b9c`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 104`** (1 nodes): `add_last_activity_and_interviewer_hide_state  Revision ID: f9b8c7d6e5a4 Revises:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 105`** (1 nodes): `enable_uuid_extension  Revision ID: fe57dd6ef27e Revises:  Create Date: 2026-03-`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_pipeline()` connect `Community 2` to `Community 9`, `Community 3`, `Community 7`?**
  _High betweenness centrality (0.135) - this node is a cross-community bridge._
- **Why does `run_synthesis_pipeline()` connect `Community 2` to `Community 10`, `Community 11`, `Community 5`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Why does `LLMClientError` connect `Community 0` to `Community 2`, `Community 6`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `run_pipeline()` (e.g. with `extract_layout_blocks()` and `normalize_layout()`) actually correct?**
  _`run_pipeline()` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `get_application_or_404()` (e.g. with `retry_application()` and `generate_final_report()`) actually correct?**
  _`get_application_or_404()` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `LLMClientError` (e.g. with `ReportChatRoute` and `ReportChatError`) actually correct?**
  _`LLMClientError` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Builds the Stage 1.7 Call 2 prompt messages.     Instructs the LLM to generate i`, `Agent 16: Interview generator (LLM Call 2).     Makes exactly one LLM call to pr`, `Builds the Stage 1.7 Call 1 prompt messages.     Instructs the LLM to perform cr` to the rest of the system?**
  _81 weakly-connected nodes found - possible documentation gaps or missing edges._