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

def validate_synthesis_output(synthesis_output: Dict[str, Any], sanitize: bool = False) -> Dict[str, Any]:
    """
    Agent 13 - Output Validation Filter.
    Scans LLM output to detect evaluative, ranking, comparative, and prescriptive phrasing.
    Returns: passed (bool), sanitized_output, violations_log
    """
    rules = PolicyConfig.get_prohibited_terms()
    violations_log = []
    
    # Prepare the sanitized structure copy
    sanitized_output = {
        "snapshot": synthesis_output.get("snapshot", ""),
        "discussion_focus_areas": synthesis_output.get("discussion_focus_areas", ""),
        "suggested_questions": synthesis_output.get("suggested_questions", "")
    }
    
    # 1. Scan Snapshot
    snapshot_text = sanitized_output["snapshot"]
    snapshot_violations = _scan_text(snapshot_text, rules)
    for v in snapshot_violations:
        v["field"] = "snapshot"
        violations_log.append(v)
        if sanitize:
            # Minimal sanitize strategy: mask the phrase or drop the sentence
            # For simplicity in Phase 7, we just redact the specific phrase.
            pattern = re.compile(re.escape(v["phrase_matched"]), re.IGNORECASE)
            sanitized_output["snapshot"] = pattern.sub("[REDACTED EVALUATIVE PHRASE]", sanitized_output["snapshot"])
            
    # 2. Scan Discussion Focus Areas
    dfa_text = sanitized_output["discussion_focus_areas"]
    dfa_violations = _scan_text(dfa_text, rules)
    for v in dfa_violations:
        v["field"] = "discussion_focus_areas"
        violations_log.append(v)
        if sanitize:
            pattern = re.compile(re.escape(v["phrase_matched"]), re.IGNORECASE)
            sanitized_output["discussion_focus_areas"] = pattern.sub("[REDACTED]", sanitized_output["discussion_focus_areas"])

    # 3. Scan Suggested Questions
    sq_text = sanitized_output["suggested_questions"]
    sq_violations = _scan_text(sq_text, rules)
    for v in sq_violations:
        v["field"] = "suggested_questions"
        violations_log.append(v)
        if sanitize:
            pattern = re.compile(re.escape(v["phrase_matched"]), re.IGNORECASE)
            sanitized_output["suggested_questions"] = pattern.sub("[REDACTED]", sanitized_output["suggested_questions"])

    passed = len(violations_log) == 0

    return {
        "passed": passed,
        "sanitized_output": sanitized_output if sanitize or passed else synthesis_output,
        "violations_log": violations_log,
        "policy_version": PolicyConfig.get_version()
    }
