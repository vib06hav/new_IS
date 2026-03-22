import json
import re
import uuid
from typing import Dict, Any, List, Tuple
from app.policy.config import PolicyConfig

PROHIBITED_TERM_REWRITES = {
    "strong performance": "recorded results",
    "high performance": "recorded results",
    "excellent performance": "recorded results",
    "impressive commitment": "documented engagement",
    "showing aptitude": "",
    "indicating aptitude": "",
    "showing strong performance": "",
    "indicating strong performance": "",
}


def _scan_text(text: str, rules: List[str]) -> List[Dict[str, Any]]:
    """
    Scans a block of text against a list of prohibited phrases.
    Uses basic substring matching and word boundary regex for robustness.
    """
    violations = []
    if not text:
        return violations
    if not isinstance(text, str):
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


def _normalize_whitespace(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    return text


def _rewrite_prohibited_phrasing(text: Any, rules: List[str]) -> Any:
    if not isinstance(text, str):
        return text

    rewritten = text
    for phrase, replacement in PROHIBITED_TERM_REWRITES.items():
        rewritten = re.sub(re.escape(phrase), replacement, rewritten, flags=re.IGNORECASE)

    for rule in rules:
        rewritten = re.sub(re.escape(rule), "", rewritten, flags=re.IGNORECASE)

    rewritten = re.sub(r"\b(indicating|suggesting|showing|reflecting)\b\s*(,)?", "", rewritten, flags=re.IGNORECASE)
    rewritten = _normalize_whitespace(rewritten)
    rewritten = rewritten.strip(" -,:;")
    return rewritten


def _first_present(source: dict, keys: List[str], default=None):
    for key in keys:
        value = source.get(key)
        if value is not None:
            return value
    return default


def _normalize_signal_output(data: Any, rules: List[str]) -> Any:
    if not isinstance(data, dict):
        return data

    raw_signals = data.get("interpreted_signals", [])
    normalized_signals = []
    if isinstance(raw_signals, list):
        for sig in raw_signals:
            if not isinstance(sig, dict):
                continue
            normalized_signals.append({
                "signal_id": _first_present(sig, ["signal_id", "id"]),
                "title": _rewrite_prohibited_phrasing(_first_present(sig, ["title", "name", "label"], ""), rules),
                "description": _rewrite_prohibited_phrasing(_first_present(sig, ["description", "summary", "details"], ""), rules),
                "referenced_entity_ids": _first_present(sig, ["referenced_entity_ids", "entity_ids", "references"], []),
                "supporting_det_signal_ids": _first_present(sig, ["supporting_det_signal_ids", "det_signal_ids", "deterministic_signal_ids"], []),
            })
    return {"interpreted_signals": normalized_signals}


def _backfill_signal_references(normalized_output: Any, deterministic_signals: List[dict]) -> Any:
    if not isinstance(normalized_output, dict):
        return normalized_output

    signals = normalized_output.get("interpreted_signals")
    if not isinstance(signals, list):
        return normalized_output

    det_lookup = {}
    for det_signal in deterministic_signals:
        if not isinstance(det_signal, dict):
            continue
        det_id = det_signal.get("signal_id")
        refs = det_signal.get("referenced_entity_ids", [])
        if det_id:
            det_lookup[det_id] = [ref for ref in refs if ref]

    for signal in signals:
        if not isinstance(signal, dict):
            continue
        referenced_ids = signal.get("referenced_entity_ids")
        if referenced_ids:
            continue
        recovered_refs = []
        for det_id in signal.get("supporting_det_signal_ids", []) or []:
            for ref in det_lookup.get(det_id, []):
                if ref not in recovered_refs:
                    recovered_refs.append(ref)
        if recovered_refs:
            signal["referenced_entity_ids"] = recovered_refs

    return normalized_output


def _normalize_question_item(item: Any) -> Any:
    if isinstance(item, str):
        return _normalize_whitespace(item)
    if isinstance(item, dict):
        candidate = _first_present(item, ["question", "text", "prompt", "content"])
        if isinstance(candidate, str):
            return _normalize_whitespace(candidate)
    return item


def _normalize_theme_output(data: Any, rules: List[str], bundle: dict | None = None) -> Any:
    if not isinstance(data, dict):
        return data

    raw_themes = data.get("themes", [])
    raw_question_groups = data.get("question_groups", [])
    signal_pairs = []
    if isinstance(bundle, dict):
        raw_pairs = bundle.get("signal_evidence_pairs", [])
        if isinstance(raw_pairs, list):
            signal_pairs = raw_pairs

    normalized_themes = []
    if isinstance(raw_themes, list):
        for idx, theme in enumerate(raw_themes):
            if not isinstance(theme, dict):
                continue
            signal = {}
            if idx < len(signal_pairs) and isinstance(signal_pairs[idx], dict):
                signal = signal_pairs[idx].get("signal", {}) or {}
            title = _rewrite_prohibited_phrasing(
                _first_present(
                    theme,
                    ["title", "theme_name", "name", "heading", "theme_title"],
                    ""
                ),
                rules
            )
            if not title:
                title = _rewrite_prohibited_phrasing(_first_present(signal, ["title"], ""), rules)
            description = _rewrite_prohibited_phrasing(
                _first_present(theme, ["description", "summary", "details", "theme_description"], ""),
                rules
            )
            if not description:
                description = _rewrite_prohibited_phrasing(_first_present(signal, ["description"], ""), rules)
            referenced_entity_ids = _first_present(
                theme,
                ["referenced_entity_ids", "entity_ids", "references", "entities"],
                []
            )
            if not referenced_entity_ids:
                referenced_entity_ids = _first_present(signal, ["referenced_entity_ids"], [])
            normalized_themes.append({
                "theme_id": _first_present(theme, ["theme_id", "id"]),
                "title": title,
                "description": description,
                "referenced_entity_ids": referenced_entity_ids,
            })

    normalized_question_groups = []
    if isinstance(raw_question_groups, list):
        for qg in raw_question_groups:
            if not isinstance(qg, dict):
                continue
            raw_questions = _first_present(qg, ["questions", "items", "question_list"], [])
            questions = []
            if isinstance(raw_questions, list):
                for item in raw_questions:
                    questions.append(_normalize_question_item(item))
            normalized_question_groups.append({
                "theme_id": _first_present(qg, ["theme_id", "theme", "theme_ref"]),
                "group_title": _rewrite_prohibited_phrasing(_first_present(qg, ["group_title", "title", "heading", "name"], ""), rules),
                "questions": questions,
            })

    return {
        "themes": normalized_themes,
        "question_groups": normalized_question_groups,
    }

import logging

logger = logging.getLogger(__name__)

def validate_themes(raw_text: str, entity_id_map: List[dict], bundle: dict | None = None) -> Dict[str, Any]:
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

    normalized_output = _normalize_theme_output(synthesis_output, rules, bundle)

    # Validation Stage 2: Structural Integrity
    if not isinstance(normalized_output, dict):
        violations_log.append({"violation_id": str(uuid.uuid4()), "field": "root", "type": "structure_error", "context": "Root is not a JSON object."})
        return {"passed": False, "sanitized_output": None, "normalized_output": normalized_output, "violations_log": violations_log}
        
    themes = normalized_output.get("themes")
    question_groups = normalized_output.get("question_groups")
    
    if themes is None or not isinstance(themes, list):
        violations_log.append({"violation_id": str(uuid.uuid4()), "field": "themes", "type": "structure_error", "context": "Missing or invalid 'themes' array."})
        passed = False
        
    if question_groups is None or not isinstance(question_groups, list):
        violations_log.append({"violation_id": str(uuid.uuid4()), "field": "question_groups", "type": "structure_error", "context": "Missing or invalid 'question_groups' array."})
        passed = False
        
    if not passed:
        return {"passed": False, "sanitized_output": None, "normalized_output": normalized_output, "violations_log": violations_log}

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
                    if not isinstance(q_text, str) or not q_text.strip():
                        violations_log.append({
                            "violation_id": str(uuid.uuid4()),
                            "field": f"question_groups[{idx}].questions[{q_idx}]",
                            "type": "invalid_question_item",
                            "context": "Each question must be a non-empty string."
                        })
                        passed = False
                        continue
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
        "normalized_output": normalized_output,
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
        return {"passed": False, "sanitized_output": None, "normalized_output": None, "violations_log": violations_log}

    normalized_output = _normalize_signal_output(data, rules)
    normalized_output = _backfill_signal_references(normalized_output, deterministic_signals)

    # Validation Stage 2: Structural Integrity
    if not isinstance(normalized_output, dict) or "interpreted_signals" not in normalized_output:
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "type": "structure_error",
            "context": "Missing 'interpreted_signals' root key."
        })
        return {"passed": False, "sanitized_output": None, "normalized_output": normalized_output, "violations_log": violations_log}

    signals = normalized_output["interpreted_signals"]
    if not isinstance(signals, list):
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "type": "structure_error",
            "context": "'interpreted_signals' must be an array."
        })
        return {"passed": False, "sanitized_output": None, "normalized_output": normalized_output, "violations_log": violations_log}

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
        "normalized_output": normalized_output,
        "violations_log": violations_log,
        "policy_version": PolicyConfig.get_version()
    }
