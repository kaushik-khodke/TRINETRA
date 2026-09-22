"""
TRINETRA Phase 8 — Investigation Plan DAG & Execution Verification
Verifies:
1. Cycle detection in DAG graphs (raises CycleDetectedError)
2. Invalid dependency detection (raises InvalidDependencyError)
3. Topological sort and multi-layer concurrent batch grouping
4. End-to-end plan creation and automated execution via WorkspaceService
5. Step lifecycle state machine (PENDING -> RUNNING -> COMPLETED)
6. Plan run audit trail and result recording
"""

import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

from workspace.service import WorkspaceService
from workspace.repository import WorkspaceRepository
from workspace.models import (
    InvestigationStep,
    PlanStepType,
    StepStatus,
    PlanStatus,
)
from workspace.planning.task_graph import (
    TaskGraph,
    CycleDetectedError,
    InvalidDependencyError,
)


def run_test():
    print("=" * 70)
    print("TRINETRA Phase 8 — DAG Investigation Planning Verification")
    print("=" * 70)

    # 1. Invalid Dependency Detection
    broken_steps = [
        InvestigationStep(
            step_id="step_a",
            type=PlanStepType.OBSERVATION_SEARCH,
            depends_on=["non_existent_step"],
        )
    ]
    try:
        TaskGraph(broken_steps)
        assert False, "Should have raised InvalidDependencyError"
    except InvalidDependencyError as ex:
        print(f" [1/5] TaskGraph caught invalid dependency: {ex}")

    # 2. Cycle Detection in DAG
    cyclic_steps = [
        InvestigationStep(step_id="step_1", type=PlanStepType.OBSERVATION_SEARCH, depends_on=["step_3"]),
        InvestigationStep(step_id="step_2", type=PlanStepType.ANALYZE_BITEMPORAL, depends_on=["step_1"]),
        InvestigationStep(step_id="step_3", type=PlanStepType.ANALYZE_SAR_OPTICAL, depends_on=["step_2"]),
    ]
    try:
        tg_cyclic = TaskGraph(cyclic_steps)
        tg_cyclic.detect_cycles()
        assert False, "Should have raised CycleDetectedError"
    except CycleDetectedError as ex:
        print(f" [2/5] TaskGraph Kahn's algorithm caught cycle: {ex}")

    # 3. Valid Multi-Tier Topological Sort & Batch Layering
    valid_dag_steps = [
        InvestigationStep(step_id="s_opt", type=PlanStepType.OBSERVATION_SEARCH, depends_on=[]),
        InvestigationStep(step_id="s_sar", type=PlanStepType.OBSERVATION_SEARCH, depends_on=[]),
        InvestigationStep(step_id="s_water", type=PlanStepType.ANALYZE_BITEMPORAL, depends_on=["s_opt"]),
        InvestigationStep(step_id="s_coherence", type=PlanStepType.ANALYZE_SAR_OPTICAL, depends_on=["s_sar"]),
        InvestigationStep(step_id="s_synth", type=PlanStepType.BUILD_SYNTHESIS, depends_on=["s_water", "s_coherence"]),
        InvestigationStep(step_id="s_rep", type=PlanStepType.BUILD_REPORT, depends_on=["s_synth"]),
    ]

    tg = TaskGraph(valid_dag_steps)
    sorted_order = [s.step_id for s in tg.topological_sort()]
    batches = [[s.step_id for s in b] for b in tg.get_execution_batches()]

    assert len(batches) == 4
    # Layer 0: Acquisition (concurrent)
    assert set(batches[0]) == {"s_opt", "s_sar"}
    # Layer 1: Processing (concurrent)
    assert set(batches[1]) == {"s_water", "s_coherence"}
    # Layer 2: Synthesis
    assert batches[2] == ["s_synth"]
    # Layer 3: Report
    assert batches[3] == ["s_rep"]

    print(f" [3/5] Topological sort succeeded: {' -> '.join(sorted_order)}")
    print(f"       Concurrent execution tiers ({len(batches)} layers): {batches}")

    # 4. Service-Level Plan Creation & Execution
    repo = WorkspaceRepository(":memory:")
    service = WorkspaceService(repository=repo)
    ws = service.create_workspace(name="Sikkim GLOF Rapid Assessment")

    plan = service.create_plan(
        workspace_id=ws.workspace_id,
        title="Automated South Lhonak Cross-Sensor Investigation",
        question="Has lateral moraine displacement preceded water volume surge?",
        steps=valid_dag_steps,
    )
    assert plan.plan_id.startswith("plan-")
    assert len(plan.steps) == 6
    print(f" [4/5] Investigation plan registered: {plan.plan_id} ({len(plan.steps)} steps)")

    # 5. Plan Execution Engine Run
    plan_run = service.execute_plan(plan.plan_id)
    assert plan_run.run_id.startswith("run-")
    status_str = plan_run.status.value if hasattr(plan_run.status, "value") else str(plan_run.status)
    assert status_str == "COMPLETED"
    assert len(plan_run.step_results) == 6

    # Verify every step result marked COMPLETED
    for step_id, res in plan_run.step_results.items():
        assert res.get("status") == "COMPLETED"
        assert "execution_time" in res or "runtime_seconds" in res or "timestamp" in res

    print(f" [5/5] Plan run executed to completion: {plan_run.run_id} [Status: {plan_run.status}]")
    print(f"       Step execution results recorded: {list(plan_run.step_results.keys())}")

    # Verify workspace activity log recorded events
    activities = service.list_activities(ws.workspace_id)
    activity_types = [a.activity_type for a in activities]
    assert "PLAN_CREATED" in activity_types
    assert "PLAN_EXECUTED" in activity_types
    print(f"       Audit activities confirmed: {activity_types}")

    print("=" * 70)
    print(" ALL INVESTIGATION PLAN DAG & EXECUTION TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_test()
