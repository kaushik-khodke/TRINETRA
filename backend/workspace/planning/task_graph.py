"""
TRINETRA Phase 8 — Task Graph & Directed Acyclic Graph (DAG) Engine
Manages investigation step dependencies, cycle detection, topological sorting, and execution stages.
"""

from typing import Dict, List, Set, Optional
from collections import defaultdict, deque

try:
    from backend.workspace.models import InvestigationStep, StepStatus
except ImportError:
    from workspace.models import InvestigationStep, StepStatus


class CycleDetectedError(Exception):
    """Raised when an investigation plan contains cyclic step dependencies."""
    pass


class InvalidDependencyError(Exception):
    """Raised when an investigation step depends on an unknown step ID."""
    pass


class TaskGraph:
    """
    Directed Acyclic Graph (DAG) validator and scheduler for investigation steps.
    """

    def __init__(self, steps: List[InvestigationStep]):
        self.steps = steps
        self.step_map: Dict[str, InvestigationStep] = {s.step_id: s for s in steps}
        self.adj_list: Dict[str, List[str]] = defaultdict(list)
        self.in_degree: Dict[str, int] = {s.step_id: 0 for s in steps}
        self._build_graph()

    def _build_graph(self) -> None:
        """
        Builds adjacency representation and validates that all dependency IDs exist.
        """
        for step in self.steps:
            for dep_id in step.depends_on:
                if dep_id not in self.step_map:
                    raise InvalidDependencyError(
                        f"Step '{step.step_id}' depends on unknown step '{dep_id}'"
                    )
                self.adj_list[dep_id].append(step.step_id)
                self.in_degree[step.step_id] += 1

    def detect_cycles(self) -> None:
        """
        Verifies that the graph is acyclic using Kahn's algorithm.
        Raises CycleDetectedError if a cycle is present.
        """
        in_deg = dict(self.in_degree)
        queue = deque([s_id for s_id, deg in in_deg.items() if deg == 0])
        visited_count = 0

        while queue:
            node = queue.popleft()
            visited_count += 1
            for neighbor in self.adj_list[node]:
                in_deg[neighbor] -= 1
                if in_deg[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count != len(self.steps):
            cycle_nodes = [s_id for s_id, deg in in_deg.items() if deg > 0]
            raise CycleDetectedError(
                f"Cyclic dependency detected in investigation plan involving steps: {cycle_nodes}"
            )

    def topological_sort(self) -> List[InvestigationStep]:
        """
        Returns a linearly ordered list of steps respecting all dependencies.
        Raises CycleDetectedError if the graph has a cycle.
        """
        self.detect_cycles()
        in_deg = dict(self.in_degree)
        queue = deque([s_id for s_id, deg in in_deg.items() if deg == 0])
        sorted_steps: List[InvestigationStep] = []

        while queue:
            node = queue.popleft()
            sorted_steps.append(self.step_map[node])
            for neighbor in self.adj_list[node]:
                in_deg[neighbor] -= 1
                if in_deg[neighbor] == 0:
                    queue.append(neighbor)

        return sorted_steps

    def get_execution_batches(self) -> List[List[InvestigationStep]]:
        """
        Groups steps into concurrent execution tiers/layers.
        Steps in layer N only depend on steps in layers < N.
        """
        self.detect_cycles()
        in_deg = dict(self.in_degree)
        current_layer = [s_id for s_id, deg in in_deg.items() if deg == 0]
        batches: List[List[InvestigationStep]] = []

        while current_layer:
            batches.append([self.step_map[s_id] for s_id in current_layer])
            next_layer = []
            for node in current_layer:
                for neighbor in self.adj_list[node]:
                    in_deg[neighbor] -= 1
                    if in_deg[neighbor] == 0:
                        next_layer.append(neighbor)
            current_layer = next_layer

        return batches

    def is_step_ready(self, step_id: str, completed_step_ids: Set[str]) -> bool:
        """
        Returns True if all dependencies for the specified step are completed.
        """
        step = self.step_map.get(step_id)
        if not step:
            return False
        return all(dep_id in completed_step_ids for dep_id in step.depends_on)
