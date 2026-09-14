"""One machine-readable record per extraction.

The point is to be able to answer "what did this cost us last week" without
reading prose, and to do it without putting customer writing into the logs of an
extraction service.
"""

import hashlib
import json
import sys
from typing import Any, Dict


def fingerprint(text: str) -> str:
    """Enough to correlate two records; useless for reading what was written."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def emit(record: Dict[str, Any]) -> None:
    """Default sink: one JSON object per line on stdout."""
    sys.stdout.write(json.dumps(record, ensure_ascii=False) + "\n")
