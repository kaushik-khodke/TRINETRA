"""
TRINETRA Phase 8 — Investigation Plan Validator
Validates investigation plan structure, step limits, parameter schemas, and DAG acyclicity.
"""

from typing import Dict, Any, List

try:
    from backend.config.settings import settings
except ImportError:
    from config.settings import settings

try:
    from backend.workspace.models import InvestigationPlan, PlanStepType
    from backend.workspace.planning.task_graph import TaskGraph, CycleDetectedError, InvalidDependencyError
except ImportError:
    from workspace.models import InvestigationPlan, PlanStepType
    from workspace.planning.task_graph import TaskGraph, CycleDetectedError, InvalidDependencyError


class PlanValidationError(Exception):
    """Raised when an investigation plan fails structural or constraint validation."""
    pass


class PlanValidator:
    """
    Validates investigation plan constraints, step quotas, parameter formats, and dependency trees.
    """

    @classmethod
    def validate_plan(cls, plan: InvestigationPlan) -> None:
        """
        Runs comprehensive validation on an investigation plan.
        Raises PlanValidationError or CycleDetectedError if validation fails.
        """
        if not plan.title or not plan.title.strip():
            raise PlanValidationError("Investigation plan must have a non-empty title.")

        if not plan.question or not plan.question.strip():
            raise PlanValidationError("Investigation plan must have a non-empty analytical question.")

        max_steps = getattr(settings, "workspace_max_plan_steps", 20)
        if len(plan.steps) > max_steps:
            raise PlanValidationError(
                f"Investigation plan exceeds maximum allowed steps: {len(plan.steps)} > {max_steps}"
            )

        # Unique step IDs
        seen_ids = set()
        for step in plan.steps:
            if not step.step_id or not step.step_id.strip():
                raise PlanValidationError("Investigation step ID cannot be empty.")
            if step.step_id in seen_ids:
                raise PlanValidationError(f"Duplicate step ID '{step.step_id}' found in plan.")
            seen_ids.add(step.step_id)

            # Step type check
            if not isinstance(step.type, PlanStepType):
                try:
                    PlanStepType(str(step.type))
                except ValueError:
                    raise PlanValidationError(f"Invalid step type '{step.type}' for step '{step.step_id}'.")

            # Parameters check
            if not isinstance(step.parameters, dict):
                raise PlanValidationError(f"Step '{step.step_id}' parameters must be a dictionary.")

        # DAG dependency validation and cycle detection
        if plan.steps:
            graph = TaskGraph(plan.steps)
            graph.detect_cycles()
