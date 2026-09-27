"""
TRINETRA / Shanetra Geospatial Exploration Engine
Unit & Integration Tests: AI Gateway Temporal Commands
Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
"""

import pytest
from exploration.ai_schemas import (
    ExploreCommandPlan,
    SetAOICommand,
    ClearAOICommand,
    SetDateRangeCommand,
    SelectObservationCommand,
    CompareObservationsCommand,
)
from exploration.command_validator import CommandValidator
from exploration.command_executor import CommandExecutor


def test_ai_command_set_aoi_valid():
    cmd = SetAOICommand(
        geometry={
            "type": "Polygon",
            "coordinates": [
                [
                    [79.0, 21.0],
                    [79.2, 21.0],
                    [79.2, 21.2],
                    [79.0, 21.2],
                    [79.0, 21.0],
                ]
            ],
        }
    )
    ok, err_code, err_msg = CommandValidator.validate_command(cmd)
    assert ok is True

    plan = ExploreCommandPlan(
        intent="aoi_selection",
        summary="Set AOI boundary over Nagpur region.",
        commands=[cmd],
    )
    status, items, patch, err = CommandExecutor.execute_plan(plan, current_active_layers=[])
    assert status == "completed"
    assert patch.aoi is not None
    assert patch.aoi["type"] == "Polygon"


def test_ai_command_clear_aoi():
    cmd = ClearAOICommand()
    ok, _, _ = CommandValidator.validate_command(cmd)
    assert ok is True

    plan = ExploreCommandPlan(
        intent="clear_aoi",
        summary="Clear active AOI.",
        commands=[cmd],
    )
    status, items, patch, _ = CommandExecutor.execute_plan(plan, current_active_layers=[])
    assert status == "completed"
    assert patch.aoi is None


def test_ai_command_set_date_range_valid_and_invalid():
    valid_cmd = SetDateRangeCommand(
        start_date="2026-01-01",
        end_date="2026-06-01",
    )
    ok, _, _ = CommandValidator.validate_command(valid_cmd)
    assert ok is True

    invalid_cmd = SetDateRangeCommand(
        start_date="2026-06-01",
        end_date="2026-01-01",
    )
    ok, err_code, err_msg = CommandValidator.validate_command(invalid_cmd)
    assert ok is False
    assert "cannot be after" in err_msg
