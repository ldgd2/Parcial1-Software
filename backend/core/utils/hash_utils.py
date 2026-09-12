import hashlib
import json
from typing import Any

def generate_deterministic_hash(data: Any) -> str:
    """
    Generates a deterministic SHA-256 hash for a given dictionary or list.
    It sorts the keys alphabetically so the hash is consistent regardless of key order.
    """
    json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
