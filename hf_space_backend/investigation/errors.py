"""
TRINETRA Phase 6 — Investigation Error Taxonomy
Structured error definitions for planning, governance, execution, fusion, and reasoning.
"""

from typing import Optional, Dict, Any


class InvestigationError(Exception):
    """Base exception for all Phase 6 investigation errors."""
    def __init__(self, message: str, code: str = "INVESTIGATION_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.code,
            "message": self.message,
            "details": self.details,
        }


class PlanningFailureError(InvestigationError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="PLANNING_FAILURE", details=details)


class GovernanceFailureError(InvestigationError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="GOVERNANCE_FAILURE", details=details)


class FusionFailureError(InvestigationError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="FUSION_FAILURE", details=details)


class SpecialistFailureError(InvestigationError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="SPECIALIST_FAILURE", details=details)


class ReasoningFailureError(InvestigationError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="REASONING_FAILURE", details=details)


class ResourceFailureError(InvestigationError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="RESOURCE_FAILURE", details=details)
