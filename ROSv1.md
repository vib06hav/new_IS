# 📘 ROS v1 — Report Output Specification (Finalized, No References)

---

# Top-Level Structure

```json
{
  "report_metadata": { ... },
  "page_1_background_profile": { ... },
  "page_2_academic_and_engagement": { ... },
  "page_3_essays": { ... },
  "page_4_focus_themes": { ... },
  "page_5_question_groups": { ... }
}
```

---

# 🟦 report_metadata

```json
{
  "application_number": "string",
  "generated_at": "ISO-8601 timestamp",
  "canonical_version": "string",
  "report_version": "ROS_v1"
}
```

---

# 🟦 PAGE 1 — Background Profile

```json
{
  "identity": {
    "application_number": "string",
    "full_name": "string",
    "date_of_birth": "YYYY-MM-DD",
    "age_at_application": "string",
    "gender": "string",
    "nationality": "string",
    "city": "string",
    "state": "string",
    "country": "string"
  },
  "family_background": {
    "father": {
      "name": "string",
      "education": "string",
      "occupation": "string",
      "organization": "string|null"
    },
    "mother": {
      "name": "string",
      "education": "string",
      "occupation": "string",
      "organization": "string|null"
    }
  },
  "schooling_history": [
    {
      "entity_id": "SCH-###",
      "level": "string",
      "school_name": "string",
      "board": "string",
      "location": "string"
    }
  ],
  "academic_orientation": {
    "stream": "string",
    "preferred_major": "string"
  }
}
```

### Canonical Source Clarification (v1.1)

All Page 1 fields are derived directly from Canonical v1.1.

Specifically:

- `identity` → identifiers
- `family_background` → identifiers.family_background
- `schooling_history` → schooling_history[]
- `academic_orientation` → identifiers or extracted academic metadata

Projection must not infer missing values.

If canonical fields are null or absent, ROS must preserve null values.

No heuristic reconstruction of family or schooling data is permitted.

No:

* Category
* Financial aid
* FIR
* Blood group
* Domicile
* References

---

# 🟦 PAGE 2 — Academic + Engagement

---

## Academic Records

```json
{
  "academic_records": [
    {
      "entity_id": "ACA-###",
      "level": "string",
      "board": "string",
      "year": 0,
      "overall_percentage_or_cgpa": "number|string",
      "subjects": [
        {
          "subject": "string",
          "maximum_marks": "number|null",
          "obtained_marks": "number|null"
        }
      ]
    }
  ]
}
```

---

## Standardized Tests

(Overall + Breakdown included)

```json
{
  "standardized_tests": [
    {
      "entity_id": "TEST-###",
      "name": "string",
      "date": "YYYY-MM-DD|null",
      "overall_score": "number|null",
      "overall_percentile": "number|null",
      "breakdown": {
        "physics_percentile": "number|null",
        "mathematics_percentile": "number|null",
        "chemistry_percentile": "number|null"
      },
      "qualified_next_stage": "boolean|null"
    }
  ]
}
```

---

## Additional Tests

```json
{
  "additional_tests": [
    {
      "entity_id": "TEST-ADD-###",
      "name": "string",
      "date": "string|null"
    }
  ]
}
```

---

## Extracurricular Activities

```json
{
  "extracurricular_activities": [
    {
      "entity_id": "ACT-###",
      "name": "string",
      "level": "string",
      "years_of_participation": "number|null",
      "details": "string|null"
    }
  ]
}
```

---

## Co-Curricular Activities

```json
{
  "co_curricular_activities": [
    {
      "entity_id": "ACT-###",
      "name": "string",
      "level": "string",
      "years_of_participation": "number|null",
      "achievement": "string|null"
    }
  ]
}
```

---

## Leadership Roles (Separate)

```json
{
  "leadership_roles": [
    {
      "entity_id": "LEAD-###",
      "position": "string",
      "years": "number|null",
      "responsibilities": "string|null"
    }
  ]
}
```
### Activity Classification Rule (Deterministic)

Activity grouping in ROS Page 2 is based strictly on canonical `activity_type`.

Mapping:

- activity_type == "leadership" → leadership_roles
- activity_type == "extracurricular" → extracurricular_activities
- activity_type == "co_curricular" → co_curricular_activities
- activity_type == "other" → extracurricular_activities (default bucket unless otherwise specified)

Projection must not reclassify activities.
Classification occurs during deterministic extraction only.
---

# 🟦 PAGE 3 — Essays (Full Text + Deterministic Highlights)

```json
{
  "essays": [
    {
      "entity_id": "ESS-###",
      "prompt": "string",
      "full_text": "string",
      "word_count": "number",
      "highlights": [
        {
          "start_char": "number",
          "end_char": "number",
          "referenced_entity_ids": ["string"]
        }
      ]
    }
  ]
}
```

No LLM commentary here.
Highlights strictly deterministic.

---

# 🟦 PAGE 4 — Focus Themes (LLM Structured)

```json
{
  "themes": [
    {
      "theme_id": "THEME-###",
      "title": "string",
      "description": "string",
      "referenced_entity_ids": ["string"]
    }
  ]
}
```

Rules:

* Every referenced_entity_id must exist in canonical.
* No free-floating references.
* No evaluative language.
* No ranking.

---

# 🟦 PAGE 5 — Question Groups

```json
{
  "question_groups": [
    {
      "theme_id": "THEME-###",
      "group_title": "string",
      "questions": ["string"]
    }
  ]
}
```

Each group must link to a valid theme_id.

---

# 🔒 ROS v1 Is Now Locked

* 5 pages
* No references
* Expandable-ready JSON
* Subject-level data retained
* Percentile breakdown retained
* Leadership separate
* Additional tests retained
* Deterministic highlight model
* Anchored LLM themes
* Anchored question groups
* Single LLM call sufficient

---