"""
TRINETRA Phase 8 — Synthesis Validator
Ensures synthesis payloads have consistent references and valid workspace bindings.
"""

from typing import Dict, Any


class SynthesisValidationError(Exception):
    """Raised when synthesis generation fails schema or reference integrity."""
    pass


class SynthesisValidator:
    """
    Validates synthesis inputs and claims.
    """

    @classmethod
    def validate_synthesis_request(cls, workspace_id: str) -> None:
        if not workspace_id or not workspace_id.strip():
            raise SynthesisValidationError("Workspace ID must not be empty.")
