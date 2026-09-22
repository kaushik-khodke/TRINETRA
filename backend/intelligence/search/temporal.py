"""
TRINETRA Phase 7 — Temporal Search Operations
Time-range matching and epoch duration filtering.
"""

from datetime import datetime
from typing import Optional, Dict


class TemporalSearchFilter:
    """
    Evaluates temporal inclusion and duration over ISO-8601 timestamps.
    """

    @classmethod
    def matches_range(
        cls,
        item_timestamp: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> bool:
        if not item_timestamp:
            return True

        item_clean = item_timestamp.replace("Z", "+00:00")
        try:
            item_dt = datetime.fromisoformat(item_clean)
        except Exception:
            return True

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                if item_dt < start_dt:
                    return False
            except Exception:
                pass

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                if item_dt > end_dt:
                    return False
            except Exception:
                pass

        return True
