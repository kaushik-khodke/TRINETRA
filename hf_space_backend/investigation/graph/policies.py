"""
TRINETRA Phase 6 — Investigation Policy & Governance Engine
Enforces compute budgets, concurrency caps, regional limits, and safety boundaries.
"""

import logging
from typing import Dict, Any, List, Tuple
from config.settings import settings
from investigation.errors import GovernanceFailureError

logger = logging.getLogger("trinetra.investigation.policies")


class InvestigationPolicyEngine:
    """
    Validates investigation plans and execution parameters against platform governance policies.
    """

    @classmethod
    def enforce_plan_policies(cls, plan: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """
        Validates planned specialists, runtime limits, and observation scope.
        Returns (warnings, errors).
        """
        errors: List[str] = []
        warnings: List[str] = []

        specialists = plan.get("planned_specialists", [])
        max_specialists = getattr(settings, "investigation_max_specialists", 4)
        if len(specialists) > max_specialists:
            warnings.append(
                f"Planned specialists ({len(specialists)}) exceeded limit ({max_specialists}). Truncated to {max_specialists}."
            )
            plan["planned_specialists"] = specialists[:max_specialists]

        est_runtime = plan.get("estimated_runtime_seconds", 0.0)
        max_runtime = float(getattr(settings, "investigation_max_runtime_seconds", 180.0))
        if est_runtime > max_runtime:
            warnings.append(
                f"Estimated runtime ({est_runtime}s) exceeds policy ceiling ({max_runtime}s); execution will be aggressively managed."
            )

        return warnings, errors

    @classmethod
    def enforce_region_policy(cls, region_count: int) -> int:
        """
        Caps detected regions to the configured platform limit to prevent combinatorial explosion.
        """
        max_regions = getattr(settings, "investigation_max_regions", 100)
        if region_count > max_regions:
            logger.warning("Extracted regions (%d) exceeded limit (%d); clamping to top %d.", region_count, max_regions, max_regions)
            return max_regions
        return region_count
