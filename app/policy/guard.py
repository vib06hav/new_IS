import json
import logging
import re
import uuid
from typing import Any, Dict, List

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

logger = logging.getLogger(__name__)


def _scan_text(text: str, rules: List[str]) -> List[Dict[str, Any]]:
    """
    Scans a block of text against a list of prohibited phrases.
    Uses basic substring matching and word boundary regex for robustness.
    """
    violations = []
    if not text or not isinstance(text, str):
        return violations

    lower_text = text.lower()
    for phrase in rules:
        lower_phrase = phrase.lower()
        if lower_phrase in lower_text:
            violations.append({
                "violation_id": str(uuid.uuid4()),
                "phrase_matched": phrase,
                "context": text[:100] + "..." if len(text) > 100 else text,
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


def _normalize_question_item(item: Any) -> Any:
    if isinstance(item, str):
        return _normalize_whitespace(item)
    if isinstance(item, dict):
        candidate = _first_present(item, ["question", "text", "prompt", "content"])
        if isinstance(candidate, str):
            return _normalize_whitespace(candidate)
    return item


def _normalize_theme_entries(raw_themes: Any, rules: List[str]) -> List[Dict[str, Any]]:
    normalized_themes = []
    if not isinstance(raw_themes, list):
        return normalized_themes

    for theme in raw_themes:
        if not isinstance(theme, dict):
            continue
        normalized_themes.append({
            "theme_id": _first_present(theme, ["theme_id", "id"]),
            "title": _rewrite_prohibited_phrasing(
                _first_present(theme, ["title", "theme_name", "name", "heading", "theme_title"], ""),
                rules,
            ),
            "description": _rewrite_prohibited_phrasing(
                _first_present(theme, ["description", "summary", "details", "theme_description"], ""),
                rules,
            ),
            "referenced_entity_ids": _first_present(
                theme,
                ["referenced_entity_ids", "entity_ids", "references", "entities"],
                [],
            ),
        })
    return normalized_themes


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
                "theme_id": _first_present(sig, ["theme_id", "theme", "theme_ref"]),
                "title": _rewrite_prohibited_phrasing(_first_present(sig, ["title", "name", "label"], ""), rules),
                "essay_claim": _first_present(sig, ["essay_claim"], ""),
                "evidence_observation": _first_present(sig, ["evidence_observation"], ""),
                "tension_or_coherence": _first_present(sig, ["tension_or_coherence"], ""),
                "interview_hook": _first_present(sig, ["interview_hook"], ""),
                "referenced_entity_ids": _first_present(sig, ["referenced_entity_ids", "entity_ids", "references"], []),
                "supporting_det_signal_ids": _first_present(
                    sig,
                    ["supporting_det_signal_ids", "det_signal_ids", "deterministic_signal_ids"],
                    [],
                ),
            })
    return {
        "interpreted_signals": normalized_signals,
        "themes": _normalize_theme_entries(data.get("themes", []), rules),
    }


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


def _normalize_question_group_output(data: Any, rules: List[str]) -> Any:
    if not isinstance(data, dict):
        return data

    raw_question_groups = data.get("question_groups", [])
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
                "group_title": _rewrite_prohibited_phrasing(
                    _first_present(qg, ["group_title", "title", "heading", "name"], ""),
                    rules,
                ),
                "questions": questions,
            })

    return {"question_groups": normalized_question_groups}


def _append_text_violations(
    violations_log: List[Dict[str, Any]],
    field_name: str,
    text: str,
    rules: List[str],
) -> bool:
    found_violation = False
    for violation in _scan_text(text, rules):
        violation["field"] = field_name
        violation["type"] = "prohibited_language"
        violations_log.append(violation)
        found_violation = True
    return found_violation


def validate_signals(raw_text: str, entity_id_map: List[dict], deterministic_signals: List[dict]) -> dict:
    """
    Agent 15 - Signal Validation Layer.
    Strictly validates LLM Call 1 output (interpreted signals + themes).
    Enforces schema, entity grounding, theme linkage, and neutral language.
    """
    logger.debug("Starting Call 1 signal/theme validation.")
    rules = PolicyConfig.get_prohibited_terms()
    violations_log = []

    try:
        data = json.loads(raw_text)
    except Exception as exc:
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "type": "structure_error",
            "context": f"Malformed JSON: {str(exc)}",
        })
        return {"passed": False, "sanitized_output": None, "normalized_output": None, "violations_log": violations_log}

    normalized_output = _normalize_signal_output(data, rules)
    normalized_output = _backfill_signal_references(normalized_output, deterministic_signals)

    if not isinstance(normalized_output, dict):
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "field": "root",
            "type": "structure_error",
            "context": "Root is not a JSON object.",
        })
        return {"passed": False, "sanitized_output": None, "normalized_output": normalized_output, "violations_log": violations_log}

    signals = normalized_output.get("interpreted_signals")
    themes = normalized_output.get("themes")
    if not isinstance(signals, list):
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "field": "interpreted_signals",
            "type": "structure_error",
            "context": "'interpreted_signals' must be an array.",
        })
    if not isinstance(themes, list):
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "field": "themes",
            "type": "structure_error",
            "context": "'themes' must be an array.",
        })
    if violations_log:
        return {"passed": False, "sanitized_output": None, "normalized_output": normalized_output, "violations_log": violations_log}

    valid_entity_ids = {e.get("entity_id") for e in entity_id_map if e.get("entity_id")}
    valid_det_signal_ids = {s.get("signal_id") for s in deterministic_signals if s.get("signal_id")}

    passed = True
    known_int_ids = set()
    known_theme_ids = set()
    sanitized_signals = []
    sanitized_themes = []
    theme_signal_counts: Dict[str, int] = {}
    theme_signal_refs: Dict[str, set[str]] = {}

    for idx, sig in enumerate(signals):
        if not isinstance(sig, dict):
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"interpreted_signals[{idx}]",
                "type": "structure_error",
                "context": "Each interpreted signal must be an object.",
            })
            passed = False
            continue

        sig_passed = True
        required = [
            "signal_id",
            "theme_id",
            "title",
            "essay_claim",
            "evidence_observation",
            "tension_or_coherence",
            "interview_hook",
            "referenced_entity_ids",
            "supporting_det_signal_ids",
        ]
        for field in required:
            value = sig.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                violations_log.append({
                    "violation_id": str(uuid.uuid4()),
                    "field": f"interpreted_signals[{idx}].{field}",
                    "type": "missing_field",
                    "context": f"Required field '{field}' is missing or empty.",
                })
                sig_passed = False
                passed = False

        signal_id = sig.get("signal_id")
        if not signal_id or not re.match(r"^INT-\d{3}$", str(signal_id)):
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"interpreted_signals[{idx}].signal_id",
                "type": "invalid_format",
                "context": f"Invalid ID format: {signal_id}",
            })
            sig_passed = False
            passed = False
        elif signal_id in known_int_ids:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"interpreted_signals[{idx}].signal_id",
                "type": "duplicate_id",
                "context": f"Duplicate signal ID: {signal_id}",
            })
            sig_passed = False
            passed = False
        else:
            known_int_ids.add(signal_id)

        theme_id = sig.get("theme_id")
        if not theme_id or not re.match(r"^THEME-\d{3}$", str(theme_id)):
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"interpreted_signals[{idx}].theme_id",
                "type": "invalid_format",
                "context": f"Invalid theme_id format: {theme_id}",
            })
            sig_passed = False
            passed = False

        referenced_entity_ids = sig.get("referenced_entity_ids", [])
        if not isinstance(referenced_entity_ids, list) or not referenced_entity_ids:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"interpreted_signals[{idx}].referenced_entity_ids",
                "type": "empty_array",
                "context": "Signal must reference at least one entity ID.",
            })
            sig_passed = False
            passed = False
        else:
            for ent_id in referenced_entity_ids:
                if ent_id not in valid_entity_ids:
                    violations_log.append({
                        "violation_id": str(uuid.uuid4()),
                        "field": f"interpreted_signals[{idx}].referenced_entity_ids",
                        "type": "invented_entity_id",
                        "context": f"Invented Entity ID: {ent_id}",
                    })
                    sig_passed = False
                    passed = False

        supporting_det_signal_ids = sig.get("supporting_det_signal_ids", [])
        if not isinstance(supporting_det_signal_ids, list):
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"interpreted_signals[{idx}].supporting_det_signal_ids",
                "type": "invalid_type",
                "context": "supporting_det_signal_ids must be an array.",
            })
            sig_passed = False
            passed = False
        else:
            for det_id in supporting_det_signal_ids:
                if det_id not in valid_det_signal_ids:
                    violations_log.append({
                        "violation_id": str(uuid.uuid4()),
                        "field": f"interpreted_signals[{idx}].supporting_det_signal_ids",
                        "type": "invented_det_signal_id",
                        "context": f"Invented Deterministic Signal ID: {det_id}",
                    })
                    sig_passed = False
                    passed = False

        for field in ["title", "essay_claim", "evidence_observation", "tension_or_coherence", "interview_hook"]:
            if _append_text_violations(violations_log, f"interpreted_signals[{idx}].{field}", sig.get(field, ""), rules):
                sig_passed = False
                passed = False

        if not sig_passed:
            continue

        sanitized_signal = {
            "signal_id": signal_id,
            "theme_id": theme_id,
            "title": sig.get("title"),
            "essay_claim": sig.get("essay_claim"),
            "evidence_observation": sig.get("evidence_observation"),
            "tension_or_coherence": sig.get("tension_or_coherence"),
            "interview_hook": sig.get("interview_hook"),
            "referenced_entity_ids": referenced_entity_ids,
            "supporting_det_signal_ids": supporting_det_signal_ids,
        }
        sanitized_signals.append(sanitized_signal)
        theme_signal_counts[theme_id] = theme_signal_counts.get(theme_id, 0) + 1
        theme_signal_refs.setdefault(theme_id, set()).update(referenced_entity_ids)

    for idx, theme in enumerate(themes):
        if not isinstance(theme, dict):
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"themes[{idx}]",
                "type": "structure_error",
                "context": "Each theme must be an object.",
            })
            passed = False
            continue

        theme_passed = True
        required = ["theme_id", "title", "description", "referenced_entity_ids"]
        for field in required:
            value = theme.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                violations_log.append({
                    "violation_id": str(uuid.uuid4()),
                    "field": f"themes[{idx}].{field}",
                    "type": "missing_field",
                    "context": f"Field '{field}' is missing or empty.",
                })
                theme_passed = False
                passed = False

        theme_id = theme.get("theme_id")
        if not theme_id or not re.match(r"^THEME-\d{3}$", str(theme_id)):
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"themes[{idx}].theme_id",
                "type": "invalid_format",
                "context": f"Invalid format: {theme_id}",
            })
            theme_passed = False
            passed = False
        elif theme_id in known_theme_ids:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"themes[{idx}].theme_id",
                "type": "duplicate_theme_id",
                "context": f"Duplicate theme_id: {theme_id}",
            })
            theme_passed = False
            passed = False
        else:
            known_theme_ids.add(theme_id)

        refs = theme.get("referenced_entity_ids", [])
        if not isinstance(refs, list) or not refs:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"themes[{idx}].referenced_entity_ids",
                "type": "empty_array",
                "context": "Theme must reference at least one entity ID.",
            })
            theme_passed = False
            passed = False
        else:
            for ref in refs:
                if ref not in valid_entity_ids:
                    violations_log.append({
                        "violation_id": str(uuid.uuid4()),
                        "field": f"themes[{idx}].referenced_entity_ids",
                        "type": "invented_entity_id",
                        "context": f"Invented entity ID: {ref}",
                    })
                    theme_passed = False
                    passed = False

        for field in ["title", "description"]:
            if _append_text_violations(violations_log, f"themes[{idx}].{field}", theme.get(field, ""), rules):
                theme_passed = False
                passed = False

        if not theme_passed:
            continue

        sanitized_themes.append({
            "theme_id": theme_id,
            "title": theme.get("title"),
            "description": theme.get("description"),
            "referenced_entity_ids": refs,
        })

    valid_theme_ids = {theme["theme_id"] for theme in sanitized_themes}

    for idx, sig in enumerate(sanitized_signals):
        theme_id = sig["theme_id"]
        if theme_id not in valid_theme_ids:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"interpreted_signals[{idx}].theme_id",
                "type": "broken_linkage",
                "context": f"References non-existent theme_id: {theme_id}",
            })
            passed = False

    for idx, theme in enumerate(sanitized_themes):
        theme_id = theme["theme_id"]
        member_count = theme_signal_counts.get(theme_id, 0)
        if member_count == 0:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"themes[{idx}].theme_id",
                "type": "orphan_theme",
                "context": f"Theme {theme_id} is not referenced by any interpreted signal.",
            })
            passed = False
            continue

        signal_refs = theme_signal_refs.get(theme_id, set())
        ungrounded_refs = [ref for ref in theme["referenced_entity_ids"] if ref not in signal_refs]
        if ungrounded_refs:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"themes[{idx}].referenced_entity_ids",
                "type": "ungrounded_theme_entity_id",
                "context": f"Theme references IDs not grounded in member signals: {ungrounded_refs}",
            })
            passed = False

    return {
        "passed": passed,
        "sanitized_output": {
            "interpreted_signals": sanitized_signals,
            "themes": sanitized_themes,
        } if passed else None,
        "normalized_output": normalized_output,
        "violations_log": violations_log,
        "policy_version": PolicyConfig.get_version(),
    }


def validate_question_groups(raw_text: str, entity_id_map: List[dict], bundle: dict | None = None) -> Dict[str, Any]:
    """
    Agent 15 - Call 2 Validation Layer.
    Strictly validates LLM Call 2 output (question groups only).
    Enforces schema, theme coverage/linkage, and neutral language.
    """
    logger.debug("Starting Call 2 question-group validation.")
    rules = PolicyConfig.get_prohibited_terms()
    violations_log = []

    try:
        synthesis_output = json.loads(raw_text)
    except Exception as exc:
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "type": "structure_error",
            "context": f"Malformed JSON: {str(exc)}",
        })
        return {"passed": False, "sanitized_output": None, "violations_log": violations_log}

    normalized_output = _normalize_question_group_output(synthesis_output, rules)
    if not isinstance(normalized_output, dict):
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "field": "root",
            "type": "structure_error",
            "context": "Root is not a JSON object.",
        })
        return {"passed": False, "sanitized_output": None, "normalized_output": normalized_output, "violations_log": violations_log}

    question_groups = normalized_output.get("question_groups")
    if not isinstance(question_groups, list):
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "field": "question_groups",
            "type": "structure_error",
            "context": "Missing or invalid 'question_groups' array.",
        })
        return {"passed": False, "sanitized_output": None, "normalized_output": normalized_output, "violations_log": violations_log}

    bundle_themes = []
    if isinstance(bundle, dict):
        raw_themes = bundle.get("themes", [])
        if isinstance(raw_themes, list):
            bundle_themes = [theme for theme in raw_themes if isinstance(theme, dict)]

    expected_theme_ids = [theme.get("theme_id") for theme in bundle_themes if theme.get("theme_id")]
    expected_theme_id_set = set(expected_theme_ids)

    passed = True
    seen_theme_ids = set()
    sanitized_question_groups = []

    for idx, qg in enumerate(question_groups):
        if not isinstance(qg, dict):
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"question_groups[{idx}]",
                "type": "structure_error",
                "context": "Each question group must be an object.",
            })
            passed = False
            continue

        qg_passed = True
        theme_id = qg.get("theme_id")
        if theme_id not in expected_theme_id_set:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"question_groups[{idx}].theme_id",
                "type": "broken_linkage",
                "context": f"References non-existent theme_id: {theme_id}",
            })
            qg_passed = False
            passed = False
        elif theme_id in seen_theme_ids:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"question_groups[{idx}].theme_id",
                "type": "duplicate_theme_group",
                "context": f"Duplicate question group for theme_id: {theme_id}",
            })
            qg_passed = False
            passed = False
        else:
            seen_theme_ids.add(theme_id)

        group_title = qg.get("group_title")
        if not isinstance(group_title, str) or not group_title.strip():
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"question_groups[{idx}].group_title",
                "type": "missing_field",
                "context": "Field 'group_title' is missing or empty.",
            })
            qg_passed = False
            passed = False
        elif _append_text_violations(violations_log, f"question_groups[{idx}].group_title", group_title, rules):
            qg_passed = False
            passed = False

        questions = qg.get("questions")
        if not isinstance(questions, list) or not questions:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"question_groups[{idx}].questions",
                "type": "empty_array",
                "context": "Questions array is empty.",
            })
            qg_passed = False
            passed = False
        else:
            for q_idx, q_text in enumerate(questions):
                if not isinstance(q_text, str) or not q_text.strip():
                    violations_log.append({
                        "violation_id": str(uuid.uuid4()),
                        "field": f"question_groups[{idx}].questions[{q_idx}]",
                        "type": "invalid_question_item",
                        "context": "Each question must be a non-empty string.",
                    })
                    qg_passed = False
                    passed = False
                    continue
                if _append_text_violations(
                    violations_log,
                    f"question_groups[{idx}].questions[{q_idx}]",
                    q_text,
                    rules,
                ):
                    qg_passed = False
                    passed = False

        if not qg_passed:
            continue

        sanitized_question_groups.append({
            "theme_id": theme_id,
            "group_title": group_title,
            "questions": questions,
        })

    missing_theme_ids = expected_theme_id_set - seen_theme_ids
    extra_theme_ids = seen_theme_ids - expected_theme_id_set
    if missing_theme_ids:
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "field": "question_groups",
            "type": "missing_theme_coverage",
            "context": f"Missing question groups for theme_ids: {sorted(missing_theme_ids)}",
        })
        passed = False
    if extra_theme_ids:
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "field": "question_groups",
            "type": "extra_theme_coverage",
            "context": f"Unexpected question groups for theme_ids: {sorted(extra_theme_ids)}",
        })
        passed = False

    return {
        "passed": passed,
        "sanitized_output": {"question_groups": sanitized_question_groups} if passed else None,
        "normalized_output": normalized_output,
        "violations_log": violations_log,
        "policy_version": PolicyConfig.get_version(),
    }


def validate_themes(raw_text: str, entity_id_map: List[dict], bundle: dict | None = None) -> Dict[str, Any]:
    """
    Backward-compatible wrapper for older callers.
    Call 2 now validates question groups only.
    """
    return validate_question_groups(raw_text, entity_id_map, bundle)
