from typing import Dict, Any

def assemble_ros_v1(
    page_1: Dict[str, Any],
    page_2: Dict[str, Any],
    page_3: Dict[str, Any],
    llm_output: Dict[str, Any],
    report_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Deterministic ROS assembly.
    Merges Pages 1-3 (from projection), Pages 4-5 (from Validation Filter),
    and report_metadata into the final ROS v1 JSON document.
    """
    
    ros_v1 = {
        "report_metadata": report_metadata,
        "page_1_background_profile": page_1,
        "page_2_academic_and_engagement": page_2,
        "page_3_essays": page_3,
        "page_4_focus_themes": {
            "themes": llm_output.get("themes", [])
        },
        "page_5_question_groups": {
            "question_groups": llm_output.get("question_groups", [])
        }
    }
    
    return ros_v1
