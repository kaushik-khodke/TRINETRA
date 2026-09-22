"""
TRINETRA Phase 8 — Batch Scheduler
Schedules and orchestrates concurrency-controlled chunks of batch targets.
"""

from typing import List, Any
from .models import BatchTarget


class BatchScheduler:
    """
    Partitions batch targets into concurrency-bounded execution blocks.
    """

    def __init__(self, concurrency: int = 2):
        self.concurrency = max(1, concurrency)

    def chunk_targets(self, targets: List[BatchTarget]) -> List[List[BatchTarget]]:
        """
        Splits targets into groups of size self.concurrency.
        """
        chunks = []
        for i in range(0, len(targets), self.concurrency):
            chunks.append(targets[i : i + self.concurrency])
        return chunks
