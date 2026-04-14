import json
from pathlib import Path

def compile_questions():
    base = Path("provider_testing/benchmarking_v2")
    output = []
    
    for provider_dir in base.iterdir():
        if not provider_dir.is_dir(): continue
        for json_file in provider_dir.glob("*.json"):
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            model_id = data.get("metrics", {}).get("model")
            call_2 = data.get("call_2_question_groups", {})
            groups = call_2.get("question_groups", []) if isinstance(call_2, dict) else []
            
            output.append(f"=== MODEL: {model_id} ===")
            output.append(f"Total Groups: {len(groups)}")
            for i, group in enumerate(groups, 1):
                output.append(f"\nGroup {i}: {group.get('group_title', 'Untitled')}")
                for j, q in enumerate(group.get('questions', []), 1):
                    output.append(f"  Q{j}: {q}")
            output.append("\n" + "="*50 + "\n")
            
    with open("scratch/compiled_questions.txt", "w") as f:
        f.write("\n".join(output))

if __name__ == "__main__":
    compile_questions()
