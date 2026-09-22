"""
TRINETRA Phase 8 Tests — Investigation Planning Subsystem
Verifies DAG topological sorting, cycle detection, step limits, and plan execution.
"""

import pytest
from workspace.models import InvestigationPlan, InvestigationStep, PlanStepType, PlanStatus
from workspace.planning.task_graph import TaskGraph, CycleDetectedError, InvalidDependencyError
from workspace.planning.validator import PlanValidator, PlanValidationError
from workspace.planning.planner import InvestigationPlanner
from workspace.repository import WorkspaceRepository


@pytest.fixture
def repo():
    return WorkspaceRepository(":memory:")


@pytest.fixture
def planner(repo):
    return InvestigationPlanner(repository=repo)


def test_task_graph_linear_dependency():
    s1 = InvestigationStep("s1", PlanStepType.OBSERVATION_SEARCH)
    s2 = InvestigationStep("s2", PlanStepType.ANALYZE_BITEMPORAL, depends_on=["s1"])
    s3 = InvestigationStep("s3", PlanStepType.BUILD_REPORT, depends_on=["s2"])

    graph = TaskGraph([s1, s2, s3])
    sorted_steps = graph.topological_sort()
    assert [s.step_id for s in sorted_steps] == ["s1", "s2", "s3"]

    batches = graph.get_execution_batches()
    assert len(batches) == 3
    assert [s.step_id for s in batches[0]] == ["s1"]
    assert [s.step_id for s in batches[1]] == ["s2"]
    assert [s.step_id for s in batches[2]] == ["s3"]


def test_task_graph_branching_and_concurrency():
    s1 = InvestigationStep("s1", PlanStepType.OBSERVATION_SEARCH)
    s2a = InvestigationStep("s2a", PlanStepType.ANALYZE_BITEMPORAL, depends_on=["s1"])
    s2b = InvestigationStep("s2b", PlanStepType.ANALYZE_SAR_OPTICAL, depends_on=["s1"])
    s3 = InvestigationStep("s3", PlanStepType.BUILD_SYNTHESIS, depends_on=["s2a", "s2b"])

    graph = TaskGraph([s1, s2a, s2b, s3])
    batches = graph.get_execution_batches()

    assert len(batches) == 3
    assert [s.step_id for s in batches[0]] == ["s1"]
    batch_2_ids = {s.step_id for s in batches[1]}
    assert batch_2_ids == {"s2a", "s2b"}
    assert [s.step_id for s in batches[2]] == ["s3"]


def test_task_graph_cycle_detection():
    # Direct cycle: s1 -> s2 -> s1
    s1 = InvestigationStep("s1", PlanStepType.OBSERVATION_SEARCH, depends_on=["s2"])
    s2 = InvestigationStep("s2", PlanStepType.ANALYZE_BITEMPORAL, depends_on=["s1"])

    graph = TaskGraph([s1, s2])
    with pytest.raises(CycleDetectedError) as exc_info:
        graph.detect_cycles()
    assert "Cyclic dependency detected" in str(exc_info.value)


def test_task_graph_invalid_dependency_id():
    s1 = InvestigationStep("s1", PlanStepType.OBSERVATION_SEARCH, depends_on=["unknown-step"])
    with pytest.raises(InvalidDependencyError):
        TaskGraph([s1])


def test_plan_validator_step_limit():
    steps = [InvestigationStep(f"s-{i}", PlanStepType.OBSERVATION_SEARCH) for i in range(25)]
    plan = InvestigationPlan(
        plan_id="p-overlimit",
        workspace_id="ws-1",
        title="Excessive Steps Plan",
        question="How to overflow?",
        steps=steps,
    )
    with pytest.raises(PlanValidationError) as exc:
        PlanValidator.validate_plan(plan)
    assert "maximum allowed steps" in str(exc.value)


def test_planner_execute_plan_success(planner):
    s1 = InvestigationStep("step-fetch", PlanStepType.OBSERVATION_SEARCH)
    s2 = InvestigationStep("step-analyze", PlanStepType.ANALYZE_BITEMPORAL, depends_on=["step-fetch"])
    s3 = InvestigationStep("step-synth", PlanStepType.BUILD_SYNTHESIS, depends_on=["step-analyze"])

    plan = planner.create_plan(
        workspace_id="ws-plan-test",
        title="Glacier Mass Balance Investigation",
        question="What is the retreat velocity?",
        steps=[s1, s2, s3],
    )

    run = planner.execute_plan(plan.plan_id)
    assert run.status == PlanStatus.COMPLETED
    assert len(run.step_results) == 3
    assert run.step_results["step-fetch"]["status"] == "COMPLETED"
    assert run.step_results["step-analyze"]["status"] == "COMPLETED"
    assert run.step_results["step-synth"]["status"] == "COMPLETED"
