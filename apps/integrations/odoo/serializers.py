"""
Serialization layer: Django domain objects -> Odoo payloads.

Keep it explicit, versionable, and well-tested.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OdooConventionPayload:
    data: dict[str, Any]

