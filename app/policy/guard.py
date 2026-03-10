import re
import uuid
from typing import Dict, Any, List, Tuple
from app.policy.config import PolicyConfig

def _scan_text(text: str, rules: List[str]) -> List[Dict[str, Any]]:
    """
    Scans a block of text against a list of prohibited phrases.
    Uses basic substring matching and word boundary regex for robustness.
    """
    violations = []
    if not text:
        return violations
        
    lower_text = text.lower()
    
    for phrase in rules:
        lower_phrase = phrase.lower()
        if lower_phrase in lower_text:
            violations.append({
                "violation_id": str(uuid.uuid4()),
                "phrase_matched": phrase,
                "context": text[:100] + "..." if len(text) > 100 else text
            })
    return violations

import logging

logger = logging.getLogger(__name__)

def validate_synthesis_output(synthesis_output: Dict[str, Any], entity_map: Dict[str, str], sanitize: bool = False) -> Dict[str, Any]:
    """
    Agent 13 - Output Validation Filter.
    Scans LLM output to detect evaluative phasing and structural integrity (themes, entity linking).
    Returns: passed (bool), sanitized_output, violations_log
    """
    logger.debug("Starting Agent 13 validation filter.")
    logger.debug(f"Using entity_map with {len(entity_map)} total references.")
    rules = PolicyConfig.get_prohibited_terms()
    violations_log = []
    
    passed = True
    
    # Validation F.1.1: JSON structure conformance
    if not isinstance(synthesis_output, dict):
        violations_log.append({"violation_id": str(uuid.uuid4()), "field": "root", "type": "structure_error", "context": "Root is not a JSON object."})
        return {"passed": False, "sanitized_output": None, "violations_log": violations_log}
        
    themes = synthesis_output.get("themes")
    question_groups = synthesis_output.get("question_groups")
    
    if themes is None or not isinstance(themes, list):
        violations_log.append({"violation_id": str(uuid.uuid4()), "field": "themes", "type": "structure_error", "context": "Missing or invalid 'themes' array."})
        passed = False
        
    if question_groups is None or not isinstance(question_groups, list):
        violations_log.append({"violation_id": str(uuid.uuid4()), "field": "question_groups", "type": "structure_error", "context": "Missing or invalid 'question_groups' array."})
        passed = False
        
    if not passed:
        return {"passed": False, "sanitized_output": None, "violations_log": violations_log}

    # Prepare the sanitized structure copy
    sanitized_output = {
        "themes": [],
        "question_groups": []
    }
    
    known_theme_ids = set()
    valid_entity_ids = set(entity_map.values())
    
    # 1. Scan Themes
    for idx, theme in enumerate(themes):
        if not isinstance(theme, dict): continue
        theme_id = theme.get("theme_id")
        
        # Validation F.1.2: theme_id uniqueness
        if theme_id in known_theme_ids:
            violations_log.append({"violation_id": str(uuid.uuid4()), "field": f"themes[{idx}]", "type": "duplicate_theme_id", "context": f"Duplicate theme_id: {theme_id}"})
            passed = False
        elif theme_id:
            known_theme_ids.add(theme_id)
            
        sanitized_theme = {
            "theme_id": theme_id,
            "title": theme.get("title", ""),
            "description": theme.get("description", ""),
            "referenced_entity_ids": theme.get("referenced_entity_ids", [])
        }
        
        # Validation F.1.3 & F.1.5: referenced_entity_ids existence
        refs = theme.get("referenced_entity_ids", [])
        if not isinstance(refs, list): refs = []
        for ref in refs:
            if ref not in valid_entity_ids:
                violations_log.append({"violation_id": str(uuid.uuid4()), "field": f"themes[{idx}].referenced_entity_ids", "type": "invented_entity_id", "context": f"Invented entity ID: {ref}"})
                passed = False
                
        # Prohibited language detection (title and description)
        for field in ["title", "description"]:
            text = sanitized_theme.get(field, "")
            violations = _scan_text(text, rules)
            for v in violations:
                v["field"] = f"themes[{idx}].{field}"
                v["type"] = "prohibited_language"
                violations_log.append(v)
                passed = False
                
        sanitized_output["themes"].append(sanitized_theme)

    # 2. Scan Question Groups
    for idx, qg in enumerate(question_groups):
        if not isinstance(qg, dict): continue
        theme_id = qg.get("theme_id")
        
        # Validation F.1.4: question_groups.theme_id linkage
        if theme_id not in known_theme_ids:
            violations_log.append({"violation_id": str(uuid.uuid4()), "field": f"question_groups[{idx}].theme_id", "type": "broken_linkage", "context": f"References non-existent theme_id: {theme_id}"})
            passed = False
            
        sanitized_qg = {
            "theme_id": theme_id,
            "group_title": qg.get("group_title", ""),
            "questions": qg.get("questions", [])
        }
        
        # Prohibited language in title
        title_text = sanitized_qg["group_title"]
        violations = _scan_text(title_text, rules)
        for v in violations:
            v["field"] = f"question_groups[{idx}].group_title"
            v["type"] = "prohibited_language"
            violations_log.append(v)
            passed = False
            
        # Prohibited language in questions
        questions = qg.get("questions", [])
        if not isinstance(questions, list): questions = []
        for q_idx, q_text in enumerate(questions):
            q_violations = _scan_text(q_text, rules)
            for v in q_violations:
                v["field"] = f"question_groups[{idx}].questions[{q_idx}]"
                v["type"] = "prohibited_language"
                violations_log.append(v)
                passed = False
                
        sanitized_output["question_groups"].append(sanitized_qg)

    
    if len(violations_log) > 0:
        logger.debug(f"Validation failed with {len(violations_log)} violations.")
        for v in violations_log:
            logger.debug(f"Violation Trigger: {v}")
    else:
        logger.debug("Validation succeeded.")

    return {
        "passed": passed,
        "sanitized_output": sanitized_output if passed else None,
        "violations_log": violations_log,
        "policy_version": PolicyConfig.get_version()
    }
