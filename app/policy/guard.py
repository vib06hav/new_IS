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

FOCUS_AREA_BANNED_PHRASES = [
    "this area explores",
    "this covers",
    "it is important to determine",
    "it is important to",
    "it's important to",
    "this reveals whether",
    "the candidate demonstrates",
    "this signal suggests",
    "understanding this reveals",
    "ask them to",
    "have them explain",
    "get them to",
    "buzzword",
]

QUESTION_BANNED_PHRASES = []

FOCUS_AREA_PRONOUN_RE = re.compile(r"\b(he|she|his|her)\b", flags=re.IGNORECASE)
FIRST_QUESTION_CONTENTION_RE = re.compile(r"\b(yet|despite|while)\b", flags=re.IGNORECASE)

logger = logging.getLogger(__name__)
MAX_FRAGMENT_IDS_PER_SIGNAL = 3


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
            "supporting_signal_ids": _first_present(
                theme,
                ["supporting_signal_ids", "signal_ids", "member_signal_ids"],
                [],
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

    raw_signals = data.get("signals", [])
    normalized_signals = []
    if isinstance(raw_signals, list):
        for sig in raw_signals:
            if not isinstance(sig, dict):
                continue
            normalized_signals.append({
                "signal_id": _first_present(sig, ["signal_id", "id"]),
                "title": _rewrite_prohibited_phrasing(_first_present(sig, ["title", "name", "label"], ""), rules),
                "theme_id": _first_present(sig, ["theme_id", "theme", "theme_ref"]),
                "core_observation": _first_present(sig, ["core_observation", "direct_read", "evidence_anchor"], ""),
                "interview_opening": _first_present(sig, ["interview_opening", "depth_opening", "what_remains_open"], ""),
                "referenced_entity_ids": _first_present(sig, ["referenced_entity_ids", "entity_ids", "references"], []),
                "supporting_det_signal_ids": _first_present(
                    sig,
                    ["supporting_det_signal_ids", "det_signal_ids", "deterministic_signal_ids"],
                    [],
                ),
                "supporting_fragment_ids": _first_present(
                    sig,
                    ["supporting_fragment_ids", "fragment_ids", "essay_fragment_ids"],
                    [],
                ),
            })
    return {
        "signals": normalized_signals,
        "themes": _normalize_theme_entries(data.get("themes", []), rules),
    }


def _backfill_signal_references(normalized_output: Any, deterministic_signals: List[dict]) -> Any:
    if not isinstance(normalized_output, dict):
        return normalized_output

    signals = normalized_output.get("signals")
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


def _normalize_opening_group_output(data: Any, rules: List[str]) -> Any:
    if not isinstance(data, dict):
        return data

    raw_question_groups = data.get("question_groups", data.get("opening_groups", []))
    normalized_question_groups = []
    if isinstance(raw_question_groups, list):
        for qg in raw_question_groups:
            if not isinstance(qg, dict):
                continue
            raw_questions = _first_present(qg, ["questions", "openings", "items", "question_list"], [])
            questions = []
            if isinstance(raw_questions, list):
                for item_index, item in enumerate(raw_questions):
                    if isinstance(item, str):
                        questions.append({
                            "question_id": f"Q-{item_index + 1:03d}",
                            "question": _normalize_whitespace(item),
                        })
                    elif isinstance(item, dict):
                        questions.append({
                            "question_id": _first_present(item, ["question_id", "opening_id", "id"], ""),
                            "question": _normalize_question_item(
                                _first_present(item, ["question", "text", "sample_question"], "")
                            ),
                        })
            normalized_question_groups.append({
                "focus_area_id": _first_present(qg, ["focus_area_id", "focus_area", "focus_area_ref", "theme_id", "theme", "theme_ref"]),
                "group_label": _rewrite_prohibited_phrasing(
                    _first_present(qg, ["group_label", "title", "heading", "name"], ""),
                    rules,
                ),
                "line_of_inquiry": _rewrite_prohibited_phrasing(
                    _first_present(qg, ["line_of_inquiry", "inquiry"], ""),
                    rules,
                ),
                "questions": questions,
                "source_theme_ids": _first_present(qg, ["source_theme_ids", "theme_ids"], []),
                "source_signal_ids": _first_present(qg, ["source_signal_ids", "signal_ids"], []),
            })

    return {"question_groups": normalized_question_groups}


def _normalize_focus_area_output(data: Any, rules: List[str]) -> Any:
    if not isinstance(data, dict):
        return data

    raw_focus_areas = data.get("focus_areas", [])
    normalized_focus_areas = []
    if isinstance(raw_focus_areas, list):
        for item in raw_focus_areas:
            if not isinstance(item, dict):
                continue
            normalized_focus_areas.append({
                "focus_area_id": _first_present(item, ["focus_area_id", "id"]),
                "title": _rewrite_prohibited_phrasing(
                    _first_present(item, ["title", "name", "heading"], ""),
                    rules,
                ),
                "territory": _rewrite_prohibited_phrasing(
                    _first_present(item, ["territory", "summary", "description"], ""),
                    rules,
                ),
                "what_makes_it_worth_time": _rewrite_prohibited_phrasing(
                    _first_present(item, ["what_makes_it_worth_time", "why_it_matters_here", "why_this_is_worth_time"], ""),
                    rules,
                ),
                "source_theme_ids": _first_present(item, ["source_theme_ids", "theme_ids"], []),
                "source_signal_ids": _first_present(item, ["source_signal_ids", "signal_ids"], []),
            })

    return {"focus_areas": normalized_focus_areas}


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


def _append_phrase_violations(
    violations_log: List[Dict[str, Any]],
    field_name: str,
    text: str,
    phrases: List[str],
    violation_type: str,
) -> bool:
    found_violation = False
    for violation in _scan_text(text, phrases):
        violation["field"] = field_name
        violation["type"] = violation_type
        violations_log.append(violation)
        found_violation = True
    return found_violation


def sanitise_llm_output(
    raw_output: dict,
    valid_fragment_ids: set,
    valid_entity_ids: set,
    fragment_entity_lookup: dict[str, str] | None = None,
) -> dict:
    """
    Pre-validation auto-repair layer.
    Silently fixes all recoverable LLM output violations before the strict
    guard runs. Repairs are logged at INFO level.

    Handles:
    - HC-1 / too_many_fragment_ids   → truncates supporting_fragment_ids to MAX
    - HC-2 / invented_fragment_id    → strips unknown fragment IDs
    - HC-3 / invented_entity_id      → strips unknown entity IDs
    - HC-4 / unknown_supporting_signal_id → strips ghost SIG-IDs from themes
    - HC-5 / missing_signal_coverage → assigns orphaned signals to smallest theme
    """
    repairs = []

    signals = raw_output.get("signals", [])
    themes = raw_output.get("themes", [])

    # Build the set of SIG-IDs actually emitted in this response
    emitted_signal_ids = {s.get("signal_id") for s in signals if isinstance(s, dict) and s.get("signal_id")}

    # --- Repair signals ---
    for idx, sig in enumerate(signals):
        if not isinstance(sig, dict):
            continue

        field_prefix = f"signals[{idx}]"

        # HC-3: Strip invented entity IDs
        raw_entity_ids = sig.get("referenced_entity_ids", [])
        if isinstance(raw_entity_ids, list):
            clean_entity_ids = [eid for eid in raw_entity_ids if eid in valid_entity_ids]
            removed = set(raw_entity_ids) - set(clean_entity_ids)
            if removed:
                logger.info(f"[SANITISER] {field_prefix}.referenced_entity_ids: stripped invented entity IDs {removed}")
                repairs.append({"field": f"{field_prefix}.referenced_entity_ids", "action": "strip_invented_entity_ids", "removed": list(removed)})
                sig["referenced_entity_ids"] = clean_entity_ids

        # HC-2: Strip invented fragment IDs
        raw_fragment_ids = sig.get("supporting_fragment_ids", [])
        if isinstance(raw_fragment_ids, list) and valid_fragment_ids:
            clean_fragment_ids = [fid for fid in raw_fragment_ids if fid in valid_fragment_ids]
            removed = set(raw_fragment_ids) - set(clean_fragment_ids)
            if removed:
                logger.info(f"[SANITISER] {field_prefix}.supporting_fragment_ids: stripped invented fragment IDs {removed}")
                repairs.append({"field": f"{field_prefix}.supporting_fragment_ids", "action": "strip_invented_fragment_ids", "removed": list(removed)})
                raw_fragment_ids = clean_fragment_ids
                sig["supporting_fragment_ids"] = raw_fragment_ids

            if isinstance(sig.get("referenced_entity_ids", []), list) and fragment_entity_lookup:
                clean_fragment_ids = [
                    fid
                    for fid in raw_fragment_ids
                    if fragment_entity_lookup.get(fid) in sig.get("referenced_entity_ids", [])
                ]
                removed = [fid for fid in raw_fragment_ids if fid not in clean_fragment_ids]
                if removed:
                    logger.info(
                        f"[SANITISER] {field_prefix}.supporting_fragment_ids: stripped fragment/entity mismatches {removed}"
                    )
                    repairs.append(
                        {
                            "field": f"{field_prefix}.supporting_fragment_ids",
                            "action": "strip_fragment_entity_mismatches",
                            "removed": removed,
                        }
                    )
                    raw_fragment_ids = clean_fragment_ids
                    sig["supporting_fragment_ids"] = raw_fragment_ids

            # HC-1: Truncate fragment overflow after stripping
            if len(raw_fragment_ids) > MAX_FRAGMENT_IDS_PER_SIGNAL:
                truncated = raw_fragment_ids[MAX_FRAGMENT_IDS_PER_SIGNAL:]
                sig["supporting_fragment_ids"] = raw_fragment_ids[:MAX_FRAGMENT_IDS_PER_SIGNAL]
                logger.info(f"[SANITISER] {field_prefix}.supporting_fragment_ids: truncated {truncated} (limit={MAX_FRAGMENT_IDS_PER_SIGNAL})")
                repairs.append({"field": f"{field_prefix}.supporting_fragment_ids", "action": "truncate_fragment_overflow", "removed": truncated})

    # --- Repair themes: HC-4 strip ghost signal IDs ---
    for idx, theme in enumerate(themes):
        if not isinstance(theme, dict):
            continue
        raw_sig_ids = theme.get("supporting_signal_ids", [])
        if isinstance(raw_sig_ids, list):
            clean_sig_ids = [sid for sid in raw_sig_ids if sid in emitted_signal_ids]
            removed = set(raw_sig_ids) - set(clean_sig_ids)
            if removed:
                logger.info(f"[SANITISER] themes[{idx}].supporting_signal_ids: stripped ghost signal IDs {removed}")
                repairs.append({"field": f"themes[{idx}].supporting_signal_ids", "action": "strip_ghost_signal_ids", "removed": list(removed)})
                theme["supporting_signal_ids"] = clean_sig_ids

    # --- Repair orphaned signals: HC-5 assign to smallest theme ---
    all_theme_signal_ids = set()
    for theme in themes:
        if isinstance(theme, dict):
            for sid in theme.get("supporting_signal_ids", []):
                all_theme_signal_ids.add(sid)

    orphaned_sigs = [s["signal_id"] for s in signals if isinstance(s, dict) and s.get("signal_id") and s["signal_id"] not in all_theme_signal_ids]
    if orphaned_sigs and themes:
        for orphan_id in orphaned_sigs:
            # Pick the theme with the fewest signals currently
            valid_themes = [t for t in themes if isinstance(t, dict) and isinstance(t.get("supporting_signal_ids"), list)]
            if not valid_themes:
                break
            target_theme = min(valid_themes, key=lambda t: len(t.get("supporting_signal_ids", [])))
            target_theme["supporting_signal_ids"].append(orphan_id)
            logger.info(f"[SANITISER] Assigned orphaned signal {orphan_id} to theme {target_theme.get('theme_id')}")
            repairs.append({"field": "themes.supporting_signal_ids", "action": "assign_orphaned_signal", "signal_id": orphan_id, "assigned_to": target_theme.get("theme_id")})

    if repairs:
        logger.info(f"[SANITISER] Auto-repair complete. {len(repairs)} repair(s) applied.")
    else:
        logger.info("[SANITISER] No repairs needed.")

    return raw_output


def validate_signals(
    raw_text: str,
    entity_id_map: List[dict],
    deterministic_signals: List[dict],
    essay_fragments: List[dict] | None = None,
) -> dict:
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

    signals = normalized_output.get("signals")
    themes = normalized_output.get("themes")
    signals_missing = not isinstance(signals, list) or len(signals) == 0
    themes_missing = not isinstance(themes, list) or len(themes) == 0
    if signals_missing:
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "field": "signals",
            "type": "structure_error",
            "context": "'signals' array is missing or empty. At least one signal must be generated.",
        })
    if themes_missing:
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "field": "themes",
            "type": "structure_error",
            "context": "'themes' array is missing or empty. At least one theme must be generated.",
        })
    if signals_missing:
        return {"passed": False, "sanitized_output": None, "normalized_output": normalized_output, "violations_log": violations_log}

    valid_entity_ids = {e.get("entity_id") for e in entity_id_map if e.get("entity_id")}
    valid_det_signal_ids = {s.get("signal_id") for s in deterministic_signals if s.get("signal_id")}
    valid_fragment_lookup = {
        fragment.get("fragment_id"): fragment
        for fragment in (essay_fragments or [])
        if fragment.get("fragment_id")
    }

    passed = True
    known_signal_ids = set()
    known_theme_ids = set()
    sanitized_signals = []
    sanitized_themes = []
    sanitized_signal_lookup: Dict[str, Dict[str, Any]] = {}

    for idx, sig in enumerate(signals):
        if not isinstance(sig, dict):
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"signals[{idx}]",
                "type": "structure_error",
                "context": "Each signal must be an object.",
            })
            passed = False
            continue

        sig_passed = True
        required = [
            "signal_id",
            "title",
            "core_observation",
            "interview_opening",
            "referenced_entity_ids",
            "supporting_det_signal_ids",
        ]
        for field in required:
            value = sig.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                violations_log.append({
                    "violation_id": str(uuid.uuid4()),
                    "field": f"signals[{idx}].{field}",
                    "type": "missing_field",
                    "context": f"Required field '{field}' is missing or empty.",
                })
                sig_passed = False
                passed = False

        signal_id = sig.get("signal_id")
        if not signal_id or not re.match(r"^SIG-\d{3}$", str(signal_id)):
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"signals[{idx}].signal_id",
                "type": "invalid_format",
                "context": f"Invalid ID format: {signal_id}",
            })
            sig_passed = False
            passed = False
        elif signal_id in known_signal_ids:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"signals[{idx}].signal_id",
                "type": "duplicate_id",
                "context": f"Duplicate signal ID: {signal_id}",
            })
            sig_passed = False
            passed = False
        else:
            known_signal_ids.add(signal_id)

        referenced_entity_ids = sig.get("referenced_entity_ids", [])
        if not isinstance(referenced_entity_ids, list) or not referenced_entity_ids:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"signals[{idx}].referenced_entity_ids",
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
                        "field": f"signals[{idx}].referenced_entity_ids",
                        "type": "invented_entity_id",
                        "context": f"Invented Entity ID: {ent_id}",
                    })
                    sig_passed = False
                    passed = False

        supporting_det_signal_ids = sig.get("supporting_det_signal_ids", [])
        if not isinstance(supporting_det_signal_ids, list):
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"signals[{idx}].supporting_det_signal_ids",
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
                        "field": f"signals[{idx}].supporting_det_signal_ids",
                        "type": "invented_det_signal_id",
                        "context": f"Invented Deterministic Signal ID: {det_id}",
                    })
                    sig_passed = False
                    passed = False

        supporting_fragment_ids = sig.get("supporting_fragment_ids", [])
        if not isinstance(supporting_fragment_ids, list):
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"signals[{idx}].supporting_fragment_ids",
                "type": "invalid_type",
                "context": "supporting_fragment_ids must be an array.",
            })
            sig_passed = False
            passed = False
        else:
            deduped_fragment_ids = []
            for fragment_id in supporting_fragment_ids:
                if fragment_id not in deduped_fragment_ids:
                    deduped_fragment_ids.append(fragment_id)
            supporting_fragment_ids = deduped_fragment_ids

            if len(supporting_fragment_ids) > MAX_FRAGMENT_IDS_PER_SIGNAL:
                violations_log.append({
                    "violation_id": str(uuid.uuid4()),
                    "field": f"signals[{idx}].supporting_fragment_ids",
                    "type": "too_many_fragment_ids",
                    "context": (
                        f"Signal may reference at most {MAX_FRAGMENT_IDS_PER_SIGNAL} fragments; "
                        f"received {len(supporting_fragment_ids)}."
                    ),
                })
                sig_passed = False
                passed = False

            for fragment_id in supporting_fragment_ids:
                fragment = valid_fragment_lookup.get(fragment_id)
                if not fragment:
                    violations_log.append({
                        "violation_id": str(uuid.uuid4()),
                        "field": f"signals[{idx}].supporting_fragment_ids",
                        "type": "invented_fragment_id",
                        "context": f"Invented fragment ID: {fragment_id}",
                    })
                    sig_passed = False
                    passed = False
                    continue

                fragment_entity_id = fragment.get("entity_id")
                if fragment_entity_id not in referenced_entity_ids:
                    violations_log.append({
                        "violation_id": str(uuid.uuid4()),
                        "field": f"signals[{idx}].supporting_fragment_ids",
                        "type": "fragment_entity_mismatch",
                        "context": (
                            f"Fragment {fragment_id} belongs to {fragment_entity_id}, "
                            "which is not present in referenced_entity_ids."
                        ),
                    })
                    sig_passed = False
                    passed = False

        for field in ["title", "core_observation", "interview_opening"]:
            if _append_text_violations(violations_log, f"signals[{idx}].{field}", sig.get(field, ""), rules):
                sig_passed = False
                passed = False

        if not sig_passed:
            continue

        sanitized_signal = {
            "signal_id": signal_id,
            "title": sig.get("title"),
            "core_observation": sig.get("core_observation"),
            "interview_opening": sig.get("interview_opening"),
            "referenced_entity_ids": referenced_entity_ids,
            "supporting_det_signal_ids": supporting_det_signal_ids,
            "supporting_fragment_ids": supporting_fragment_ids,
        }
        sanitized_signals.append(sanitized_signal)
        sanitized_signal_lookup[signal_id] = sanitized_signal

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
        required = ["theme_id", "title", "supporting_signal_ids"]
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

        supporting_signal_ids = theme.get("supporting_signal_ids", [])
        if not isinstance(supporting_signal_ids, list):
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"themes[{idx}].supporting_signal_ids",
                "type": "invalid_type",
                "context": "Theme must provide supporting_signal_ids as an array.",
            })
            theme_passed = False
            passed = False
        else:
            for signal_id in supporting_signal_ids:
                if signal_id not in sanitized_signal_lookup:
                    violations_log.append({
                        "violation_id": str(uuid.uuid4()),
                        "field": f"themes[{idx}].supporting_signal_ids",
                        "type": "unknown_supporting_signal_id",
                        "context": f"Unknown supporting signal ID: {signal_id}",
                    })
                    theme_passed = False
                    passed = False

        for field in ["title"]:
            if _append_text_violations(violations_log, f"themes[{idx}].{field}", theme.get(field, ""), rules):
                theme_passed = False
                passed = False

        if not theme_passed:
            continue

        referenced_entity_ids = []
        for signal_id in supporting_signal_ids:
            signal = sanitized_signal_lookup.get(signal_id)
            if not signal:
                continue
            for entity_id in signal["referenced_entity_ids"]:
                if entity_id not in referenced_entity_ids:
                    referenced_entity_ids.append(entity_id)

        sanitized_themes.append({
            "theme_id": theme_id,
            "title": theme.get("title"),
            "supporting_signal_ids": supporting_signal_ids,
            "referenced_entity_ids": referenced_entity_ids,
        })

    signal_to_theme_ids: Dict[str, List[str]] = {signal["signal_id"]: [] for signal in sanitized_signals}
    for theme in sanitized_themes:
        for signal_id in theme["supporting_signal_ids"]:
            if signal_id in signal_to_theme_ids:
                signal_to_theme_ids[signal_id].append(theme["theme_id"])

    for signal_id, theme_ids in signal_to_theme_ids.items():
        if len(theme_ids) > 1:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": "themes.supporting_signal_ids",
                "type": "signal_linked_multiple_times",
                "context": f"Signal {signal_id} linked to multiple themes: {theme_ids}",
            })
            passed = False
        elif len(theme_ids) == 0:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": "themes.supporting_signal_ids",
                "type": "missing_signal_coverage",
                "context": f"Signal {signal_id} is not linked to any theme.",
            })
            passed = False

    for idx, theme in enumerate(sanitized_themes):
        if not theme["supporting_signal_ids"]:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"themes[{idx}].supporting_signal_ids",
                "type": "orphan_theme",
                "context": f"Theme {theme['theme_id']} has no supporting signals.",
            })
            passed = False

    if passed:
        for signal in sanitized_signals:
            signal["theme_id"] = signal_to_theme_ids[signal["signal_id"]][0]

    return {
        "passed": passed,
        "sanitized_output": {
            "signals": sanitized_signals,
            "themes": sanitized_themes,
        } if passed else None,
        "normalized_output": normalized_output,
        "violations_log": violations_log,
        "policy_version": PolicyConfig.get_version(),
    }


def validate_focus_areas(raw_text: str, call_1_output: dict | None = None) -> Dict[str, Any]:
    logger.debug("Starting Call 2 focus-area validation.")
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

    normalized_output = _normalize_focus_area_output(synthesis_output, rules)
    if not isinstance(normalized_output, dict):
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "field": "root",
            "type": "structure_error",
            "context": "Root is not a JSON object.",
        })
        return {"passed": False, "sanitized_output": None, "normalized_output": normalized_output, "violations_log": violations_log}

    focus_areas = normalized_output.get("focus_areas")
    if not isinstance(focus_areas, list) or len(focus_areas) == 0:
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "field": "focus_areas",
            "type": "structure_error",
            "context": "Missing or empty 'focus_areas' array. At least one focus area must be generated.",
        })
        return {"passed": False, "sanitized_output": None, "normalized_output": normalized_output, "violations_log": violations_log}
    if len(focus_areas) < 2 or len(focus_areas) > 3:
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "field": "focus_areas",
            "type": "invalid_focus_area_count",
            "context": f"Focus areas must contain 2 to 3 items; received {len(focus_areas)}.",
        })
        return {"passed": False, "sanitized_output": None, "normalized_output": normalized_output, "violations_log": violations_log}

    call_1_themes = []
    call_1_signals = []
    if isinstance(call_1_output, dict):
        raw_themes = call_1_output.get("themes", [])
        raw_signals = call_1_output.get("signals", [])
        if isinstance(raw_themes, list):
            call_1_themes = [theme for theme in raw_themes if isinstance(theme, dict)]
        if isinstance(raw_signals, list):
            call_1_signals = [signal for signal in raw_signals if isinstance(signal, dict)]

    expected_theme_ids = {theme.get("theme_id") for theme in call_1_themes if theme.get("theme_id")}
    expected_signal_ids = {signal.get("signal_id") for signal in call_1_signals if signal.get("signal_id")}

    passed = True
    seen_focus_area_ids = set()
    covered_theme_ids = set()
    sanitized_focus_areas = []

    for idx, focus_area in enumerate(focus_areas):
        if not isinstance(focus_area, dict):
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"focus_areas[{idx}]",
                "type": "structure_error",
                "context": "Each focus area must be an object.",
            })
            passed = False
            continue

        item_passed = True
        required = [
            "focus_area_id",
            "title",
            "territory",
            "what_makes_it_worth_time",
            "source_theme_ids",
            "source_signal_ids",
        ]
        for field in required:
            value = focus_area.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                violations_log.append({
                    "violation_id": str(uuid.uuid4()),
                    "field": f"focus_areas[{idx}].{field}",
                    "type": "missing_field",
                    "context": f"Field '{field}' is missing or empty.",
                })
                item_passed = False
                passed = False

        focus_area_id = focus_area.get("focus_area_id")
        if not focus_area_id or not re.match(r"^FA-\d{3}$", str(focus_area_id)):
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"focus_areas[{idx}].focus_area_id",
                "type": "invalid_format",
                "context": f"Invalid focus area ID format: {focus_area_id}",
            })
            item_passed = False
            passed = False
        elif focus_area_id in seen_focus_area_ids:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"focus_areas[{idx}].focus_area_id",
                "type": "duplicate_id",
                "context": f"Duplicate focus_area_id: {focus_area_id}",
            })
            item_passed = False
            passed = False
        else:
            seen_focus_area_ids.add(focus_area_id)

        source_theme_ids = focus_area.get("source_theme_ids", [])
        source_signal_ids = focus_area.get("source_signal_ids", [])
        if not isinstance(source_theme_ids, list) or not source_theme_ids:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"focus_areas[{idx}].source_theme_ids",
                "type": "empty_array",
                "context": "source_theme_ids must be a non-empty array.",
            })
            item_passed = False
            passed = False
        else:
            for theme_id in source_theme_ids:
                if theme_id not in expected_theme_ids:
                    violations_log.append({
                        "violation_id": str(uuid.uuid4()),
                        "field": f"focus_areas[{idx}].source_theme_ids",
                        "type": "broken_linkage",
                        "context": f"Unknown theme_id: {theme_id}",
                    })
                    item_passed = False
                    passed = False
                else:
                    covered_theme_ids.add(theme_id)

        if not isinstance(source_signal_ids, list) or not source_signal_ids:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"focus_areas[{idx}].source_signal_ids",
                "type": "empty_array",
                "context": "source_signal_ids must be a non-empty array.",
            })
            item_passed = False
            passed = False
        else:
            for signal_id in source_signal_ids:
                if signal_id not in expected_signal_ids:
                    violations_log.append({
                        "violation_id": str(uuid.uuid4()),
                        "field": f"focus_areas[{idx}].source_signal_ids",
                        "type": "broken_linkage",
                        "context": f"Unknown signal_id: {signal_id}",
                    })
                    item_passed = False
                    passed = False

        for field in ["title", "territory", "what_makes_it_worth_time"]:
            if _append_text_violations(violations_log, f"focus_areas[{idx}].{field}", focus_area.get(field, ""), rules):
                item_passed = False
                passed = False
            if _append_phrase_violations(
                violations_log,
                f"focus_areas[{idx}].{field}",
                focus_area.get(field, ""),
                FOCUS_AREA_BANNED_PHRASES,
                "framework_language",
            ):
                item_passed = False
                passed = False
            if FOCUS_AREA_PRONOUN_RE.search(str(focus_area.get(field, ""))):
                violations_log.append({
                    "violation_id": str(uuid.uuid4()),
                    "field": f"focus_areas[{idx}].{field}",
                    "type": "gender_inference",
                    "context": "Focus areas should avoid he/she/his/her pronouns unless explicitly sourced.",
                })
                item_passed = False
                passed = False

        if not item_passed:
            continue

        sanitized_focus_areas.append({
            "focus_area_id": focus_area_id,
            "title": focus_area.get("title"),
            "territory": focus_area.get("territory"),
            "what_makes_it_worth_time": focus_area.get("what_makes_it_worth_time"),
            "source_theme_ids": source_theme_ids,
            "source_signal_ids": source_signal_ids,
        })

    missing_theme_ids = expected_theme_ids - covered_theme_ids
    if missing_theme_ids:
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "field": "focus_areas",
            "type": "missing_theme_coverage",
            "context": f"Missing focus-area coverage for theme_ids: {sorted(missing_theme_ids)}",
        })
        passed = False

    return {
        "passed": passed,
        "sanitized_output": {"focus_areas": sanitized_focus_areas} if passed else None,
        "normalized_output": normalized_output,
        "violations_log": violations_log,
        "policy_version": PolicyConfig.get_version(),
    }


def validate_question_groups(raw_text: str, entity_id_map: List[dict], bundle: dict | None = None) -> Dict[str, Any]:
    """
    Agent 15 - Call 3 Validation Layer.
    Strictly validates LLM Call 3 output (question groups only).
    Enforces schema, focus-area coverage/linkage, and neutral language.
    """
    logger.debug("Starting Call 3 question-group validation.")
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

    normalized_output = _normalize_opening_group_output(synthesis_output, rules)
    if not isinstance(normalized_output, dict):
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "field": "root",
            "type": "structure_error",
            "context": "Root is not a JSON object.",
        })
        return {"passed": False, "sanitized_output": None, "normalized_output": normalized_output, "violations_log": violations_log}

    question_groups = normalized_output.get("question_groups")
    if not isinstance(question_groups, list) or len(question_groups) == 0:
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "field": "question_groups",
            "type": "structure_error",
            "context": "Missing or empty 'question_groups' array. At least one group must be generated.",
        })
        return {"passed": False, "sanitized_output": None, "normalized_output": normalized_output, "violations_log": violations_log}

    bundle_focus_areas = []
    if isinstance(bundle, dict):
        raw_focus_areas = bundle.get("focus_areas", [])
        if isinstance(raw_focus_areas, list):
            for item in raw_focus_areas:
                if not isinstance(item, dict):
                    continue
                focus_area = item.get("focus_area")
                if isinstance(focus_area, dict):
                    bundle_focus_areas.append(focus_area)

        if not bundle_focus_areas:
            fallback_focus_areas = bundle.get("focus_areas", [])
            if isinstance(fallback_focus_areas, list):
                bundle_focus_areas = [
                    item for item in fallback_focus_areas
                    if isinstance(item, dict) and item.get("focus_area_id")
                ]

    expected_focus_area_ids = [item.get("focus_area_id") for item in bundle_focus_areas if item.get("focus_area_id")]
    expected_focus_area_id_set = set(expected_focus_area_ids)
    focus_area_lookup = {
        item.get("focus_area_id"): item
        for item in bundle_focus_areas
        if item.get("focus_area_id")
    }

    passed = True
    seen_focus_area_ids = set()
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
        focus_area_id = qg.get("focus_area_id")
        if focus_area_id not in expected_focus_area_id_set:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"question_groups[{idx}].focus_area_id",
                "type": "broken_linkage",
                "context": f"References non-existent focus_area_id: {focus_area_id}",
            })
            qg_passed = False
            passed = False
        elif focus_area_id in seen_focus_area_ids:
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"question_groups[{idx}].focus_area_id",
                "type": "duplicate_focus_area_group",
                "context": f"Duplicate question group for focus_area_id: {focus_area_id}",
            })
            qg_passed = False
            passed = False
        else:
            seen_focus_area_ids.add(focus_area_id)

        group_label = qg.get("group_label")
        if not isinstance(group_label, str) or not group_label.strip():
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"question_groups[{idx}].group_label",
                "type": "missing_field",
                "context": "Field 'group_label' is missing or empty.",
            })
            qg_passed = False
            passed = False
        elif _append_text_violations(violations_log, f"question_groups[{idx}].group_label", group_label, rules):
            qg_passed = False
            passed = False

        line_of_inquiry = qg.get("line_of_inquiry")
        if not isinstance(line_of_inquiry, str) or not line_of_inquiry.strip():
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"question_groups[{idx}].line_of_inquiry",
                "type": "missing_field",
                "context": "Field 'line_of_inquiry' is missing or empty.",
            })
            qg_passed = False
            passed = False
        else:
            if _append_text_violations(violations_log, f"question_groups[{idx}].line_of_inquiry", line_of_inquiry, rules):
                qg_passed = False
                passed = False
            if _append_phrase_violations(
                violations_log,
                f"question_groups[{idx}].line_of_inquiry",
                line_of_inquiry,
                FOCUS_AREA_BANNED_PHRASES,
                "framework_language",
            ):
                qg_passed = False
                passed = False

        expected_focus_area = focus_area_lookup.get(focus_area_id, {})
        expected_theme_ids = expected_focus_area.get("source_theme_ids", []) if isinstance(expected_focus_area, dict) else []
        expected_signal_ids = expected_focus_area.get("source_signal_ids", []) if isinstance(expected_focus_area, dict) else []

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
            for q_idx, question in enumerate(questions):
                if not isinstance(question, dict):
                    violations_log.append({
                        "violation_id": str(uuid.uuid4()),
                        "field": f"question_groups[{idx}].questions[{q_idx}]",
                        "type": "structure_error",
                        "context": "Each question must be an object.",
                    })
                    qg_passed = False
                    passed = False
                    continue
                question_id = question.get("question_id")
                if not isinstance(question_id, str) or not question_id.strip():
                    violations_log.append({
                        "violation_id": str(uuid.uuid4()),
                        "field": f"question_groups[{idx}].questions[{q_idx}].question_id",
                        "type": "missing_field",
                        "context": "Each question must have a non-empty question_id.",
                    })
                    qg_passed = False
                    passed = False
                question_text = question.get("question")
                if not isinstance(question_text, str) or not question_text.strip():
                    violations_log.append({
                        "violation_id": str(uuid.uuid4()),
                        "field": f"question_groups[{idx}].questions[{q_idx}].question",
                        "type": "missing_field",
                        "context": "Field 'question' is missing or empty.",
                    })
                    qg_passed = False
                    passed = False
                    continue
                if _append_text_violations(
                    violations_log,
                    f"question_groups[{idx}].questions[{q_idx}].question",
                    question_text,
                    rules,
                ):
                    qg_passed = False
                    passed = False
                if isinstance(question_text, str):
                    if _append_phrase_violations(
                        violations_log,
                        f"question_groups[{idx}].questions[{q_idx}].question",
                        question_text,
                        QUESTION_BANNED_PHRASES,
                        "generic_question_form",
                    ):
                        qg_passed = False
                        passed = False
                    if q_idx == 0 and FIRST_QUESTION_CONTENTION_RE.search(question_text):
                        violations_log.append({
                            "violation_id": str(uuid.uuid4()),
                            "field": f"question_groups[{idx}].questions[{q_idx}].question",
                            "type": "premature_contention",
                            "context": "The opening question should not begin with a contrastive contention (yet/despite/while). Give the applicant room to establish their frame first.",
                        })
                        qg_passed = False
                        passed = False

            if not 2 <= len(questions) <= 4:
                violations_log.append({
                    "violation_id": str(uuid.uuid4()),
                    "field": f"question_groups[{idx}].questions",
                    "type": "invalid_question_count",
                    "context": f"Question groups must contain 2 to 4 questions; received {len(questions)}.",
                })
                qg_passed = False
                passed = False

        source_theme_ids = qg.get("source_theme_ids", [])
        source_signal_ids = qg.get("source_signal_ids", [])

        if not isinstance(source_theme_ids, list) or sorted(source_theme_ids) != sorted(expected_theme_ids):
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"question_groups[{idx}].source_theme_ids",
                "type": "broken_linkage",
                "context": f"source_theme_ids must match focus area {focus_area_id}.",
            })
            qg_passed = False
            passed = False

        if not isinstance(source_signal_ids, list) or sorted(source_signal_ids) != sorted(expected_signal_ids):
            violations_log.append({
                "violation_id": str(uuid.uuid4()),
                "field": f"question_groups[{idx}].source_signal_ids",
                "type": "broken_linkage",
                "context": f"source_signal_ids must match focus area {focus_area_id}.",
            })
            qg_passed = False
            passed = False

        if not qg_passed:
            continue

        sanitized_question_groups.append({
            "focus_area_id": focus_area_id,
            "group_label": group_label,
            "line_of_inquiry": line_of_inquiry,
            "questions": questions,
            "source_theme_ids": source_theme_ids,
            "source_signal_ids": source_signal_ids,
        })

    missing_focus_area_ids = expected_focus_area_id_set - seen_focus_area_ids
    extra_focus_area_ids = seen_focus_area_ids - expected_focus_area_id_set
    if missing_focus_area_ids:
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "field": "question_groups",
            "type": "missing_focus_area_coverage",
            "context": f"Missing question groups for focus_area_ids: {sorted(missing_focus_area_ids)}",
        })
        passed = False
    if extra_focus_area_ids:
        violations_log.append({
            "violation_id": str(uuid.uuid4()),
            "field": "question_groups",
            "type": "extra_focus_area_coverage",
            "context": f"Unexpected question groups for focus_area_ids: {sorted(extra_focus_area_ids)}",
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
