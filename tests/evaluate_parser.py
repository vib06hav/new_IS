import json
import os
import sys

# Ensure the root directory is in the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agents.orchestrator import run_pipeline
from tests.evaluation_rules import evaluate

def main():
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'pdfs', 'Application_form_PU_UG24_05894.pdf'))
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'outputs'))
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'latest_output.json')

    print(f"Running pipeline on {pdf_path}...")
    try:
        pipeline_output = run_pipeline(application_id="test_application", pdf_path=pdf_path)
    except Exception as e:
        print(f"Pipeline execution failed: {e}")
        print("Ensure you are running inside the Docker API container where LLM execution can succeed.")
        sys.exit(1)

    # Save output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(pipeline_output, f, indent=2, default=str)
    
    print(f"Pipeline output saved to {output_path}")

    ros_document = pipeline_output.get("ros_v1")
    if not ros_document:
        print("Warning: ros_v1 document is missing from the pipeline output. Evaluating partial response if available.")
        # Try to project it locally if we only have canonical_data
        canonical_data = pipeline_output.get("canonical_data")
        if canonical_data:
            from app.projection.ros_projector import project_ros
            page_1, page_2, page_3, _, _ = project_ros(canonical_data)
            ros_document = {
                "page_1_background_profile": page_1,
                "page_2_academic_and_engagement": page_2,
                "page_3_essays": page_3,
                "page_4_focus_themes": {"themes": []},
                "page_5_question_groups": {"question_groups": []}
            }
        else:
            ros_document = {}

    report = evaluate(ros_document)
    print(report)

if __name__ == "__main__":
    main()
