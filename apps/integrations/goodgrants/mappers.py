"""
Mapping helpers for GoodGrants payloads.

These functions should be deterministic and pure when possible.
"""

from __future__ import annotations

from typing import Any


def extract_operator_name(payload: dict[str, Any]) -> str:
    return str(payload.get("operator", {}).get("name", "")).strip()


def extract_project_title(payload: dict[str, Any]) -> str:
    return str(payload.get("project", {}).get("title", "")).strip()

