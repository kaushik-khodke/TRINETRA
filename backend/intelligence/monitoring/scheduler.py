"""
TRINETRA Phase 7 — Monitoring Scheduler & Resource Governor
Enforces limits on active monitors and manages execution cadences.
"""

from typing import List
from config.settings import settings
from intelligence.models import MonitorDefinition
from intelligence.repository import IntelligenceRepository


class MonitoringScheduler:
    """
    Governs monitoring resources and identifies due monitor definitions.
    """

    @classmethod
    def can_create_monitor(cls, repository: IntelligenceRepository) -> bool:
        monitors = repository.list_monitors()
        max_allowed = getattr(settings, "intelligence_max_monitors", 50)
        return len(monitors) < max_allowed

    @classmethod
    def get_due_monitors(cls, repository: IntelligenceRepository) -> List[MonitorDefinition]:
        return repository.list_monitors(enabled_only=True)
