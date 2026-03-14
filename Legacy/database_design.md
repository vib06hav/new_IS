# Database Design: AG_InterviewStandardiser

This document provides a comprehensive overview of the database architecture, schema, and persistence logic for the AG_InterviewStandardiser system.

## 1. Technology Stack
*   **Engine**: PostgreSQL (Utilizes `UUID` and `JSONB` extensions).
*   **ORM**: SQLAlchemy 1.4+ (Declarative Base).
*   **Migrations**: Alembic.
*   **Connection Pooling**: Managed via SQLAlchemy engine with configurable pool size and overflow.

## 2. Table Schemas

### 2.1 `users` Table
Stores system users and their authentication details.
*   [id](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/projection/ros_projector.py#4-50) (UUID, Primary Key): Unique identifier for the user.
*   `email` (String, Unique): User's email address.
*   [password_hash](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/auth/security.py#12-14) (String): Bcrypt-hashed password.
*   `role` (String): User's role (e.g., `admin`, `standard_user`).
*   `created_at` (DateTime): Record creation timestamp.

### 2.2 `applications` Table
Tracks individual application processing requests.
*   [id](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/projection/ros_projector.py#4-50) (UUID, Primary Key): Unique identifier for the application.
*   `uploaded_by` (UUID, Foreign Key): Reference to the `users` table.
*   `file_path` (String): Path to the uploaded PDF on the filesystem.
*   `pipeline_status` (String): Current processing state (`processing`, `complete`, `failed`).
*   `pipeline_confidence` (Numeric): Aggregate extraction confidence score (0.0 to 1.0).
*   `created_at` (DateTime): Record creation timestamp.

### 2.3 `canonical_records` Table
Stores the deterministic extraction output (Agent 11).
*   [id](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/projection/ros_projector.py#4-50) (UUID, Primary Key): Unique identifier for the record.
*   `application_id` (UUID, Foreign Key, Unique): One-to-one mapping to the `applications` table.
*   `canonical_version` (String): Version of the canonical model used (e.g., `1.1`).
*   `canonical_data` (JSONB): The full Canonical Representation JSON.
*   `created_at` (DateTime): Record creation timestamp.

### 2.4 `synthesis_records` Table
Stores the final report (ROS v1) and synthesis details.
*   [id](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/projection/ros_projector.py#4-50) (UUID, Primary Key): Unique identifier for the record.
*   `application_id` (UUID, Foreign Key, Unique): One-to-one mapping to the `applications` table.
*   [synthesis_output](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/policy/guard.py#31-163) (JSONB): The full ROS v1 JSON artifact (including Pages 1-5).
*   `policy_passed` (Boolean): Flag indicating if the output passed the Agent 13 policy guard.
*   `policy_violations_log` (JSONB): Detailed logs of any policy violations detected during validation.
*   `created_at` (DateTime): Record creation timestamp.

## 3. Key Architectural Decisions

### 3.1 JSONB for Flexible Schemas
The system uses PostgreSQL's `JSONB` type for both `canonical_data` and [synthesis_output](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/policy/guard.py#31-163). 
*   **Rationale**: The interview standardization process involves complex, nested data that can vary significantly between applications. `JSONB` allows for flexible storage while still supporting efficient querying and indexing of internal keys.
*   **Isolation**: Separation of `canonical_records` and `synthesis_records` ensures that the "Internal Source of Truth" is decoupled from the "Presentation Report."

### 3.2 UUID for Primary Keys
The system uses UUIDs (specifically Version 4) for all primary and foreign keys.
*   **Rationale**: Ensures data portability, prevents ID enumeration, and allows for safe ID generation even before records are committed to the database.

### 3.3 Relationships
The relationships are primarily one-to-one between an [Application](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/models/application.py#7-16) and its [CanonicalRecord](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/models/canonical_record.py#7-15) / [SynthesisRecord](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/models/synthesis_record.py#7-16). This keeps the database lean and prevents complex join overhead during report retrieval.

## 4. Migration Strategy
Migrations are managed using Alembic. Key historical migrations include:
*   `fe57dd6ef27e`: Enabling the `uuid-ossp` PostgreSQL extension.
*   `ad9fb8d26e40`: Creation of the `users` table.
*   `a3ba4d865b1f`: Creation of the `applications` table.
*   `6ea7523611f4`: Creation of the `canonical_records` table.
*   `ae34404b0e2f`: Creation of the `synthesis_records` table.

## 5. Persistence Workflow
1.  **PDF Upload**: An [Application](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/models/application.py#7-16) record is created with a `failed` status (until processing finishes).
2.  **Canonical Assembly**: Upon successful extraction (Agent 11), a [CanonicalRecord](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/models/canonical_record.py#7-15) is inserted.
3.  **Synthesis & Validation**: After synthesis (Agent 12) and policy check (Agent 13), a [SynthesisRecord](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/models/synthesis_record.py#7-16) is inserted.
4.  **Final Update**: The [Application](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/models/application.py#7-16) record is updated with `pipeline_status = 'complete'` and the aggregate confidence score.
