# Features of AG Interview Standardiser

Based on the knowledge graph extracted from the codebase, the application comprises the following core features and capabilities:

## 1. Document Extraction & Processing Engine
- **Spatial Metadata Extraction:** Parses documents (likely PDFs) and aligns spatial metadata blocks using distance-ranked pairing.
- **Record Parsing:** Dedicated pipelines for extracting academic records and activities (`extract_academic_records`, `extract_activities`).
- **Layout Normalization:** De-duplicates overlapping text blocks and ensures consistent output formatting.

## 2. LLM Orchestration & Generation
- **Multi-Stage LLM Pipeline:** Implements at least two discrete processing calls:
  - *Call 1 (Signal Interpreter):* Interprets signals and constructs evidence bundles.
  - *Call 2 (Interview Generator):* Generates the interview structure/questions.
- **Provider Agnosticism:** Uses standard interfaces to communicate with OpenAI-compatible endpoints or AICredits.
- **Output Sanitization:** Strips markdown blocks, cleans JSON, and handles pre-validation auto-repairs on LLM output.

## 3. Policy & Guardrails
- **Automated Moderation:** Enforces prohibited terms via a `PolicyConfig`.
- **Violation Tracking:** Checks inputs and outputs for disallowed judgments and structural leaks.
- **Auto-Repair:** Silently fixes recoverable LLM output errors to ensure deterministic behavior.

## 4. Application & Workspace Management
- **Workflow Lifecycle:** Handles uploading applications, assigning them to interviewers, and advancing applications through queues.
- **Interview Workspaces:** Allows draft states for interview preparation. Users can add follow-ups, add questions, and write/clear drafts.
- **Multi-Tenant or Multi-User Views:** Separate dashboard views for Administrators and Interviewers, providing dedicated shells and routing.

## 5. Canonical Data Assembly & ROS Projection
- **Data Normalization:** Assembles unstructured data into "Canonical Records" (`AcademicEntry`, `ActivityEntry`, `EssayEntry`).
- **ROS (Record of System) Assembly:** Merges multiple pages of data (e.g., Pages 1-3, Call 1 themes, Call 2 focus) into a deterministic ROS format.
- **Data Compression:** Deterministically compresses text and projects entity IDs for frontend rendering.

## 6. Interview Refinement & Report Chat
- **Interactive Refinement:** Allows dynamic refinement of interview text (`refine_interview_text`).
- **Report Chatbot:** Context-aware chat functionality that allows users to ask questions about the generated interview reports (`answer_report_question`).

## 7. Scalability & Concurrency Guardrails
- **Job Limiting:** Includes a `GenerationJobLimiter` and `CoordinationManager` to handle concurrent LLM requests and manage capacity limits.
- **Rate Limiting & Locking:** Employs an `InMemoryRateLimiter` and caching mechanisms to prevent service abuse or overload.

## 8. Security & Authentication
- **Session Management:** Dedicated utilities for session storage, signing out, and revalidation.
- **CSRF Protection:** Hardened API layer that enforces CSRF tokens for web requests.

## 9. Evaluation Harness
- **Pipeline Testing:** A standalone deterministic evaluation pipeline (`eval_pipeline.py`) that scores agent output across the LLM stages against a baseline of acceptable sample parameters.
- **Prompt Judges:** Evaluates the quality and structure of prompt builds for Calls 1 and 2.

## 10. Design Lab & Frontend Subsystems
- **Design Lab Mode:** Dedicated sandbox routes for visualizing discrete steps (e.g., `Page4FocusAreaSandbox`, `PostgameFinalReportSandbox`).
- **Interactive UI Components:** Rich components such as Interview Overlays, Report Cards, Hero Panels, and Segmented Controls.
