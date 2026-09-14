"""Stop paying twice for the same question.

In memory, for the life of the process. A database is out of scope for this
project, and an in-memory store demonstrates the idea without one -- at the cost
of a cache that does not survive a restart, which the results must say plainly
rather than imply otherwise.
"""

import hashlib
import json
from typing import Any, Dict, Optional


def key_for(*, ticket_text: str, system_prompt: str, model: str, json_schema: Dict[str, Any]) -> str:
    """Hash everything that can change the answer, not just the question.

    Keyed on the ticket alone, editing the prompt would keep serving answers the
    old one produced, with nothing to say so. That failure is silent and survives
    a deploy, which makes it worse than the cost it saves.
    """
    material = json.dumps(
        {
            "ticket": ticket_text,
            "prompt": system_prompt,
            "model": model,
            "schema": json_schema,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class InMemoryCache:
    """Successful extractions only. Failures are deliberately not stored."""

    def __init__(self) -> None:
        self._entries: Dict[str, Any] = {}

    def get(self, key: str) -> Optional[Any]:
        return self._entries.get(key)

    def set(self, key: str, value: Any) -> None:
        self._entries[key] = value
