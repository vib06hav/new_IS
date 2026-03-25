from typing import Any, Dict, List


def assemble_ros_v1(
    page_1: Dict[str, Any],
    page_2: Dict[str, Any],
    page_3: Dict[str, Any],
    themes: List[Dict[str, Any]],
    signals: List[Dict[str, Any]],
    question_groups: List[Dict[str, Any]],
    report_metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Deterministic ROS assembly.
    Merges Pages 1-3 (from projection), Call 1 themes for Page 4, Call 2
    question groups for Page 5, and report_metadata into the final ROS v1
    JSON document.
    """

    return {
        "report_metadata": report_metadata,
        "page_1_background_profile": page_1,
        "page_2_academic_and_engagement": page_2,
        "page_3_essays": page_3,
        "page_4_focus_areas": {
            "themes": themes,
            "signals": signals,
        },
        "page_5_question_groups": {
            "question_groups": question_groups,
        },
    }
