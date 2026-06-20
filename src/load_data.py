import gzip
import json
import os
from typing import Generator, Dict, Any, Optional

def stream_candidates(file_path: str) -> Generator[Dict[str, Any], None, None]:
    """
    Streams candidates line-by-line from a gzipped or plain JSONL file.
    Ensures O(1) memory overhead by not loading the entire array into RAM.
    """
    if not os.path.exists(file_path):
        # Graceful fallback or empty stream
        return

    is_gzip = file_path.endswith(".gz")
    
    open_func = gzip.open if is_gzip else open
    mode = "rt" if is_gzip else "r"
    encoding = "utf-8"

    try:
        with open_func(file_path, mode, encoding=encoding) as f:
            for line_no, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    candidate = json.loads(line)
                    # Support both standard key formats
                    if "candidate_id" not in candidate and "id" in candidate:
                        candidate["candidate_id"] = candidate["id"]
                    yield candidate
                except json.JSONDecodeError as jde:
                    # Robust handling of malformed lines
                    continue
    except Exception as e:
        # Catch file errors or access errors
        pass
