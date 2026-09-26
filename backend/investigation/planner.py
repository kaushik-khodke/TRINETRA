"""
TRINETRA Phase 6 — Investigation Planner
Maps natural-language enquiries into controlled intents, evidence requirements, and execution plans.
"""

from typing import Dict, Any, List
from config.settings import settings
from investigation.schemas import InvestigationRequest, InvestigationValidationResponse
from investigation.errors import PlanningFailureError, GovernanceFailureError


INTENT_RULES: Dict[str, Dict[str, Any]] = {
    "BUILT_UP_CHANGE": {
        "keywords": ["built", "construction", "building", "urban", "development", "structure", "expansion"],
        "required": ["CHANGE", "SPATIAL", "GIS_STATISTIC"],
        "preferred": ["OBJECT", "SPECTRAL", "OPTICAL"],
        "specialists": ["change_detection", "grounding", "spectral_analysis", "gis_statistics"],
        "cost": "MEDIUM",
    },
    "VEGETATION_CHANGE": {
        "keywords": ["vegetation", "forest", "tree", "deforestation", "green", "canopy", "loss", "ndvi"],
        "required": ["CHANGE", "SPECTRAL", "SPATIAL"],
        "preferred": ["GIS_STATISTIC", "OPTICAL"],
        "specialists": ["change_detection", "spectral_analysis", "gis_statistics"],
        "cost": "LOW",
    },
    "WATER_CHANGE": {
        "keywords": ["water", "flood", "inundation", "lake", "reservoir", "river", "wetland", "drainage"],
        "required": ["CHANGE", "SPATIAL"],
        "preferred": ["SAR", "SPECTRAL", "OPTICAL"],
        "specialists": ["change_detection", "sar_analysis", "spectral_analysis", "gis_statistics"],
        "cost": "MEDIUM",
    },
    "AGRICULTURAL_CHANGE": {
        "keywords": ["crop", "agriculture", "farm", "field", "harvest", "planting"],
        "required": ["CHANGE", "SPECTRAL", "TEMPORAL"],
        "preferred": ["GIS_STATISTIC"],
        "specialists": ["change_detection", "spectral_analysis", "temporal_statistics"],
        "cost": "MEDIUM",
    },
    "MULTIMODAL_CHANGE": {
        "keywords": ["radar", "sar", "microwave", "optical and sar", "multimodal", "cross-modal"],
        "required": ["CHANGE", "SAR", "OPTICAL"],
        "preferred": ["SPECTRAL", "GIS_STATISTIC"],
        "specialists": ["change_detection", "sar_analysis", "optical_analysis", "gis_statistics"],
        "cost": "HIGH",
    },
    "OBJECT_INVESTIGATION": {
        "keywords": ["aircraft", "plane", "vessel", "ship", "vehicle", "track", "objects", "structures"],
        "required": ["OBJECT", "SPATIAL"],
        "preferred": ["TEMPORAL", "METADATA"],
        "specialists": ["grounding", "vqa", "object_tracking", "gis_statistics"],
        "cost": "MEDIUM",
    },
    "TEMPORAL_RECURRENCE": {
        "keywords": ["persistent", "recurring", "repeated", "trajectory", "history", "trend", "across dates"],
        "required": ["CHANGE", "TEMPORAL", "SPATIAL"],
        "preferred": ["SPECTRAL", "GIS_STATISTIC"],
        "specialists": ["change_detection", "temporal_statistics", "gis_statistics"],
        "cost": "MEDIUM",
    },
    "ANOMALOUS_CHANGE": {
        "keywords": ["unusual", "anomaly", "suspicious", "unexpected", "strange"],
        "required": ["CHANGE", "SPATIAL", "MODEL"],
        "preferred": ["SAR", "OPTICAL", "SPECTRAL"],
        "specialists": ["change_detection", "spectral_analysis", "sar_analysis", "gis_statistics"],
        "cost": "HIGH",
    },
    "SCENE_UNDERSTANDING": {
        "keywords": ["describe", "caption", "scene", "overview", "what is this"],
        "required": ["METADATA"],
        "preferred": ["OPTICAL"],
        "specialists": ["caption", "vqa"],
        "cost": "LOW",
    },
    "LOCATION_IDENTIFICATION": {
        "keywords": [
            "location", "where", "coordinate", "coordinates", "situated", "latitude", "longitude",
            "gps", "which area", "what area", "which place", "what place", "which city", "what city",
            "bounds of", "name of this", "identify area", "identify region",
        ],
        "required": ["SPATIAL", "METADATA"],
        "preferred": ["OPTICAL", "GIS_STATISTIC"],
        "specialists": ["gis_statistics"],
        "cost": "LOW",
    },
    "GENERAL_CHANGE": {
        "keywords": ["change", "what happened", "difference", "impact", "evolution"],
        "required": ["CHANGE", "SPATIAL", "GIS_STATISTIC"],
        "preferred": ["SPECTRAL", "OBJECT"],
        "specialists": ["change_detection", "gis_statistics", "spectral_analysis"],
        "cost": "MEDIUM",
    },
}


class InvestigationPlanner:
    """
    Translates user questions into typed intents, evidence requirements, and specialist DAGs.
    """

    @classmethod
    def plan(cls, request: InvestigationRequest) -> Dict[str, Any]:
        intent = cls._infer_intent(request.question)
        rule = INTENT_RULES[intent]

        specialists = list(rule["specialists"])
        # If user explicitly requested SAR or multiple modalities
        if "sar" in request.question.lower() and "sar_analysis" not in specialists:
            specialists.append("sar_analysis")

        # Compute governance check
        if len(specialists) > settings.investigation_max_specialists:
            specialists = specialists[:settings.investigation_max_specialists]

        cost = rule["cost"]
        if len(specialists) >= 4 or len(request.observation_ids) > 4:
            cost = "HIGH"

        return {
            "intent": intent,
            "required_evidence": rule["required"],
            "preferred_evidence": rule["preferred"],
            "planned_specialists": specialists,
            "estimated_cost": cost,
            "estimated_runtime_seconds": cls._estimate_runtime(specialists, request.observation_ids),
        }

    @classmethod
    def validate(cls, request: InvestigationRequest) -> InvestigationValidationResponse:
        errors: List[str] = []
        warnings: List[str] = []

        # Check question validity
        clean_q = request.question.strip()
        if len(clean_q) < 3:
            errors.append("Investigation query is too short.")

        # Reject pure temporal command queries that do not require investigation
        temporal_view_keywords = ["show me the latest image", "zoom in", "switch to 3d", "reset view", "fly to"]
        if any(clean_q.lower().startswith(kw) for kw in temporal_view_keywords):
            errors.append("Query appears to be a direct map command, not an investigation enquiry.")

        plan = cls.plan(request) if not errors else {
            "intent": "GENERAL_CHANGE",
            "estimated_cost": "LOW",
            "planned_specialists": [],
            "estimated_runtime_seconds": 1.0,
        }

        # Check observation requirements
        if len(request.observation_ids) < 1 and not request.aoi:
            warnings.append("No explicit observation or AOI provided; analysis will evaluate active scene defaults.")

        valid = len(errors) == 0

        return InvestigationValidationResponse(
            valid=valid,
            intent=plan["intent"],
            estimated_compute_cost=plan["estimated_cost"],
            planned_specialists=plan["planned_specialists"],
            estimated_runtime_seconds=plan["estimated_runtime_seconds"],
            warnings=warnings,
            errors=errors,
        )

    @classmethod
    def _infer_intent(cls, question: str) -> str:
        q_lower = question.lower()
        for intent_name, rule in INTENT_RULES.items():
            if intent_name == "GENERAL_CHANGE":
                continue
            if any(kw in q_lower for kw in rule["keywords"]):
                return intent_name
        return "GENERAL_CHANGE"

    @classmethod
    def _estimate_runtime(cls, specialists: List[str], observation_ids: List[str]) -> float:
        base = 2.0
        per_specialist = 1.2
        multiplier = max(1, len(observation_ids)) * 0.4
        total = base + (len(specialists) * per_specialist) + multiplier
        return round(min(total, settings.investigation_max_runtime_seconds), 1)
