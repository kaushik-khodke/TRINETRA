"""
Test Suite: Command Validator & Policy Enforcement (Test Groups D, E, F, H, AC)
Verifies command injection defense, layer allowlists, AI permission boundaries, and limits.
"""

import pytest
from exploration.ai_schemas import (
    FlyToCommand,
    ShowLayerCommand,
    HideLayerCommand,
    SetOpacityCommand,
    ExploreCommandPlan,
    EXPLORE_COMMAND_REJECTED,
    EXPLORE_LAYER_NOT_ALLOWED,
)
from exploration.command_validator import CommandValidator


def test_validator_accepts_valid_plan():
    plan = ExploreCommandPlan(
        intent="navigation",
        summary="Fly to Nagpur",
        commands=[
            FlyToCommand(location_query="Nagpur"),
            ShowLayerCommand(layer_id="layer-local_sentinel2_nagpur_truecolor"),
        ],
    )
    is_valid, err_code, err_msg = CommandValidator.validate_plan(plan)
    assert is_valid is True
    assert err_code is None


def test_validator_rejects_unknown_command_injection():
    # Attempting to sneak an unauthorized action through a dictionary representation
    fake_cmd = {"type": "EXECUTE_JS", "code": "alert('hacked');"}
    is_valid, err_code, err_msg = CommandValidator.validate_command(fake_cmd)
    assert is_valid is False
    assert err_code == EXPLORE_COMMAND_REJECTED
    assert "EXECUTE_JS" in err_msg


def test_validator_rejects_load_url_injection():
    fake_cmd = {"type": "LOAD_URL", "url": "https://malicious-site.com/payload.js"}
    is_valid, err_code, err_msg = CommandValidator.validate_command(fake_cmd)
    assert is_valid is False
    assert err_code == EXPLORE_COMMAND_REJECTED


def test_validator_rejects_read_file_injection():
    fake_cmd = {"type": "READ_FILE", "path": "/etc/passwd"}
    is_valid, err_code, err_msg = CommandValidator.validate_command(fake_cmd)
    assert is_valid is False
    assert err_code == EXPLORE_COMMAND_REJECTED


def test_validator_rejects_unknown_layer():
    cmd = ShowLayerCommand(layer_id="layer-non-existent-12345")
    is_valid, err_code, err_msg = CommandValidator.validate_command(cmd)
    assert is_valid is False
    assert err_code == EXPLORE_LAYER_NOT_ALLOWED
    assert "does not exist" in err_msg


def test_validator_rejects_non_ai_controllable_layer():
    # Base dark layer has ai_controllable=False in the registry
    cmd = ShowLayerCommand(layer_id="layer-base-dark")
    is_valid, err_code, err_msg = CommandValidator.validate_command(cmd)
    assert is_valid is False
    assert err_code == EXPLORE_LAYER_NOT_ALLOWED
    assert "restricted from AI automated control" in err_msg


def test_validator_rejects_out_of_bounds_opacity():
    fake_cmd = {"type": "SET_LAYER_OPACITY", "layer_id": "layer-local_sentinel2_nagpur_truecolor", "opacity": 1.5}
    is_valid, err_code, err_msg = CommandValidator.validate_command(fake_cmd)
    assert is_valid is False
    assert err_code == EXPLORE_COMMAND_REJECTED
    assert "out of bounds" in err_msg
