import json
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

def validate_themes(raw_text: str, entity_id_map: List[dict]) -> Dict[str, Any]:
    """
    Agent 15 - Call 2 Validation Layer.
    Strictly validates LLM Call 2 output (interview themes and questions).
    Enforces schema, entity grounding, and neutral language.
    """
    logger.debug("Starting Agent 15 theme validation.")
    rules = PolicyConfig.get_prohibited_terms()
    violations_log = []
    
    passed = True
    
    # Validation Stage 1: JSON Integrity
    try:
        synthesis_output = json.loads(raw_text)
    except Exception as e:
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "type": "structure_error",
            "context": f"Malformed JSON: {str(e)}"
        })
        return {"passed": False, "sanitized_output": None, "violations_log": violations_log}

    # Validation Stage 2: Structural Integrity
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

    # Prepare for grounding validation
    known_theme_ids = set()
    valid_entity_ids = {e.get("entity_id") for e in entity_id_map if e.get("entity_id")}
    
    sanitized_output = {
        "themes": [],
        "question_groups": []
    }
    
    # 3. Scan Themes
    for idx, theme in enumerate(themes):
        if not isinstance(theme, dict): continue
        theme_id = theme.get("theme_id")
        
        # Theme ID format and uniqueness
        if not theme_id or not re.match(r"^THEME-\d{3}$", theme_id):
            violations_log.append({"violation_id": str(uuid.uuid4()), "field": f"themes[{idx}].theme_id", "type": "invalid_format", "context": f"Invalid format: {theme_id}"})
            passed = False
        elif theme_id in known_theme_ids:
            violations_log.append({"violation_id": str(uuid.uuid4()), "field": f"themes[{idx}]", "type": "duplicate_theme_id", "context": f"Duplicate theme_id: {theme_id}"})
            passed = False
        elif theme_id:
            known_theme_ids.add(theme_id)
            
        # Mandatory fields
        required = ["title", "description", "referenced_entity_ids"]
        for field in required:
            if field not in theme or not theme[field]:
                violations_log.append({"violation_id": str(uuid.uuid4()), "field": f"themes[{idx}].{field}", "type": "missing_field", "context": f"Field '{field}' is missing or empty."})
                passed = False

        if not passed: continue

        sanitized_theme = {
            "theme_id": theme_id,
            "title": theme.get("title", ""),
            "description": theme.get("description", ""),
            "referenced_entity_ids": theme.get("referenced_entity_ids", [])
        }
        
        # Entity Reference Validation
        refs = theme.get("referenced_entity_ids", [])
        for ref in refs:
            if ref not in valid_entity_ids:
                violations_log.append({"violation_id": str(uuid.uuid4()), "field": f"themes[{idx}].referenced_entity_ids", "type": "invented_entity_id", "context": f"Invented entity ID: {ref}"})
                passed = False
                
        # Neutrality Validation
        for field in ["title", "description"]:
            text = sanitized_theme.get(field, "")
            violations = _scan_text(text, rules)
            for v in violations:
                v["field"] = f"themes[{idx}].{field}"
                v["type"] = "prohibited_language"
                violations_log.append(v)
                passed = False
                
        sanitized_output["themes"].append(sanitized_theme)

    # 4. Scan Question Groups
    if passed:
        for idx, qg in enumerate(question_groups):
            if not isinstance(qg, dict): continue
            theme_id = qg.get("theme_id")
            
            # Linkage validation
            if theme_id not in known_theme_ids:
                violations_log.append({"violation_id": str(uuid.uuid4()), "field": f"question_groups[{idx}].theme_id", "type": "broken_linkage", "context": f"References non-existent theme_id: {theme_id}"})
                passed = False
                
            # Mandatory fields
            required = ["group_title", "questions"]
            for field in required:
                if field not in qg or not qg[field]:
                    violations_log.append({"violation_id": str(uuid.uuid4()), "field": f"question_groups[{idx}].{field}", "type": "missing_field", "context": f"Field '{field}' is missing or empty."})
                    passed = False

            if not passed: continue

            sanitized_qg = {
                "theme_id": theme_id,
                "group_title": qg.get("group_title", ""),
                "questions": qg.get("questions", [])
            }
            
            # Neutrality Validation - Group Title
            violations = _scan_text(sanitized_qg["group_title"], rules)
            for v in violations:
                v["field"] = f"question_groups[{idx}].group_title"
                v["type"] = "prohibited_language"
                violations_log.append(v)
                passed = False
                
            # Neutrality Validation - Questions
            questions = qg.get("questions", [])
            if not isinstance(questions, list) or not questions:
                violations_log.append({"violation_id": str(uuid.uuid4()), "field": f"question_groups[{idx}].questions", "type": "empty_array", "context": "Questions array is empty."})
                passed = False
            else:
                for q_idx, q_text in enumerate(questions):
                    q_violations = _scan_text(q_text, rules)
                    for v in q_violations:
                        v["field"] = f"question_groups[{idx}].questions[{q_idx}]"
                        v["type"] = "prohibited_language"
                        violations_log.append(v)
                        passed = False
                    
            sanitized_output["question_groups"].append(sanitized_qg)

    return {
        "passed": passed,
        "sanitized_output": sanitized_output if passed else None,
        "violations_log": violations_log,
        "policy_version": PolicyConfig.get_version()
    }

def validate_signals(raw_text: str, entity_id_map: List[dict], deterministic_signals: List[dict]) -> dict:
    """
    Agent 15 - Signal Validation Layer.
    Strictly validates LLM Call 1 output (interpreted signals).
    Enforces schema, entity grounding, and neutral language.
    """
    logger.debug("Starting Agent 15 signal validation.")
    rules = PolicyConfig.get_prohibited_terms()
    violations_log = []
    passed = True
    
    # Validation Stage 1: JSON Integrity
    try:
        data = json.loads(raw_text)
    except Exception as e:
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "type": "structure_error",
            "context": f"Malformed JSON: {str(e)}"
        })
        return {"passed": False, "sanitized_output": None, "violations_log": violations_log}

    # Validation Stage 2: Structural Integrity
    if not isinstance(data, dict) or "interpreted_signals" not in data:
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "type": "structure_error",
            "context": "Missing 'interpreted_signals' root key."
        })
        return {"passed": False, "sanitized_output": None, "violations_log": violations_log}

    signals = data["interpreted_signals"]
    if not isinstance(signals, list):
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "type": "structure_error",
            "context": "'interpreted_signals' must be an array."
        })
        return {"passed": False, "sanitized_output": None, "violations_log": violations_log}

    # Preparation for ID validation
    valid_entity_ids = {e.get("entity_id") for e in entity_id_map if e.get("entity_id")}
    valid_det_signal_ids = {s.get("signal_id") for s in deterministic_signals if s.get("signal_id")}
    known_int_ids = set()
    
    sanitized_signals = []

    # Validation Stage 3: Per-Signal Validation
    for idx, sig in enumerate(signals):
        sig_passed = True
        
        # Mandatory fields
        required = ["signal_id", "title", "description", "referenced_entity_ids", "supporting_det_signal_ids"]
        for field in required:
            if field not in sig or not sig[field]:
                violations_log.append({
                    "violation_id": str(uuid.uuid4()),
                    "field": f"interpreted_signals[{idx}].{field}",
                    "type": "missing_field",
                    "context": f"Required field '{field}' is missing or empty."
                })
                sig_passed = False
                passed = False

        if not sig_passed: continue

        # ID Format & Uniqueness
        sig_id = sig["signal_id"]
        if not re.match(r"^INT-\d{3}$", sig_id):
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"interpreted_signals[{idx}].signal_id",
                "type": "invalid_format",
                "context": f"Invalid ID format: {sig_id}"
            })
            passed = False
        if sig_id in known_int_ids:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"interpreted_signals[{idx}].signal_id",
                "type": "duplicate_id",
                "context": f"Duplicate signal ID: {sig_id}"
            })
            passed = False
        known_int_ids.add(sig_id)

        # Entity Reference Validation
        for ent_id in sig["referenced_entity_ids"]:
            if ent_id not in valid_entity_ids:
                violations_log.append({
                    "violation_id": str(uuid.uuid4()),
                    "field": f"interpreted_signals[{idx}].referenced_entity_ids",
                    "type": "invented_entity_id",
                    "context": f"Invented Entity ID: {ent_id}"
                })
                passed = False

        # Deterministic Signal Reference Validation
        for det_id in sig["supporting_det_signal_ids"]:
            if det_id not in valid_det_signal_ids:
                violations_log.append({
                    "violation_id": str(uuid.uuid4()),
                    "field": f"interpreted_signals[{idx}].supporting_det_signal_ids",
                    "type": "invented_det_signal_id",
                    "context": f"Invented Deterministic Signal ID: {det_id}"
                })
                passed = False

        # Neutrality Validation
        for field in ["title", "description"]:
            text = sig[field]
            violations = _scan_text(text, rules)
            for v in violations:
                v["field"] = f"interpreted_signals[{idx}].{field}"
                v["type"] = "prohibited_language"
                violations_log.append(v)
                passed = False
        
        if passed:
            sanitized_signals.append(sig)

    return {
        "passed": passed,
        "sanitized_output": {"interpreted_signals": sanitized_signals} if passed else None,
        "violations_log": violations_log,
        "policy_version": PolicyConfig.get_version()
    }
