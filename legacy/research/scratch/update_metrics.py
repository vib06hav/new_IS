import json
import os
from pathlib import Path

# Mapping of the cost data parsed from the user's log
cost_data = {
    "google/gemini-2.5-flash-lite": {
        "call_1_prompt_tokens": 9765, "call_1_completion_tokens": 1487, "call_1_cost_inr": 0.1739,
        "call_2_prompt_tokens": 6529, "call_2_completion_tokens": 432, "call_2_cost_inr": 0.0914,
        "total_cost_inr": 0.2653
    },
    "openai/gpt-4o-mini": {
        "call_1_prompt_tokens": 8432, "call_1_completion_tokens": 891, "call_1_cost_inr": 0.1992,
        "call_2_prompt_tokens": 5552, "call_2_completion_tokens": 307, "call_2_cost_inr": 0.1126,
        "total_cost_inr": 0.3118
    },
    "openai/gpt-5.4-nano": {
        "call_1_prompt_tokens": 8431, "call_1_completion_tokens": 1442, "call_1_cost_inr": 0.3862,
        "call_2_prompt_tokens": 6163, "call_2_completion_tokens": 505, "call_2_cost_inr": 0.2063,
        "total_cost_inr": 0.5925
    },
    "google/gemini-3.1-flash-lite-preview": {
        "call_1_prompt_tokens": 9765, "call_1_completion_tokens": 1090, "call_1_cost_inr": 0.4512,
        "call_2_prompt_tokens": 5866, "call_2_completion_tokens": 422, "call_2_cost_inr": 0.2324,
        "total_cost_inr": 0.6836
    },
    "openai/gpt-4.1-mini": {
        "call_1_prompt_tokens": 16864, "call_1_completion_tokens": 2856, "call_1_cost_inr": 1.0712, # including retry
        "call_2_prompt_tokens": 6944, "call_2_completion_tokens": 498, "call_2_cost_inr": 0.3957,
        "total_cost_inr": 1.4669
    },
    "openai/gpt-5.4-mini": {
        "call_1_prompt_tokens": 8431, "call_1_completion_tokens": 1644, "call_1_cost_inr": 1.5189,
        "call_2_prompt_tokens": 7100, "call_2_completion_tokens": 528, "call_2_cost_inr": 0.8525,
        "total_cost_inr": 2.3714
    },
    "anthropic/claude-haiku-4.5": {
        "call_1_prompt_tokens": 9962, "call_1_completion_tokens": 2176, "call_1_cost_inr": 2.3071,
        "call_2_prompt_tokens": 8518, "call_2_completion_tokens": 703, "call_2_cost_inr": 1.3320,
        "total_cost_inr": 3.6391
    }
}

def inject():
    base = Path("provider_testing/benchmarking_v2")
    for provider_dir in base.iterdir():
        if not provider_dir.is_dir(): continue
        for json_file in provider_dir.glob("*.json"):
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            model_id = data.get("metrics", {}).get("model")
            if model_id in cost_data:
                cost_info = cost_data[model_id]
                data["metrics"].update(cost_info)
                
                with open(json_file, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"Updated {json_file.name}")

if __name__ == "__main__":
    inject()
