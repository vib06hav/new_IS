from typing import Optional

from app.utils.text_normalization import normalize_label


SECTION_TYPE_ALIASES = {
    "document_start": "document_start",
    "personal details": "personal_details",
    "personal information": "personal_details",
    "parent details": "parent_details",
    "father details": "parent_details",
    "mother details": "parent_details",
    "sibling details": "sibling_details",
    "address details": "address_details",
    "communication address": "address_details",
    "permanent address": "address_details",
    "languages known": "languages",
    "academics": "academics",
    "academic records": "academics",
    "class 9th equivalent": "academics",
    "class 10th equivalent": "academics",
    "class 11th equivalent": "academics",
    "class 12th details": "academics",
    "standardized test scores": "standardized_tests",
    "standardized tests": "standardized_tests",
    "additional test scores": "standardized_tests",
    "joint entrance examination jee main details": "standardized_tests",
    "joint entrance examination jee mains": "standardized_tests",
    "jee mains details": "standardized_tests",
    "jee advance details": "standardized_tests",
    "scholastic assessment test sat details": "standardized_tests",
    "sat details": "standardized_tests",
    "essays": "essays",
    "extra curricular activities outside the classroom": "extracurricular",
    "extracurricular activities": "extracurricular",
    "co curricular activities tinkering research and more": "co_curricular",
    "co curricular activities": "co_curricular",
    "leadership role at school": "leadership",
    "leadership roles": "leadership",
    "activities": "activities",
    "additional information": "additional_information",
    "references": "references",
    "declaration": "declaration",
    "disclosure": "disclosure",
    "consent": "consent",
    "honour pledge": "honour_pledge",
}


def classify_section_label(label: str) -> Optional[str]:
    normalized = normalize_label(label)
    if not normalized:
        return None
    if normalized in SECTION_TYPE_ALIASES:
        return SECTION_TYPE_ALIASES[normalized]

    if "extra" in normalized and "curricul" in normalized:
        return "extracurricular"
    if "co" in normalized and "curricul" in normalized:
        return "co_curricular"
    if "leadership" in normalized:
        return "leadership"
    if any(token in normalized for token in ["class", "academic", "education", "degree", "school"]):
        return "academics"
    if any(token in normalized for token in ["test", "jee", "sat", "act", "examination", "percentile", "score"]):
        return "standardized_tests"
    if "essay" in normalized:
        return "essays"
    if "additional" in normalized:
        return "additional_information"
    if "personal" in normalized:
        return "personal_details"
    if any(token in normalized for token in ["parent", "father", "mother"]):
        return "parent_details"

    return None
