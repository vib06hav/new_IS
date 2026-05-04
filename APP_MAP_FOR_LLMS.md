# AG Interview Standardiser: App Map for LLMs

## What This App Is

AG Interview Standardiser is a full admissions interview workflow system. It takes applicant PDFs, extracts structured report data, synthesizes interview-ready focus areas and question groups, supports interviewers during live interviews, helps refine post-interview notes, and produces a final interview report.

The app has three major product faces:

- a public landing/support surface
- an admin workflow for upload, processing, report generation, and assignment
- an interviewer workflow for prep, live interview, postgame, and final report review

It also has a report copilot that answers questions about the report and the interview workflow using only the currently available report/workspace context.

## Product Identity

This is not a generic chatbot app and not a generic ATS.

It is best understood as:

- a document-to-interview-prep pipeline
- a guided interviewer workflow
- a post-interview reporting system
- a workflow-aware report copilot

## Core Roles

### Admin

Admin users:

- upload source application PDFs
- review processing status
- generate final reports after deterministic extraction completes
- assign interviewers
- manage visibility and completed outputs

### Interviewer

Interviewers:

- access assigned applications
- review Pages 1-5
- create and edit an interview workspace
- launch the live interview overlay
- mark question outcomes during the interview
- complete postgame review
- publish the final interview report on Page 6

### Public Visitor

Public visitors only interact with:

- the landing page
- support/demo request surface
- portal entry/sign-in paths

## End-to-End Workflow

The app has two related state machines:

### Application lifecycle

- `PROCESSING`: source PDF uploaded, deterministic extraction job queued/running
- `PROCESSED`: Pages 1-3 are available
- `READY`: final report synthesis exists, including Pages 4-5
- `ASSIGNED`: an interviewer owns the application
- `COMPLETE`: interview workflow is finished and final interview report is available
- `FAILED`: processing or generation failed

### Interview workspace lifecycle

- `draft`: workspace created, prep/configure stage
- `launched`: live interview in progress
- `postgame`: live interview ended, review/finalization stage
- `completed`: final interview report published

### Main flow

1. Admin uploads a PDF through `/applications/upload`.
2. The backend stores the source PDF in object storage and creates a `PROCESSING` application.
3. A background processing job runs the deterministic extraction pipeline.
4. Deterministic extraction produces the review package / Pages 1-3.
5. Admin generates a final report from the canonical structured data.
6. Final report synthesis produces Pages 4-5 and moves the application to `READY`.
7. Admin assigns the application to an interviewer, moving it to `ASSIGNED`.
8. Interviewer opens the application and creates a workspace seeded from the final report.
9. Interviewer configures/refines themes and questions in workspace `draft`.
10. Interviewer launches the workspace into the live overlay.
11. Interviewer marks question outcomes, notes, and follow-ups during the live interview.
12. Interviewer finishes the live interview, moving the workspace to `postgame`.
13. Interviewer refines notes/summary and publishes the final interview report.
14. Publishing marks the workspace `completed` and the application `COMPLETE`.
15. Page 6 becomes the primary post-interview review surface.

## The 6-Page Model

The product revolves around a 6-page report model.

### Page 1: Overview

Purpose:

- baseline applicant identity and context

Typical content:

- personal/background profile
- schooling context
- family/additional profile information

### Page 2: Academics and Activities

Purpose:

- evidence layer for achievement and engagement

Typical content:

- academic records across years
- test scores
- extracurriculars
- co-curriculars
- leadership/activity details

### Page 3: Writing

Purpose:

- essay and writing-based evidence

Typical content:

- essays
- excerpts
- narrative themes from applicant writing

### Page 4: Focus Areas

Purpose:

- synthesized interpretation of the earlier evidence

Typical content:

- themes
- signals
- unifying axes
- interview directions

This page answers:

- what stands out?
- what tensions or themes matter most?
- what should the interviewer focus on?

### Page 5: Questions

Purpose:

- convert Page 4 themes into interview action

Typical content:

- grouped interview questions
- question sets tied to themes

This page answers:

- what should I ask?
- how do I probe this theme?

### Page 6: Final Interview Report

Purpose:

- post-interview output and review record

Typical content:

- final summary
- asked question outcomes
- notes/results from the completed interview

Important meaning:

- Page 6 only exists after interview completion
- once Page 6 is active, prep/live actions are no longer the default mode

## Before / During / After Interview

### Before interview

Key surfaces:

- Pages 1-5
- configure workspace

Primary tasks:

- understand the applicant
- review evidence
- inspect focus areas
- prepare question flow
- refine/edit workspace content

### During interview

Key surface:

- overlay

Primary tasks:

- progress through questions
- mark question status
- add notes
- use follow-ups
- keep structure without losing the live conversation

### After interview

Key surfaces:

- postgame
- Page 6 final report

Primary tasks:

- review outcomes
- refine summary text
- finalize/publish final interview report
- compare the live result to earlier report expectations

## Frontend Surface Map

### Public / marketing

- `frontend/app/page.tsx`: main landing page
- `frontend/app/support/page.tsx`: support/demo request surface
- `frontend/app/portal/page.tsx`: shared portal entry surface

The landing page is storytelling/marketing, not the product workspace itself.

### Admin app

Main route group:

- `frontend/app/admin`

Important surfaces:

- dashboard
- reports list
- upload
- applications detail
- assignments
- interviewers
- profile/login

Admin application detail is a key inspection surface because it shows review package, final report, workspace summary, and the copilot.

### Interviewer app

Main route group:

- `frontend/app/interviewer`

Important surfaces:

- assigned applications list/detail
- configure
- overlay
- postgame
- settings/login/dashboard

These routes are the core operator workflow of the product.

### Design lab

- `frontend/app/design-lab`

This is a design/playground area for UI reference and experimentation. It is useful for visual patterns, but should not be treated as the primary source of live product behavior.

## Backend System Map

### App entry

- `app/main.py`

Responsibilities:

- FastAPI app creation
- security middleware
- router registration
- health check
- dev admin bootstrap

### Main API domains

- `app/api/applications.py`: upload, application detail, source PDF access, final-report export, report copilot endpoint
- `app/api/admin.py`: admin list/generate/assign/retry/hide/update operations
- `app/api/interviewer.py`: interviewer-owned application/workspace/refinement actions
- `app/auth/*`: authentication, auth routing, dependencies, service logic

### Processing and orchestration

- `app/processing.py`: queueing, claiming, retrying, and running background deterministic extraction jobs
- `app/worker.py`: worker startup path
- `app/agents/orchestrator.py`: deterministic and synthesis orchestration entrypoints

### Interview workspace and postgame

- `app/interview_workspace.py`: seed-building and normalization for workspace content
- `app/interview_refinement.py`: AI-assisted postgame refinement

### Copilot

- `app/report_chat.py`: report/workflow copilot logic

This module is currently responsible for:

- validating questions
- building unified report/workflow context
- asking the LLM for grounded answers
- shaping responses into `content`, `workflow`, `action`, or `mixed`
- keeping the copilot in scope of report/workflow context only

### LLM and policy

- `app/llm/client.py`
- `app/llm/control.py`
- `app/policy/*`

These modules handle model access, capacity/limits, and policy-like constraints.

### Storage and data access

- `app/storage/service.py`: object storage / MinIO behavior
- `app/database.py`: DB session plumbing
- `app/models/*`: ORM entities

## Main Data Model

The most important entities are:

### Application

Represents a candidate/application record.

Important fields/concepts:

- `display_id`
- status
- source PDF storage key
- visibility state
- lifecycle timestamps

### ProcessingJob

Represents background deterministic extraction work.

Used for:

- queueing
- retries
- stale-job recovery

### CanonicalRecord

Represents structured/canonical extracted data from the source application.

This is the basis for later synthesis and report building.

### FinalReport

Represents synthesized report output, including Pages 4-5 and exported report content.

### Assignment

Connects an application to an interviewer.

### InterviewWorkspace

Represents the editable working interview plan and postgame state.

Important concepts:

- themes
- generated/custom questions
- follow-ups
- final summary
- status transitions

### User

Represents admins and interviewers with role-based access.

## Report and Synthesis Pipeline

There are two major stages:

### 1. Deterministic extraction

Started by:

- upload + background processing job

Purpose:

- turn the raw PDF into structured data

High-level outputs:

- Pages 1-3 review package content
- canonical records for later synthesis

### 2. Final report synthesis

Started by:

- admin `generate-report`

Purpose:

- turn canonical structured data into interviewer-ready synthesis

High-level outputs:

- Page 4 focus areas
- Page 5 question groups
- report metadata

The synthesis result is also the seed for the interviewer workspace.

## Interview Workspace Model

The workspace is seeded from final report content.

Seed behavior:

- Page 4 themes become workspace theme cards
- Page 5 question groups/questions become generated workspace questions

Workspace content then evolves through:

- interviewer edits
- status changes
- question outcomes
- follow-up additions
- postgame refinement
- final summary creation

Question status values:

- `unasked`
- `satisfactory`
- `mixed`
- `unsatisfactory`

Workspace status values:

- `draft`
- `launched`
- `postgame`
- `completed`

## Copilot Map

### What it is

The report copilot is an LLM-first assistant for the report workflow.

It is not a general-purpose assistant.

### What it can do

- explain report content
- answer questions about Pages 1-6
- explain the current page/surface
- explain workflow stages
- suggest what to do next inside the report/interview flow
- answer mixed questions that combine report insight and workflow guidance

### What it should not do

- answer unrelated coding/dev requests
- go outside the report/workflow resources provided to it
- infer missing facts not present in the report/workspace context
- judge, rank, admit, or reject the candidate

### Runtime context it uses

The copilot is aware of:

- current surface type
- current page
- workflow stage
- available actions
- Pages 1-3
- Pages 4-5 if present
- Page 6/workspace summary if present

### Where it appears

Current report-related surfaces include:

- admin application detail
- interviewer application detail
- configure
- overlay
- postgame
- final report view

### Current answer categories

- `content`
- `workflow`
- `action`
- `mixed`
- `degraded` response state when it has to fall back

## Access and Security Model

The app uses:

- role-based auth for admin/interviewer
- CSRF protection middleware
- rate limiting for sensitive AI-backed endpoints
- authorization checks on application, workspace, source PDF, and final report access

Important practical rule:

- interviewers can only access applications assigned to them
- admins can access and manage the full workflow

## Important API Flows

### Upload and processing

- upload PDF
- create `PROCESSING` application
- enqueue background deterministic pipeline

### Admin report generation

- generate final report from canonical record
- transition `PROCESSED -> READY`

### Assignment

- assign interviewer
- transition `READY -> ASSIGNED`

### Interviewer workspace

- create workspace from final report
- update draft workspace
- launch live interview
- finish into postgame
- complete into final report / `COMPLETE`

### Copilot

- `POST /applications/{application_id}/report-chat`

Used by both admin and interviewer application/report-related surfaces, subject to authorization.

## Key Entry Points for a New LLM

If you need to understand the app quickly, start here:

### Backend

- `app/main.py`
- `app/api/applications.py`
- `app/api/admin.py`
- `app/api/interviewer.py`
- `app/processing.py`
- `app/interview_workspace.py`
- `app/report_chat.py`

### Frontend

- `frontend/app/page.tsx`
- `frontend/app/admin/*`
- `frontend/app/interviewer/*`
- `frontend/components/ReportChatWidget.tsx`

### Shared contracts

- `app/api/schemas.py`
- `frontend/lib/types.ts`

## How to Reason About This Repo

### If you want product flow truth

Look at:

- current frontend routes
- application/workspace status transitions
- landing page narrative only as a product summary, not as behavior truth

### If you want backend behavior truth

Look at:

- API routers
- processing pipeline
- workspace logic
- copilot module

### If you want report-generation truth

Look at:

- processing pipeline
- canonical records
- final report generation path
- agent orchestrator modules

### If you want copilot truth

Look at:

- `app/report_chat.py`
- report-chat request/response types
- `ReportChatWidget`
- surfaces that pass page/stage/action context into the copilot

## Current Boundaries and Non-Goals

- The copilot is not meant to become a general assistant.
- The copilot is constrained to report/workflow content only.
- Candidate judgment is intentionally out of scope.
- The landing page is narrative/marketing, not the operational truth of the product.
- `legacy/` contains historical stage/spec material and naming lineage, but should not be treated as the current source of truth for live behavior.

## Historical Note

This repo contains substantial historical documentation under `legacy/`. Those documents explain earlier architecture stages and terminology, but the current app behavior should be derived from:

- current FastAPI routers
- current frontend routes/components
- current processing/workspace/copilot code

When there is a conflict, prefer current code over historical specs.
