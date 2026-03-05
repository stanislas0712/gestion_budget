"""
GoodGrants services (API calls, retries, pagination, etc.).

No Django model/business logic here; map raw payloads -> Project/Operator in apps.projects/services.py.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class GoodGrantsConfig:
    base_url: str
    token: str


def get_config() -> GoodGrantsConfig:
    return GoodGrantsConfig(
        base_url=os.environ.get("GOODGRANTS_API_BASE_URL", "").rstrip("/"),
        token=os.environ.get("GOODGRANTS_API_TOKEN", ""),
    )


class GoodGrantsOperatorSync:
    def __init__(self, config: GoodGrantsConfig | None = None) -> None:
        self.config = config or get_config()

    def _headers(self) -> dict[str, str]:
        if not self.config.token:
            return {}
        return {"Authorization": f"Bearer {self.config.token}"}

    def fetch_validated_applications(self) -> list[dict[str, Any]]:
        """
        Placeholder: implement API contract when endpoints are confirmed.
        """
        if not self.config.base_url:
            return []
        resp = requests.get(f"{self.config.base_url}/applications/validated", headers=self._headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else data.get("results", [])

