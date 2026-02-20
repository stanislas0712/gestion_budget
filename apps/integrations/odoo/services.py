"""
Odoo operator sync + service layer.

Do not mix GoodGrants concerns here. This module should only know about Odoo.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class OdooConfig:
    base_url: str
    db: str
    username: str
    password: str


def get_config() -> OdooConfig:
    return OdooConfig(
        base_url=os.environ.get("ODOO_API_BASE_URL", "").rstrip("/"),
        db=os.environ.get("ODOO_API_DB", ""),
        username=os.environ.get("ODOO_API_USERNAME", ""),
        password=os.environ.get("ODOO_API_PASSWORD", ""),
    )


class OdooOperatorSync:
    """
    Placeholder operator sync service. Adapt to your chosen Odoo protocol:
    - JSON-RPC (common)
    - XML-RPC
    - Custom REST gateway
    """

    def __init__(self, config: OdooConfig | None = None) -> None:
        self.config = config or get_config()

    def ping(self) -> bool:
        if not self.config.base_url:
            return False
        resp = requests.get(f"{self.config.base_url}/health", timeout=10)
        return resp.status_code == 200

    def push_convention(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.config.base_url:
            raise RuntimeError("ODOO_API_BASE_URL manquant")
        resp = requests.post(f"{self.config.base_url}/conventions", json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()

