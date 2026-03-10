def evaluate(ros_document: dict) -> str:
    score = 0
    max_score = 100
    report_lines = ["\n" + "="*40, "PARSER EVALUATION REPORT", "="*40]

    # 1. Academic record count sanity (20 pts)
    page_2 = ros_document.get("page_2_academic_and_engagement", {})
    academics = page_2.get("academic_records", [])
    if len(academics) >= 2:
        score += 20
        report_lines.append(f"[PASS] Academic records found: {len(academics)} (20/20)")
    elif len(academics) == 1:
        score += 10
        report_lines.append(f"[PARTIAL] Academic records found: {len(academics)} (10/20)")
    else:
        report_lines.append(f"[FAIL] No academic records found. (0/20)")

    # 2. Essay presence and minimum length (20 pts)
    page_3 = ros_document.get("page_3_essays", {})
    essays = page_3.get("essays", [])
    valid_essays = [e for e in essays if e.get("word_count", 0) >= 100]
    if len(valid_essays) >= 1:
        score += 20
        report_lines.append(f"[PASS] Minimum required essays found: {len(valid_essays)} (20/20)")
    elif len(essays) >= 1:
        score += 10
        report_lines.append(f"[PARTIAL] Essays found but below word count. (10/20)")
    else:
        report_lines.append(f"[FAIL] No essays found. (0/20)")

    # 3. Subject table detection via numeric marks (20 pts)
    has_subjects_with_marks = False
    for a in academics:
        subjects = a.get("subject_entries", [])
        for s in subjects:
            if s.get("score_raw") or s.get("predicted_score_raw"):
                has_subjects_with_marks = True
                break
        if has_subjects_with_marks:
            break
            
    if has_subjects_with_marks:
        score += 20
        report_lines.append(f"[PASS] Subject tables with numeric marks detected. (20/20)")
    else:
        report_lines.append(f"[FAIL] No subject tables with numeric marks detected. (0/20)")

    # 4. Extracurricular activity presence (20 pts)
    activities = page_2.get("extracurricular_activities", []) + page_2.get("co_curricular_activities", []) + page_2.get("leadership_roles", [])
    if len(activities) > 0:
        score += 20
        report_lines.append(f"[PASS] Extracurricular/Co-curricular activities found: {len(activities)} (20/20)")
    else:
        report_lines.append(f"[FAIL] No extracurricular activities found. (0/20)")

    # 5. Standardized test detection (20 pts)
    tests = page_2.get("standardized_tests", [])
    if len(tests) > 0:
        score += 20
        report_lines.append(f"[PASS] Standardized tests found: {len(tests)} (20/20)")
    else:
        # Standardized tests might be optional for some applicants, but evaluating parsing capability means we expect it normally or we just give score 0.
        report_lines.append(f"[INFO] No standardized tests found. (0/20)")

    report_lines.append("-" * 40)
    report_lines.append(f"TOTAL PARSER SCORE: {score}/{max_score}")
    report_lines.append("="*40 + "\n")
    
    return "\n".join(report_lines)
