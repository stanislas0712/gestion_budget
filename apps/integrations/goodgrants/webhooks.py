"""
GoodGrants webhooks entrypoints (Django views will call these helpers).

We keep this module free of Django view concerns to keep views thin.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WebhookEvent:
    event_type: str
    gg_id: str
    payload: dict[str, Any]


def parse_webhook(payload: dict[str, Any]) -> WebhookEvent:
    """
    Placeholder parser. Adapt to actual GoodGrants webhook format.
    """
    return WebhookEvent(
        event_type=str(payload.get("type", "")),
        gg_id=str(payload.get("id", "")),
        payload=payload,
    )

