import re
from typing import Any


PROHIBITED_TERMS = [
    "Strength", "Weakness", "Outstanding", "Exceptional", "Deficiency",
    "Below average", "Underperformance", "High potential", "Top candidate",
    "Risk factor", "Admit", "Reject", "Likelihood", "Impressive",
    "Concerning", "Excellent", "Poor", "Weak", "Strong",
    "Competitive", "Uncompetitive"
]

ALLOWED_SIGNAL_TYPES = [
    "academic_trajectory_shift",
    "academic_transition_event",
    "subject_imbalance",
    "leadership_depth",
    "sustained_commitment",
    "test_section_imbalance",
]

MAX_SIGNALS = 6
ACADEMIC_TRAJECTORY_THRESHOLD = 7.0
SUBJECT_IMBALANCE_THRESHOLD = 12.0
TEST_SECTION_IMBALANCE_THRESHOLD = 8.0
LEADERSHIP_MIN_DURATION = 1.0
PERSONAL_ACTIVITY_MIN_DURATION = 3.0

INTERVIEW_RELEVANT_ACADEMIC_LEVELS = {"10TH", "11TH", "12TH"}
NON_PERSONAL_LEVEL_PRIORITY = {
    "international": 6,
    "national": 5,
    "state": 4,
    "district": 3,
    "regional": 2,
    "school": 1,
    "institutional": 1,
    "local": 1,
}
DEPRIORITIZED_SUBJECT_NAMES = {
    "sanskrit",
    "hindi",
}

SIGNAL_TYPE_PRIORITY = {
    "academic_trajectory_shift": 1,
    "academic_transition_event": 2,
    "subject_imbalance": 3,
    "leadership_depth": 4,
    "sustained_commitment": 5,
    "test_section_imbalance": 6,
}


def detect_signals(canonical: dict, entity_id_map: list) -> list[dict]:
    """
    Agent 12: Rule-based deterministic signal detection.
    Surfaces high-signal structured patterns from academics, tests, and
    activities without semantic interpretation.
    """
    entity_lookup = {e["entity_id"]: e for e in entity_id_map}

    def check_prohibited(text: str):
        if not text:
            return
        for term in PROHIBITED_TERMS:
            if re.search(re.escape(term), text, re.IGNORECASE):
                raise RuntimeError(f"Prohibited language detected: '{term}' in '{text}'")

    def clean_text(value: Any) -> str | None:
        if value is None:
            return None
        cleaned = re.sub(r"\s+", " ", str(value)).strip()
        return cleaned or None

    def safe_float(value: Any) -> float | None:
        if value is None:
            return None
        match = re.search(r"-?\d+\.?\d*", str(value))
        if not match:
            return None
        try:
            return float(match.group(0))
        except ValueError:
            return None

    def to_percentage(score: Any, max_score: Any = None) -> float | None:
        score_value = safe_float(score)
        if score_value is None:
            return None
        max_value = safe_float(max_score) or 100.0
        if max_value <= 0:
            return None
        return (score_value / max_value) * 100.0

    def effective_percentage(entry: dict) -> float | None:
        return to_percentage(entry.get("score_raw") or entry.get("predicted_score_raw"), entry.get("max_score_raw"))

    def resolve_entity_id(collection: str, *descriptor_candidates: Any) -> str | None:
        normalized_candidates = [clean_text(candidate) for candidate in descriptor_candidates if clean_text(candidate)]
        if not normalized_candidates:
            return None
        for mapping in entity_id_map:
            if mapping.get("collection") != collection:
                continue
            descriptor = clean_text(mapping.get("descriptor"))
            if descriptor and descriptor in normalized_candidates:
                return mapping.get("entity_id")
        return None

    def activity_detail_score(entry: dict) -> int:
        return sum(
            1
            for field in ("activity_name", "position_title", "duration", "level", "roles_and_responsibilities")
            if clean_text(entry.get(field))
        )

    def level_priority(level: str | None) -> int:
        normalized_level = (clean_text(level) or "").lower()
        if not normalized_level:
            return 0
        if normalized_level == "personal":
            return 0
        return NON_PERSONAL_LEVEL_PRIORITY.get(normalized_level, 1)

    def build_subject_metrics(entry: dict) -> list[dict[str, Any]]:
        metrics = []
        for subject in entry.get("subject_entries", []) or []:
            subject_name = clean_text(subject.get("subject_name"))
            percentage = to_percentage(subject.get("score_raw") or subject.get("predicted_score_raw"), subject.get("max_score_raw"))
            if subject_name and percentage is not None:
                metrics.append(
                    {
                        "subject_name": subject_name,
                        "percentage": percentage,
                    }
                )
        return metrics

    def is_deprioritized_subject(subject_name: str | None) -> bool:
        normalized = (clean_text(subject_name) or "").lower()
        return normalized in DEPRIORITIZED_SUBJECT_NAMES

    def activity_signal_sort_key(candidate: dict) -> tuple:
        metadata = candidate["metadata"]
        return (
            SIGNAL_TYPE_PRIORITY[candidate["signal_type"]],
            -metadata.get("level_priority", 0),
            -metadata.get("detail_score", 0),
            -metadata.get("primary_magnitude", 0.0),
            candidate["observation"],
        )

    def generic_signal_sort_key(candidate: dict) -> tuple:
        metadata = candidate["metadata"]
        return (
            SIGNAL_TYPE_PRIORITY[candidate["signal_type"]],
            -metadata.get("level_priority", 0),
            -metadata.get("detail_score", 0),
            -metadata.get("primary_magnitude", 0.0),
            candidate["observation"],
        )

    def build_signal(
        signal_type: str,
        observation: str,
        referenced_entity_ids: list[str],
        source_collection: str,
        metadata: dict[str, Any],
    ) -> dict:
        return {
            "signal_type": signal_type,
            "observation": observation,
            "referenced_entity_ids": referenced_entity_ids,
            "source_collection": source_collection,
            "metadata": metadata,
        }

    sorted_academic_entries = sorted(
        [
            entry
            for entry in canonical.get("academic_entries", [])
            if clean_text(entry.get("academic_level")) in INTERVIEW_RELEVANT_ACADEMIC_LEVELS
        ],
        key=lambda item: (
            safe_float(item.get("academic_year")) if safe_float(item.get("academic_year")) is not None else 0.0,
            str(item.get("academic_level") or "")
        )
    )

    candidates: list[dict] = []

    # academic_trajectory_shift + academic_transition_event
    for previous_entry, current_entry in zip(sorted_academic_entries, sorted_academic_entries[1:]):
        prev_entity_id = resolve_entity_id("academic_entries", previous_entry.get("academic_level"))
        current_entity_id = resolve_entity_id("academic_entries", current_entry.get("academic_level"))
        if not prev_entity_id or not current_entity_id:
            continue

        previous_level = clean_text(previous_entry.get("academic_level")) or "prior level"
        current_level = clean_text(current_entry.get("academic_level")) or "next level"

        previous_percentage = effective_percentage(previous_entry)
        current_percentage = effective_percentage(current_entry)
        if previous_percentage is not None and current_percentage is not None:
            delta = current_percentage - previous_percentage
            if abs(delta) >= ACADEMIC_TRAJECTORY_THRESHOLD:
                direction = "upward" if delta > 0 else "downward"
                candidates.append(
                    build_signal(
                        "academic_trajectory_shift",
                        (
                            f"Performance shifted {direction} from {previous_level} to "
                            f"{current_level} by {abs(delta):.1f} percentage points."
                        ),
                        [prev_entity_id, current_entity_id],
                        "academic_entries",
                        {"primary_magnitude": abs(delta)},
                    )
                )

        board_changed = (
            clean_text(previous_entry.get("board_name"))
            and clean_text(current_entry.get("board_name"))
            and clean_text(previous_entry.get("board_name")) != clean_text(current_entry.get("board_name"))
        )
        school_changed = (
            clean_text(previous_entry.get("school_name"))
            and clean_text(current_entry.get("school_name"))
            and clean_text(previous_entry.get("school_name")) != clean_text(current_entry.get("school_name"))
        )
        if board_changed or school_changed:
            if board_changed and school_changed:
                observation = f"School and board changed between {previous_level} and {current_level}."
                magnitude = 2.0
            elif board_changed:
                observation = f"Board changed between {previous_level} and {current_level}."
                magnitude = 1.0
            else:
                observation = f"School changed between {previous_level} and {current_level}."
                magnitude = 1.0

            candidates.append(
                build_signal(
                    "academic_transition_event",
                    observation,
                    [prev_entity_id, current_entity_id],
                    "academic_entries",
                    {"primary_magnitude": magnitude},
                )
            )

    # subject_imbalance
    for entry in sorted_academic_entries:
        entity_id = resolve_entity_id("academic_entries", entry.get("academic_level"))
        if not entity_id:
            continue

        subject_metrics = build_subject_metrics(entry)
        if len(subject_metrics) < 3:
            continue

        prioritized_subject_metrics = [
            item for item in subject_metrics if not is_deprioritized_subject(item["subject_name"])
        ]
        if len(prioritized_subject_metrics) < 2:
            continue

        weakest_subject = min(prioritized_subject_metrics, key=lambda item: item["percentage"])
        strongest_subject = max(prioritized_subject_metrics, key=lambda item: item["percentage"])
        spread = strongest_subject["percentage"] - weakest_subject["percentage"]
        if spread >= SUBJECT_IMBALANCE_THRESHOLD:
            level = clean_text(entry.get("academic_level")) or "this academic level"
            candidates.append(
                build_signal(
                    "subject_imbalance",
                    (
                        f"In {level}, {weakest_subject['subject_name']} was the lowest subject at "
                        f"{weakest_subject['percentage']:.1f}% and {strongest_subject['subject_name']} "
                        f"was the highest at {strongest_subject['percentage']:.1f}%."
                    ),
                    [entity_id],
                    "academic_entries",
                    {"primary_magnitude": spread},
                )
            )

    # cross-grade repeated strongest/weakest subjects
    weakest_subject_occurrences: dict[str, list[dict[str, Any]]] = {}
    strongest_subject_occurrences: dict[str, list[dict[str, Any]]] = {}
    for entry in sorted_academic_entries:
        entity_id = resolve_entity_id("academic_entries", entry.get("academic_level"))
        if not entity_id:
            continue

        subject_metrics = build_subject_metrics(entry)
        if not subject_metrics:
            continue

        weakest_subject = min(subject_metrics, key=lambda item: item["percentage"])
        strongest_subject = max(subject_metrics, key=lambda item: item["percentage"])
        level = clean_text(entry.get("academic_level")) or "this level"

        weakest_subject_occurrences.setdefault(weakest_subject["subject_name"], []).append(
            {
                "entity_id": entity_id,
                "level": level,
                "percentage": weakest_subject["percentage"],
            }
        )
        strongest_subject_occurrences.setdefault(strongest_subject["subject_name"], []).append(
            {
                "entity_id": entity_id,
                "level": level,
                "percentage": strongest_subject["percentage"],
            }
        )

    for subject_name, occurrences in weakest_subject_occurrences.items():
        if len(occurrences) < 2:
            continue
        ordered_occurrences = sorted(occurrences, key=lambda item: item["level"])
        level_list = " and ".join(item["level"] for item in ordered_occurrences)
        candidates.append(
            build_signal(
                "subject_imbalance",
                (
                    f"{subject_name} was the lowest-scoring subject across {level_list}, with normalized scores "
                    f"ranging from {min(item['percentage'] for item in ordered_occurrences):.1f}% to "
                    f"{max(item['percentage'] for item in ordered_occurrences):.1f}%."
                ),
                [item["entity_id"] for item in ordered_occurrences],
                "academic_entries",
                {"primary_magnitude": len(ordered_occurrences)},
            )
        )

    for subject_name, occurrences in strongest_subject_occurrences.items():
        if len(occurrences) < 2:
            continue
        ordered_occurrences = sorted(occurrences, key=lambda item: item["level"])
        level_list = " and ".join(item["level"] for item in ordered_occurrences)
        candidates.append(
            build_signal(
                "subject_imbalance",
                (
                    f"{subject_name} was the highest-scoring subject across {level_list}, with normalized scores "
                    f"ranging from {min(item['percentage'] for item in ordered_occurrences):.1f}% to "
                    f"{max(item['percentage'] for item in ordered_occurrences):.1f}%."
                ),
                [item["entity_id"] for item in ordered_occurrences],
                "academic_entries",
                {"primary_magnitude": len(ordered_occurrences)},
            )
        )

    # leadership_depth + sustained_commitment
    activity_candidates = []
    for entry in canonical.get("activity_entries", []):
        activity_type = clean_text(entry.get("activity_type"))
        entity_id = resolve_entity_id(
            "activity_entries",
            entry.get("activity_name"),
            entry.get("position_title"),
            activity_type,
        )
        if not entity_id:
            continue

        duration = safe_float(entry.get("duration"))
        name = clean_text(entry.get("activity_name"))
        position = clean_text(entry.get("position_title"))
        level = clean_text(entry.get("level"))
        responsibilities = clean_text(entry.get("roles_and_responsibilities"))
        detail_score = activity_detail_score(entry)
        non_personal_level_priority = level_priority(level)

        if activity_type == "leadership":
            if position:
                duration_text = f"{duration:.1f}-year duration" if duration is not None else "undisclosed duration"
                activity_candidates.append(
                    build_signal(
                        "leadership_depth",
                        (
                            f"Leadership experience includes the role '{position}' with "
                            f"{duration_text}."
                        ),
                        [entity_id],
                        "activity_entries",
                        {
                            "primary_magnitude": duration or 0.0,
                            "detail_score": detail_score,
                            "level_priority": non_personal_level_priority,
                        },
                    )
                )
            continue

        if activity_type in {"extracurricular", "co_curricular"}:
            if non_personal_level_priority > 0:
                label = name or position or activity_type
                activity_candidates.append(
                    build_signal(
                        "sustained_commitment",
                        f"{label} reached {level} level participation over {duration:.1f} years." if duration is not None
                        else f"{label} reached {level} level participation.",
                        [entity_id],
                        "activity_entries",
                        {
                            "primary_magnitude": duration if duration is not None else float(non_personal_level_priority),
                            "detail_score": detail_score,
                            "level_priority": non_personal_level_priority,
                        },
                    )
                )
                continue

            if (
                level and level.lower() == "personal"
                and duration is not None
                and duration >= PERSONAL_ACTIVITY_MIN_DURATION
                and position
                and responsibilities
            ):
                label = name or position or activity_type
                activity_candidates.append(
                    build_signal(
                        "sustained_commitment",
                        (
                            f"{label} is a Personal activity sustained for {duration:.1f} years "
                            f"with a structured role and responsibilities."
                        ),
                        [entity_id],
                        "activity_entries",
                        {
                            "primary_magnitude": duration,
                            "detail_score": detail_score,
                            "level_priority": 0,
                        },
                    )
                )

    activity_candidates.sort(key=activity_signal_sort_key)
    candidates.extend(activity_candidates)

    # test_section_imbalance
    for entry in canonical.get("test_entries", []):
        entity_id = resolve_entity_id("test_entries", entry.get("test_name"))
        if not entity_id:
            continue

        section_scores = [
            safe_float(section.get("raw_score"))
            for section in entry.get("sectional_scores", []) or []
            if safe_float(section.get("raw_score")) is not None
        ]
        if len(section_scores) < 2:
            continue

        spread = max(section_scores) - min(section_scores)
        if spread >= TEST_SECTION_IMBALANCE_THRESHOLD:
            test_name = clean_text(entry.get("test_name")) or "the test"
            candidates.append(
                build_signal(
                    "test_section_imbalance",
                    (
                        f"Test section scores show an {spread:.1f}-point spread between "
                        f"the highest and lowest sections within {test_name}."
                    ),
                    [entity_id],
                    "test_entries",
                    {"primary_magnitude": spread},
                )
            )

    # Global selection: de-duplicate, order, cap, assign DET ids only after final selection.
    deduped_candidates = []
    seen = set()
    for candidate in sorted(candidates, key=generic_signal_sort_key):
        dedupe_key = (
            candidate["signal_type"],
            tuple(candidate["referenced_entity_ids"]),
            candidate["observation"],
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        deduped_candidates.append(candidate)

    selected_candidates = deduped_candidates[:MAX_SIGNALS]

    final_signals = []
    for index, candidate in enumerate(selected_candidates, start=1):
        signal = {
            "signal_id": f"DET-{index:03}",
            "signal_type": candidate["signal_type"],
            "observation": candidate["observation"],
            "referenced_entity_ids": candidate["referenced_entity_ids"],
            "source_collection": candidate["source_collection"],
        }
        final_signals.append(signal)

    for signal in final_signals:
        if signal["signal_type"] not in ALLOWED_SIGNAL_TYPES:
            raise RuntimeError(f"Invalid signal type: {signal['signal_type']}")

        check_prohibited(str(signal["observation"]))

        for entity_id in signal["referenced_entity_ids"]:
            if entity_id not in entity_lookup:
                raise RuntimeError(f"Entity ID {entity_id} not found in entity_id_map")

    return final_signals
