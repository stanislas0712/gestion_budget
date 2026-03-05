"""
Async tasks for Odoo pushes.

We keep Celery optional at first; this module can be imported safely even if Celery isn't wired yet.
"""

from __future__ import annotations


def enqueue_push_convention(convention_id: int) -> None:
    """
    Placeholder.
    Later: wrap with Celery task (.delay()) and add retry policy.
    """

    # Intentionally no-op for now.
    _ = convention_id

