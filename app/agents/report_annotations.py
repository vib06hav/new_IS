from typing import Any


PAGE_2_COLLECTIONS = {"academic_entries", "test_entries", "activity_entries"}


def build_report_annotations(
    signals: list[dict[str, Any]],
    themes: list[dict[str, Any]],
    entity_id_map: list[dict[str, Any]],
    essay_fragments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    theme_ids_by_signal_id = {
        signal.get("signal_id"): [signal.get("theme_id")] if signal.get("theme_id") else []
        for signal in signals
    }
    entity_collection_by_id = {
        mapping.get("entity_id"): mapping.get("collection")
        for mapping in entity_id_map
        if mapping.get("entity_id") and mapping.get("collection")
    }
    fragment_lookup = {
        fragment.get("fragment_id"): fragment
        for fragment in (essay_fragments or [])
        if fragment.get("fragment_id")
    }

    page_2_entities: dict[str, dict[str, list[str]]] = {}
    page_3_fragments: dict[str, list[dict[str, Any]]] = {}

    for signal in signals:
        signal_id = signal.get("signal_id")
        theme_ids = theme_ids_by_signal_id.get(signal_id, [])

        for entity_id in signal.get("referenced_entity_ids", []):
            if entity_collection_by_id.get(entity_id) not in PAGE_2_COLLECTIONS:
                continue

            annotation = page_2_entities.setdefault(entity_id, {"signal_ids": [], "theme_ids": []})
            if signal_id and signal_id not in annotation["signal_ids"]:
                annotation["signal_ids"].append(signal_id)
            for theme_id in theme_ids:
                if theme_id and theme_id not in annotation["theme_ids"]:
                    annotation["theme_ids"].append(theme_id)

        for fragment_id in signal.get("supporting_fragment_ids", []) or []:
            fragment = fragment_lookup.get(fragment_id)
            if not fragment:
                continue

            entity_id = fragment.get("entity_id")
            if not entity_id:
                continue

            essay_annotations = page_3_fragments.setdefault(entity_id, [])
            existing = next((item for item in essay_annotations if item["fragment_id"] == fragment_id), None)
            if not existing:
                existing = {
                    "fragment_id": fragment_id,
                    "start_char": fragment.get("start_char"),
                    "end_char": fragment.get("end_char"),
                    "signal_ids": [],
                    "theme_ids": [],
                }
                essay_annotations.append(existing)

            if signal_id and signal_id not in existing["signal_ids"]:
                existing["signal_ids"].append(signal_id)
            for theme_id in theme_ids:
                if theme_id and theme_id not in existing["theme_ids"]:
                    existing["theme_ids"].append(theme_id)

    for entity_id, fragments in page_3_fragments.items():
        page_3_fragments[entity_id] = sorted(fragments, key=lambda item: (item["start_char"], item["end_char"]))

    return {
        "page_1_entities": {},
        "page_2_entities": page_2_entities,
        "page_3_fragments": page_3_fragments,
    }
