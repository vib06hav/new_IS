## Final Canonical JSON Refinement Decisions

---

### Remove Entirely

**1. `extracurricular_activities[]`**
Duplicate of entries in `activity_entries`. Presentation grouping belongs to the ROS projection layer, not canonical.

**2. `co_curricular_activities[]`**
Same reason.

**3. `leadership_activities[]`**
Same reason.

**4. `component_tags: []` on academic entries**
Always empty. Remove.

**5. `component_tag: null` on subject entries**
Always null. Remove.

**6. `original_row_content` on activity entries**
Raw extraction artifact. Not applicant data. Belongs in extraction logs if needed for debugging, not in canonical.

**7. `upload_flag` on activity entries**
Extraction process flag. Not a property of the activity itself. Remove.

**8. `category: null` on activity entries**
Never populated and superseded by `activity_type`. Remove.

**9. `declared_preferences: {}`**
Empty scaffolding. Introduce only when the field has real data to populate.

**10. `demographic_flags: {}`**
Same reason.

**11. `duplication_ratio` on essay entries**
Derived metric, not a raw extracted value. Remove.

**12. `character_count` on essay entries**
Redundant given `word_count` is already present. Remove.

**13. `profile_meta`**
Extraction infrastructure metadata — page count, layout block count, timestamp, detected section labels. Describes the PDF and the extraction process, not the applicant. `extraction_timestamp` specifically breaks deterministic stability by making two canonical representations of the same applicant non-identical on re-extraction. Remove from canonical. Store as a separate column on the `canonical_records` row if debugging access is needed.

---

### Keep

**14. `placeholder_flag` on essay entries**
Binary fact about submission quality. Legitimate canonical data.

**15. `short_response_flag` on essay entries**
Same reason.

**16. `confidence_score` per entry**
Required by Agent 10 integrity analyzer.

**17. `schooling_history[]`**
Architecturally correct as a separate collection — institutional history may exist independently from performance records. Keep the collection. However, extraction logic should be reviewed to avoid populating it with entries that are already fully represented in `academic_entries` with no additional information. The collection earns its place when schooling data and academic performance data are not one-to-one.

---

### Extend — Activity Entry Schema

The current `activity_entry` schema is too narrow to hold leadership data without information loss. The schema must be extended to accommodate the structurally different fields present in the Leadership section of the PDF.

**Current schema** forces leadership entries into fields that don't map correctly (`activity_name: "Yes"`, `description_raw` containing form question text).

**Extended schema:**

```json
{
  "entry_id": "UUID",
  "activity_type": "extracurricular | co_curricular | leadership",
  "activity_name": "string | null",
  "position_title": "string | null",
  "level": "string | null",
  "duration": "string | null",
  "achievement": "string | null",
  "roles_and_responsibilities": "string | null",
  "description_raw": "string | null",
  "confidence_score": 0.0
}
```

**Field population by section type:**

| Field | Extra-Curricular | Co-Curricular | Leadership |
|---|---|---|---|
| `activity_type` | `"extracurricular"` | `"co_curricular"` | `"leadership"` |
| `activity_name` | Populated | Populated | null |
| `position_title` | null | null | Populated |
| `level` | Populated | Populated | null |
| `duration` | Populated | Populated | Populated |
| `achievement` | Populated | Populated | null |
| `roles_and_responsibilities` | null | null | Populated |
| `description_raw` | null | null | null |

`description_raw` is retained in the schema as a safety field for extraction edge cases where structured mapping fails. It should be null for all clean extractions.

---

### Extraction Behavior — Keep Separate, Merge Output

The extractor (Agent 7) correctly processes the three PDF sections separately because their table schemas are structurally different. This is not what changes. What changes is the output:

- Three separate extraction passes → one merged `activity_entries[]` in canonical
- `activity_type` is the discriminator
- No separate typed arrays in canonical at any level

---

### Integrity Analyzer — Flag Empty Section Errors

Agent 10 must be extended to detect the class of error seen in the Aarav Jain parsing case — where an empty leadership section caused the extractor to pick up adjacent form question-answer text as an activity entry. Indicators to flag:

- `activity_name` containing values like `"Yes"` or `"No"`
- `description_raw` containing question-like text patterns
- `position_title` null on a leadership entry with no other populated fields
- Duration null and achievement null simultaneously on any entry

---

### Final Canonical Activity Structure

```json
"activity_entries": [
  {
    "entry_id": "UUID",
    "activity_type": "extracurricular",
    "activity_name": "Chess",
    "position_title": null,
    "level": "State",
    "duration": "6",
    "achievement": "State 4th ranked",
    "roles_and_responsibilities": null,
    "description_raw": null,
    "confidence_score": 0.9
  },
  {
    "entry_id": "UUID",
    "activity_type": "leadership",
    "activity_name": null,
    "position_title": "Class Monitor",
    "level": null,
    "duration": "3",
    "achievement": null,
    "roles_and_responsibilities": "Check schedule everyday and verify notes, project submissions",
    "description_raw": null,
    "confidence_score": 0.9
  }
]
```

---

### Summary Table

| Item | Decision |
|---|---|
| `extracurricular_activities[]` | Remove |
| `co_curricular_activities[]` | Remove |
| `leadership_activities[]` | Remove |
| `component_tags[]` on academic entries | Remove |
| `component_tag` on subject entries | Remove |
| `original_row_content` on activities | Remove |
| `upload_flag` on activities | Remove |
| `category` on activities | Remove |
| `declared_preferences` | Remove |
| `demographic_flags` | Remove |
| `duplication_ratio` on essays | Remove |
| `character_count` on essays | Remove |
| `profile_meta` | Remove from canonical |
| `placeholder_flag` on essays | Keep |
| `short_response_flag` on essays | Keep |
| `confidence_score` per entry | Keep |
| `schooling_history[]` | Keep, review extraction logic |
| Activity entry schema | Extend with `position_title`, `achievement`, `roles_and_responsibilities` |
| Three-section activity extraction | Keep separate at extraction level, merge into single `activity_entries[]` in canonical |
| Agent 10 empty section detection | Extend to catch malformed activity entries |