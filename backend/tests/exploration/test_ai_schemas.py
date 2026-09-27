"""
Test Suite: AI Schemas & Discriminated Command Contracts (Test Group A)
Verifies Pydantic strictness, discriminated unions, extra forbidden fields, and bounds.
"""

import pytest
from pydantic import ValidationError
from exploration.ai_schemas import (
    ExploreIntent,
    ExploreIntentType,
    FlyToCommand,
    ShowLayerCommand,
    HideLayerCommand,
    SetOpacityCommand,
    SearchDatasetsCommand,
    ExploreCommandPlan,
    MAX_AI_COMMANDS_PER_REQUEST,
)


def test_valid_explore_intent():
    intent = ExploreIntent(
        intent=ExploreIntentType.NAVIGATION,
        confidence=0.98,
        location_query="Nagpur",
        dataset_query=None,
        requested_layers=[],
        requested_actions=["fly_to"],
    )
    assert intent.intent == ExploreIntentType.NAVIGATION
    assert intent.location_query == "Nagpur"
    assert intent.confidence == 0.98


def test_invalid_explore_intent_confidence_bounds():
    with pytest.raises(ValidationError):
        ExploreIntent(
            intent=ExploreIntentType.NAVIGATION,
            confidence=1.5,  # Must be <= 1.0
        )


def test_valid_fly_to_command():
    cmd = FlyToCommand(
        location_query="Nagpur",
        latitude=21.1458,
        longitude=79.0882,
        zoom=10.5,
    )
    assert cmd.type == "FLY_TO"
    assert cmd.latitude == 21.1458
    assert cmd.longitude == 79.0882


def test_invalid_fly_to_coordinates():
    with pytest.raises(ValidationError):
        FlyToCommand(latitude=95.0, longitude=79.0)  # lat > 90

    with pytest.raises(ValidationError):
        FlyToCommand(latitude=20.0, longitude=200.0)  # lon > 180


def test_valid_set_opacity_command():
    cmd = SetOpacityCommand(layer_id="layer-borders", opacity=0.6)
    assert cmd.type == "SET_LAYER_OPACITY"
    assert cmd.opacity == 0.6


def test_invalid_opacity_bounds():
    with pytest.raises(ValidationError):
        SetOpacityCommand(layer_id="layer-borders", opacity=1.5)

    with pytest.raises(ValidationError):
        SetOpacityCommand(layer_id="layer-borders", opacity=-0.1)


def test_valid_command_plan():
    plan = ExploreCommandPlan(
        intent="navigation",
        summary="Fly to Nagpur and show Sentinel-2",
        commands=[
            FlyToCommand(location_query="Nagpur", latitude=21.1458, longitude=79.0882, zoom=10.0),
            ShowLayerCommand(layer_id="layer-local_sentinel2_nagpur_truecolor"),
        ],
    )
    assert len(plan.commands) == 2
    assert plan.commands[0].type == "FLY_TO"
    assert plan.commands[1].type == "SHOW_LAYER"


def test_command_plan_exceeds_max_commands():
    cmds = [ShowLayerCommand(layer_id=f"layer-{i}") for i in range(MAX_AI_COMMANDS_PER_REQUEST + 1)]
    with pytest.raises(ValidationError):
        ExploreCommandPlan(
            intent="overflow",
            summary="Flooding commands",
            commands=cmds,
        )


def test_forbid_extra_properties_injection():
    # Command injection attempt with arbitrary unauthorized fields
    with pytest.raises(ValidationError):
        FlyToCommand.model_validate({
            "type": "FLY_TO",
            "location_query": "Nagpur",
            "malicious_code": "alert(1);",
        })
