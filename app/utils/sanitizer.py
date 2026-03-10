import uuid
from typing import Any

def sanitize_for_json(data: Any) -> Any:
    """
    Recursively walk dictionaries and lists to convert UUID objects to strings,
    ensuring the data is JSON serializable for database insertion.
    """
    if isinstance(data, dict):
        return {k: sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_json(i) for i in data]
    elif isinstance(data, uuid.UUID):
        return str(data)
    else:
        return data
