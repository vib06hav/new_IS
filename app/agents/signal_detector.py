import re

PROHIBITED_TERMS = [
    "Strength", "Weakness", "Outstanding", "Exceptional", "Deficiency",
    "Below average", "Underperformance", "High potential", "Top candidate",
    "Risk factor", "Admit", "Reject", "Likelihood", "Impressive",
    "Concerning", "Excellent", "Poor", "Weak", "Strong",
    "Competitive", "Uncompetitive"
]

ALLOWED_SIGNAL_TYPES = [
    "domain_concentration", "leadership_presence",
    "academic_distribution", "cross_section_pattern",
    "test_performance_pattern"
]

def detect_signals(canonical: dict, entity_id_map: list) -> list[dict]:
    """
    Agent 12: Rule-based deterministic signal detection.
    Analyzes canonical representation and derives structured signals.
    """
    signals = []
    entity_lookup = {e["entity_id"]: e for e in entity_id_map}
    
    # helper to check for prohibited language
    def check_prohibited(text: str):
        if not text:
            return
        for term in PROHIBITED_TERMS:
            if re.search(re.escape(term), text, re.IGNORECASE):
                raise RuntimeError(f"Prohibited language detected: '{term}' in '{text}'")

    # 2. domain_concentration (Science/Math focus)
    science_math_keywords = ["physics", "chemistry", "mathematics", "biology", "computer", "science"]
    all_subjects = []
    for entry in canonical.get("academic_entries", []):
        for sub in entry.get("subject_entries", []):
            all_subjects.append(sub.get("subject_name", "").lower())
    
    concentration_count = sum(1 for s in all_subjects if any(kw in s for kw in science_math_keywords))
    if concentration_count >= 4:
        # Reference all academic entries
        aca_ids = [e["entity_id"] for e in entity_id_map if e.get("collection") == "academic_entries"]
        signals.append({
            "signal_id": f"DET-{len(signals)+1:03}",
            "signal_type": "domain_concentration",
            "observation": f"Academic profile shows concentration of {concentration_count} entries in science and mathematics domains.",
            "referenced_entity_ids": aca_ids,
            "source_collection": "academic_entries"
        })

    # 3. leadership_presence
    leadership_acts = [act for act in canonical.get("activity_entries", []) if act.get("activity_type") == "leadership"]
    if leadership_acts:
        ent_ids = []
        for lact in leadership_acts:
            descriptor = lact.get("activity_name") or lact.get("position_title")
            eid = next((e["entity_id"] for e in entity_id_map if e.get("collection") == "activity_entries" and e.get("descriptor") == descriptor), None)
            if eid: ent_ids.append(eid)
        
        if ent_ids:
            signals.append({
                "signal_id": f"DET-{len(signals)+1:03}",
                "signal_type": "leadership_presence",
                "observation": f"Applicant held leadership positions in {len(leadership_acts)} activities.",
                "referenced_entity_ids": ent_ids,
                "source_collection": "activity_entries"
            })

    # 4. academic_distribution (High performance consistency)
    scores = []
    for entry in canonical.get("academic_entries", []):
        score_val = entry.get("score_raw")
        if score_val:
            try:
                nums = re.findall(r"\d+\.?\d*", str(score_val))
                if nums: scores.append(float(nums[0]))
            except ValueError: continue
    
    if scores and all(s >= 90 for s in scores):
        aca_ids = [e["entity_id"] for e in entity_id_map if e.get("collection") == "academic_entries"]
        signals.append({
            "signal_id": f"DET-{len(signals)+1:03}",
            "signal_type": "academic_distribution",
            "observation": "Academic scores across all recorded levels show consistent performance at 90% or above.",
            "referenced_entity_ids": aca_ids,
            "source_collection": "academic_entries"
        })

    # 6. cross_section_pattern (Recursive term "Robotics" - example for Ananya)
    keywords = ["robotics", "debate", "community", "service"]
    for kw in keywords:
        found_in = []
        ent_ids = []
        # Check activities
        for act in canonical.get("activity_entries", []):
            if kw in str(act.get("activity_name", "")).lower() or kw in str(act.get("position_title", "")).lower():
                eid = next((e["entity_id"] for e in entity_id_map if e.get("collection") == "activity_entries" and e.get("descriptor") == act.get("activity_name")), None)
                if eid:
                    ent_ids.append(eid)
                    if "activity" not in found_in: found_in.append("activity")
        # Check essays
        for essay in canonical.get("essay_entries", []):
            if kw in str(essay.get("raw_text", "")).lower():
                eid = next((e["entity_id"] for e in entity_id_map if e.get("collection") == "essay_entries" and e.get("descriptor") == essay.get("essay_identifier")), None)
                if eid:
                    ent_ids.append(eid)
                    if "essay" not in found_in: found_in.append("essay")
        
        if len(found_in) >= 2:
            signals.append({
                "signal_id": f"DET-{len(signals)+1:03}",
                "signal_type": "cross_section_pattern",
                "observation": f"Term '{kw}' appears across {', '.join(found_in)} sections.",
                "referenced_entity_ids": ent_ids,
                "source_collection": "multiple"
            })

    # 8. test_performance_pattern (Consistent test scores)
    for test in canonical.get("test_entries", []):
        score_val = test.get("total_score")
        if score_val:
            try:
                nums = re.findall(r"\d+\.?\d*", str(score_val))
                if nums:
                    eid = next((e["entity_id"] for e in entity_id_map if e.get("collection") == "test_entries" and e.get("descriptor") == test.get("test_name")), None)
                    if eid:
                        signals.append({
                            "signal_id": f"DET-{len(signals)+1:03}",
                            "signal_type": "test_performance_pattern",
                            "observation": f"Score of {score_val} achieved in {test.get('test_name')}.",
                            "referenced_entity_ids": [eid],
                            "source_collection": "test_entries"
                        })
            except ValueError: continue

    # Final Validation
    for s in signals:
        if s["signal_type"] not in ALLOWED_SIGNAL_TYPES:
            raise RuntimeError(f"Invalid signal type: {s['signal_type']}")
        
        check_prohibited(str(s["observation"]))
        
        for eid in s["referenced_entity_ids"]:
            if eid not in entity_lookup:
                raise RuntimeError(f"Entity ID {eid} not found in entity_id_map")
    
    return signals
