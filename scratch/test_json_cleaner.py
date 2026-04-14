import re

def _clean_json_response(text: str) -> str:
    if not text:
        return ""
    
    text = text.strip()
    
    # Try to extract content from markdown fences first
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL | re.IGNORECASE)
    if match:
        print("Regex Matched")
        text = match.group(1).strip()
    else:
        print("Regex Failed - Falling back to { }")
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            text = text[start:end+1]
    
    return text.strip()

fenced_input = "```json\n{\n  \"signals\": []\n}\n```"
print(f"Input:\n{fenced_input}")
output = _clean_json_response(fenced_input)
print(f"Output:\n{output}")

preamble_input = "Sure! Here is your JSON:\n```json\n{\n  \"signals\": []\n}\n```\nHope this helps!"
print(f"\nPreamble Input:\n{preamble_input}")
output = _clean_json_response(preamble_input)
print(f"Output:\n{output}")
