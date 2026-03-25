import re

filepath = r"c:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\app\agents\projection_builder.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Delete compact_mode = ...
content = re.sub(r'    compact_mode = settings\.LLM_PAYLOAD_MODE == "compact"\n\n', '', content)
# Make sure to handle if the newlines are different
content = re.sub(r'[ \t]*compact_mode = .*?\n', '', content)

# 2. Delete _compact_parent
content = re.sub(r'    def _compact_parent\(parent_data\):.*?    return compact_parent\n\n', '', content, flags=re.DOTALL)

# 3. Delete _build_activity_summary
content = re.sub(r'    def _build_activity_summary\(entry\):.*?    return "; "\.join\(parts\)\n\n', '', content, flags=re.DOTALL)

# 4. _build_test_sections compact branch
test_section_compact = r'        if compact_mode:\n            highest_score = max\(score for score, _ in section_scores\)\n            lowest_score, lowest_label = min\(section_scores, key=lambda item: item\[0\]\)\n            if highest_score - lowest_score >= 8 and lowest_label:\n                sections\.append\(\{"label": lowest_label, "score": f"\{lowest_score:\.2f\}"\.rstrip\("0"\)\.rstrip\("\."\)\}\)\n            return sections\n\n'
content = re.sub(test_section_compact, '', content)

# 5. Applicant context full_name
full_name_old = r'    if not compact_mode:\n        context\["full_name"\] = identifiers\.get\("full_name"\)'
full_name_new = r'    context["full_name"] = identifiers.get("full_name")'
content = content.replace(full_name_old, full_name_new)

# 6. Family background compact mode branch
family_old = r'                if compact_mode:\n                    cleaned_parent = _compact_parent\(parent_data\)\n                else:\n                    cleaned_parent = \{k: v for k, v in parent_data\.items\(\) if v is not None\}\n'
family_new = r'                cleaned_parent = {k: v for k, v in parent_data.items() if v is not None}\n'
content = content.replace(family_old, family_new)

# 7. Academic profile branching
aca_old = r'''        if not compact_mode:
            aca_entry\["school_name"\] = entry\.get\("school_name"\)
            aca_entry\["board_name"\] = entry\.get\("board_name"\)
        else:
            previous_entry = academic_entries\[academic_index - 1\] if academic_index > 0 else None
            if previous_entry is None or entry\.get\("school_name"\) != previous_entry\.get\("school_name"\):
                aca_entry\["school_name"\] = entry\.get\("school_name"\)
            if previous_entry is None or entry\.get\("board_name"\) != previous_entry\.get\("board_name"\):
                aca_entry\["board_name"\] = entry\.get\("board_name"\)'''

aca_new = r'''        aca_entry["school_name"] = entry.get("school_name")
        aca_entry["board_name"] = entry.get("board_name")'''
content = re.sub(aca_old, aca_new, content)

# 7b. Academic profile subjects branching
sub_old = r'''        if compact_mode:
            subjects = \[\]
            subject_scores = \[\]
            for sub in entry\.get\("subject_entries", \[\]\):
                score = _safe_float\(sub\.get\("score_raw"\)\)
                subject_name = _clean_text\(sub\.get\("subject_name"\)\)
                if score is None or not subject_name:
                    continue
                subject_scores\.append\(\(score, subject_name\)\)
            if subject_scores:
                top_score, top_subject = max\(subject_scores, key=lambda item: item\[0\]\)
                low_score, low_subject = min\(subject_scores, key=lambda item: item\[0\]\)
                aca_entry\["subject_summary"\] = \{
                    "highest_subject": top_subject,
                    "highest_score": f"\{top_score:\.2f\}"\.rstrip\("0"\)\.rstrip\("\."\),
                    "lowest_subject": low_subject,
                    "lowest_score": f"\{low_score:\.2f\}"\.rstrip\("0"\)\.rstrip\("\."\)
                \}
        else:
            subjects = \[\]
            for sub in entry\.get\("subject_entries", \[\]\):'''

sub_new = r'''        subjects = []
        for sub in entry.get("subject_entries", []):'''
content = re.sub(sub_old, sub_new, content)

# 8. Essay profile text length
essay_old = r'400 if compact_mode else 1000'
essay_new = r'1000'
content = content.replace(essay_old, essay_new)

# 9. Activity profile compact mode return
act_old = r'''        if compact_mode:
            summary = _build_activity_summary\(entry\)
            if not summary:
                continue
            act_entry\["summary"\] = summary
            activity_profile\.append\(act_entry\)
            continue
        
'''
content = re.sub(act_old, '', content)

# 10. Entity ID map filtering
ent_old = r'''    if compact_mode:
        referenced_ids = set\(\)
        for section_name in \["academic_profile", "test_profile", "essay_profile", "activity_profile"\]:
            for entry in locals\(\)\.get\(section_name, \[\]\):
                if isinstance\(entry, dict\) and entry\.get\("entity_id"\):
                    referenced_ids\.add\(entry\["entity_id"\]\)
        for signal in deterministic_signals:
            for entity_id in signal\.get\("referenced_entity_ids", \[\]\) or \[\]:
                if entity_id:
                    referenced_ids\.add\(entity_id\)
        compact_map = \[\]
        seen = set\(\)
        for entry in entity_id_map:
            entity_id = entry\.get\("entity_id"\)
            if entity_id not in referenced_ids or entity_id in seen:
                continue
            seen\.add\(entity_id\)
            compact_entry = \{"entity_id": entity_id\}
            descriptor = entry\.get\("descriptor"\)
            if descriptor:
                compact_entry\["descriptor"\] = descriptor
            compact_map\.append\(compact_entry\)
        projection_entity_map = compact_map'''
content = re.sub(ent_old, '', content)

# 11. academic_summary conditional
acad_sum_old = r'    if compact_mode and academic_summary:\n        projection\["academic_summary"\] = academic_summary'
acad_sum_new = r'    if academic_summary:\n        projection["academic_summary"] = academic_summary'
content = re.sub(acad_sum_old, acad_sum_new, content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Done editing.")
