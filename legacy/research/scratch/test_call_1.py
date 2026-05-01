import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

env_path = Path("c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/.env")
load_dotenv(env_path)

sys.path.insert(0, str(env_path.parent))

from app.llm.client import generate
from app.agents.signal_interpreter import build_signal_interpreter_messages

# We will load the exact projection from the canonical_data in our run
run_dir = Path("/app/tests/outputs/stage_1_7_runs/20260413T173359Z_Dummy_App_1_v8_filled")
with open(run_dir / "canonical_data.json", "r") as f:
    canonical = json.load(f)

from app.projection.ros_projector import project_ros
from app.agents.signal_detector import detect_signals
from app.agents.projection_builder import build_projection

page_1, page_2, page_3, _, entity_id_map = project_ros(canonical)
deterministic_signals = detect_signals(canonical, entity_id_map)
projection = build_projection(canonical, entity_id_map, deterministic_signals)

messages = build_signal_interpreter_messages(projection)
import httpx
from app.config import settings

print("Sending direct request to LLM (Call 1) with FULL prompt...")
payload = {
    "model": "google/gemini-2.5-flash-lite",
    "messages": messages,
    "temperature": settings.LLM_TEMPERATURE,
    "max_tokens": settings.AICREDITS_GENERATION_MAX_TOKENS,
    "response_format": {"type": "json_object"} if settings.LLM_JSON_MODE else None,
}
# Remove None keys
payload = {k: v for k, v in payload.items() if v is not None}

headers = {
    "Authorization": f"Bearer {settings.AICREDITS_GENERATION_API_KEY}",
    "Content-Type": "application/json",
}

try:
    response = httpx.post(
        f"{settings.AICREDITS_BASE_URL.rstrip('/')}/chat/completions",
        json=payload,
        headers=headers,
        timeout=300.0,
    )
    print(f"Status Code: {response.status_code}")
    print("\n--- RAW JSON RESPONSE ---")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
