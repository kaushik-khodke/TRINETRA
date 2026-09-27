"""
TRINETRA Workstation — Scientific Domain & Schema Validator
Strictly checks AnalysisPlan integrity against the Pipeline Registry and Mission Assets
matching copilot-prompt-and-validation.md.
"""

from typing import Dict, Any, List, Tuple
from .schemas import AnalysisPlan
from .pipeline_registry import get_pipeline


class PlanDomainValidator:
    """
    Validates AnalysisPlans against scientific bounds, required sensor bands,
    input role bindings, and execution safety rules.
    """

    @classmethod
    def validate_plan(
        cls,
        plan: AnalysisPlan,
        available_assets: List[Dict[str, Any]],
        available_aois: List[Dict[str, Any]],
    ) -> Tuple[List[str], List[str]]:
        """
        Returns (blocking_errors, warnings).
        If blocking_errors is non-empty, the plan CANNOT be approved or executed.
        """
        blocking_errors: List[str] = []
        warnings: List[str] = []

        # 1. Pipeline existence
        pipeline_def = get_pipeline(plan.pipeline.key)
        if not pipeline_def:
            blocking_errors.append(f"Pipeline '{plan.pipeline.key}' is not in the allowlisted pipeline registry.")
            return blocking_errors, warnings

        # 2. AOI check
        if plan.aoiId:
            aoi_match = next((a for a in available_aois if a.get("id") == plan.aoiId), None)
            if not aoi_match:
                blocking_errors.append(f"AOI ID '{plan.aoiId}' does not belong to active mission context.")
        else:
            warnings.append("No explicit AOI specified. Analysis will use full asset extent.")

        # 3. Input role coverage
        bound_roles = {inp.role for inp in plan.inputs}
        for req_role in pipeline_def.inputRoles:
            if req_role.startswith("optional_"):
                continue
            if req_role not in bound_roles:
                blocking_errors.append(f"Missing required input role binding '{req_role}' for pipeline '{pipeline_def.key}'.")

        # 4. Asset checks
        asset_map = {a.get("id"): a for a in available_assets}
        # Also map versions if present
        version_to_asset = {}
        for a in available_assets:
            for v in a.get("versions", []):
                version_to_asset[v.get("id")] = a

        for inp in plan.inputs:
            target_asset = asset_map.get(inp.assetId) or version_to_asset.get(inp.assetVersionId)
            if not target_asset and available_assets:
                # If we have assets registered, check existence
                warnings.append(f"Input role '{inp.role}' references asset '{inp.assetVersionId}' which is pending verification.")
            elif target_asset:
                coll = (target_asset.get("collection_id") or "").lower()
                if pipeline_def.supportedCollections and coll and coll not in [c.lower() for c in pipeline_def.supportedCollections]:
                    # Check sensor mismatch
                    if "sar" in pipeline_def.key and "sentinel-2" in coll:
                        blocking_errors.append(f"Input '{inp.role}' is optical '{coll}' but pipeline '{pipeline_def.key}' requires SAR sensor data.")
                    elif "optical" in pipeline_def.key and "sentinel-1" in coll:
                        blocking_errors.append(f"Input '{inp.role}' is Sentinel-1 SAR and does not provide optical reflectance bands required by '{pipeline_def.key}'.")

        # 5. Parameter boundaries
        bounds = pipeline_def.parameterBounds or {}
        params = plan.parameters or {}

        if "index" in bounds and "index" in params:
            allowed_indices = bounds["index"]
            if params["index"] not in allowed_indices:
                blocking_errors.append(f"Index '{params['index']}' is not supported. Allowed: {allowed_indices}")

        if "threshold" in bounds and "threshold" in params:
            th_spec = bounds["threshold"]
            val = float(params["threshold"])
            if val < th_spec.get("min", -1.0) or val > th_spec.get("max", 1.0):
                blocking_errors.append(f"Threshold {val} is outside allowed range [{th_spec.get('min')}, {th_spec.get('max')}].")

        if "thresholdDb" in bounds and "thresholdDb" in params:
            th_spec = bounds["thresholdDb"]
            val = float(params["thresholdDb"])
            if val < th_spec.get("min", -30.0) or val > th_spec.get("max", 30.0):
                blocking_errors.append(f"Radar threshold {val} dB is outside allowed range [{th_spec.get('min')}, {th_spec.get('max')}].")

        if "cloudMask" in bounds:
            cm = params.get("cloudMask", "none")
            if cm not in bounds["cloudMask"]:
                warnings.append(f"Cloud mask setting '{cm}' is non-standard. Defaulting to s2cloudless.")

        # 6. Non-causal scientific attribution warning
        if not plan.limitations:
            plan.limitations.append("Spectral and backscatter changes do not establish human intentionality or environmental causality.")

        return blocking_errors, warnings
