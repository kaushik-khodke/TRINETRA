"""
Test Suite: Command Executor & State Patch Engine (Test Groups G, N, P, U)
Verifies sequential execution, idempotency, partial failure isolation, and patch generation.
"""

from exploration.ai_schemas import (
    ExploreCommandPlan,
    FlyToCommand,
    ShowLayerCommand,
    HideLayerCommand,
    SetOpacityCommand,
    CommandExecutionStatus,
    EXPLORE_LOCATION_AMBIGUOUS,
)
from exploration.command_executor import CommandExecutor


def test_executor_fly_to_resolution():
    plan = ExploreCommandPlan(
        intent="navigation",
        summary="Fly to Nagpur",
        commands=[FlyToCommand(location_query="Nagpur")],
    )

    status, items, patch, err = CommandExecutor.execute_plan(
        plan=plan,
        current_active_layers=["layer-base-dark"],
    )

    assert status == "completed"
    assert len(items) == 1
    assert items[0].status == CommandExecutionStatus.EXECUTED
    assert patch.camera is not None
    assert patch.camera["latitude"] == 21.1458
    assert patch.camera["longitude"] == 79.0882


def test_executor_idempotency_show_layer():
    plan = ExploreCommandPlan(
        intent="layer_control",
        summary="Show borders twice",
        commands=[
            ShowLayerCommand(layer_id="layer-borders"),
            ShowLayerCommand(layer_id="layer-borders"),
        ],
    )

    status, items, patch, err = CommandExecutor.execute_plan(
        plan=plan,
        current_active_layers=["layer-base-dark"],
    )

    assert status == "completed"
    assert items[0].status == CommandExecutionStatus.EXECUTED
    assert items[1].status == CommandExecutionStatus.NO_OP
    assert "already active" in items[1].message
    assert "layer-borders" in patch.visible_layer_ids
    # Ensure not duplicated in active list
    assert patch.visible_layer_ids.count("layer-borders") == 1


def test_executor_partial_failure_sequence():
    # Command 1: valid show borders
    # Command 2: invalid non-existent layer -> fails
    # Command 3: valid set opacity -> must be cancelled
    plan = ExploreCommandPlan(
        intent="layer_control",
        summary="Mixed validity plan",
        commands=[
            ShowLayerCommand(layer_id="layer-borders"),
            ShowLayerCommand(layer_id="layer-completely-invalid-xyz"),
            SetOpacityCommand(layer_id="layer-borders", opacity=0.5),
        ],
    )

    status, items, patch, err = CommandExecutor.execute_plan(
        plan=plan,
        current_active_layers=["layer-base-dark"],
    )

    assert status == "partial_failure"
    assert len(items) == 3
    assert items[0].status == CommandExecutionStatus.EXECUTED
    assert items[1].status == CommandExecutionStatus.FAILED
    assert items[2].status == CommandExecutionStatus.CANCELLED
    assert "Cancelled due to prior command failure" in items[2].message


def test_executor_ambiguous_location_halts_navigation():
    plan = ExploreCommandPlan(
        intent="navigation",
        summary="Fly to ambiguous Springfield",
        commands=[FlyToCommand(location_query="Springfield")],
    )

    status, items, patch, err = CommandExecutor.execute_plan(
        plan=plan,
        current_active_layers=["layer-base-dark"],
    )

    assert status == "error"
    assert items[0].status == CommandExecutionStatus.FAILED
    assert err == EXPLORE_LOCATION_AMBIGUOUS
    assert patch.camera is None
