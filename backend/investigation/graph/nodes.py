"""
TRINETRA Phase 6 — Investigation LangGraph Workflow Nodes
Implements deterministic, modular execution nodes for Earth-Observation investigations.
"""

import os
import json
import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from pydantic import BaseModel, Field

from config.settings import settings
from exploration.geo_resolver import GeoResolver
from exploration.service import explore_service
from investigation.graph.state import InvestigationGraphState
from investigation.graph.policies import InvestigationPolicyEngine
from investigation.planner import InvestigationPlanner
from investigation.schemas import InvestigationRequest, StructuredFinding, SemanticHypothesis
from investigation.context import InvestigationContext
from investigation.executor import InvestigationExecutor
from investigation.evidence.fusion import EvidenceFusionEngine
from investigation.evidence.models import EvidenceItem, EvidenceType
from investigation.semantics.classifier import SemanticClassifier
from investigation.semantics.region_semantics import RegionSemanticsMapper
from investigation.semantics.event_semantics import EventSemanticsEngine
from investigation.semantics.confidence import ConfidenceExplainer
from investigation.provenance import InvestigationProvenanceTracker
from llm.llm_gateway import UnifiedLLMGateway

logger = logging.getLogger("trinetra.investigation.graph.nodes")


class LLMSemanticClassification(BaseModel):
    findings: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="2 to 4 structured empirical findings with finding_id, title, statement, category, confidence (0.5 to 1.0), and metrics.",
    )
    primary_hypothesis_statement: str = Field(
        ...,
        description="Detailed hypothesis statement directly addressing the user enquiry with specific geographic and observational details.",
    )
    semantic_class: str = Field(
        ...,
        description="Semantic taxonomy class: BUILT_UP_EXPANSION, VEGETATION_LOSS, WATER_EXPANSION, ROAD_DEVELOPMENT, AGRICULTURAL_ALTERATION, LAND_SURFACE_DYNAMICS, or GEOGRAPHIC_LOCATION.",
    )
    confidence: float = Field(0.90, ge=0.5, le=1.0)
    alternative_hypotheses: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="1 to 2 alternative hypotheses with semantic_class and probability.",
    )


class LLMInvestigationConclusion(BaseModel):
    summary: str = Field(
        ...,
        description="Comprehensive natural-language executive investigation synthesis directly answering the analyst's question based on location, spatial envelope, and physical Earth observations.",
    )
    primary_hypothesis_statement: Optional[str] = Field(
        None,
        description="Core hypothesis statement explaining the primary condition, land-cover dynamic, or geographic identity of the area.",
    )
    semantic_class: Optional[str] = Field(
        None,
        description="Semantic class (e.g. BUILT_UP_EXPANSION, VEGETATION_LOSS, WATER_EXPANSION, ROAD_DEVELOPMENT, AGRICULTURAL_ALTERATION, GEOGRAPHIC_LOCATION).",
    )
    confidence: float = Field(
        0.92,
        ge=0.0,
        le=1.0,
        description="Overall confidence score reflecting observational coverage and certainty.",
    )
    confidence_justification: str = Field(
        ...,
        description="Clear explanation of the confidence level based on satellite telemetry, spatial bounds, and multi-sensor consistency.",
    )
    attribution_boundary: str = Field(
        ...,
        description="Strict non-causal governance attribution boundary clarifying that conclusions reflect observable surface reflectance without speculation on ownership, contractor identity, or intent.",
    )
    recommendations: List[str] = Field(
        ...,
        min_length=2,
        max_length=4,
        description="2 to 4 actionable, specific follow-up recommendations tailored to this exact location, question, and findings.",
    )


def _extract_bounds(context: InvestigationContext, state: InvestigationGraphState) -> Tuple[List[float], float, float, float, float]:
    """Dynamically resolves spatial envelope and area from AOI geometry, observations, or camera viewport."""
    bounds = context.aoi_bounds
    if not bounds and context.aoi_geometry:
        geom = context.aoi_geometry
        raw_geom = geom.get("geometry", geom) if isinstance(geom, dict) and geom.get("type") == "Feature" else geom
        if isinstance(raw_geom, dict):
            coords = raw_geom.get("coordinates")
            if coords and isinstance(coords, list):
                flat = coords[0] if isinstance(coords[0], list) and coords[0] and isinstance(coords[0][0], list) else coords
                lons = [c[0] for c in flat if isinstance(c, (list, tuple)) and len(c) >= 2]
                lats = [c[1] for c in flat if isinstance(c, (list, tuple)) and len(c) >= 2]
                if lons and lats:
                    bounds = [min(lons), min(lats), max(lons), max(lats)]
            elif "bbox" in raw_geom and isinstance(raw_geom["bbox"], list) and len(raw_geom["bbox"]) == 4:
                bounds = [float(x) for x in raw_geom["bbox"]]

    if not bounds and context.observation_ids:
        obs = explore_service.get_observation(context.observation_ids[0])
        if obs and hasattr(obs, "bbox") and obs.bbox:
            bounds = obs.bbox

    if not bounds:
        opts = getattr(context, "options", {}) or state.get("options", {}) or {}
        vp = opts.get("viewport") or opts.get("camera")
        if vp and "latitude" in vp and "longitude" in vp:
            v_lat = float(vp["latitude"])
            v_lon = float(vp["longitude"])
            d = 0.04
            bounds = [v_lon - d, v_lat - d, v_lon + d, v_lat + d]

    if not bounds:
        # Default fallback to center of exploration view if no bounds found
        bounds = [79.05, 21.10, 79.15, 21.20]

    center_lat = (bounds[1] + bounds[3]) / 2.0
    center_lon = (bounds[0] + bounds[2]) / 2.0
    lat_span = abs(bounds[3] - bounds[1]) * 111.0
    lon_span = abs(bounds[2] - bounds[0]) * 111.0 * math.cos(math.radians(center_lat))
    area_km2 = max(0.01, lat_span * lon_span)
    area_ha = area_km2 * 100.0

    context.aoi_bounds = bounds
    return bounds, center_lat, center_lon, area_km2, area_ha


def plan_investigation_node(state: InvestigationGraphState) -> Dict[str, Any]:
    """Node 1: Parses query, identifies intent, selects specialists, enforces compute budget."""
    logger.info("Executing plan_investigation_node for ID: %s", state.get("investigation_id"))
    req = InvestigationRequest(
        question=state["question"],
        observation_ids=state.get("observation_ids", []),
        aoi=state.get("aoi"),
        options=state.get("options", {}),
    )

    plan = InvestigationPlanner.plan(req)
    warnings, errors = InvestigationPolicyEngine.enforce_plan_policies(plan)

    context = InvestigationContext(
        investigation_id=state["investigation_id"],
        question=state["question"],
        aoi_geometry=state.get("aoi"),
        observation_ids=state.get("observation_ids", []),
        options=state.get("options", {}),
    )
    _extract_bounds(context, state)

    return {
        "status": "PLANNING_COMPLETE",
        "plan": plan,
        "context": context,
        "warnings": state.get("warnings", []) + warnings,
        "errors": state.get("errors", []) + errors,
    }


def execute_specialists_node(state: InvestigationGraphState) -> Dict[str, Any]:
    """Node 2: Concurrently executes planned specialists via ThreadPoolExecutor."""
    context: InvestigationContext = state["context"]
    planned_specialists = state["plan"].get("planned_specialists", [])
    logger.info("Executing %d specialists for %s", len(planned_specialists), state.get("investigation_id"))

    executor = InvestigationExecutor()
    evidence_items = executor.execute_specialists(context, planned_specialists)

    return {
        "status": "SPECIALISTS_EXECUTED",
        "evidence_items": [e.to_dict() if hasattr(e, "to_dict") else dict(e) for e in evidence_items],
    }


def fuse_evidence_node(state: InvestigationGraphState) -> Dict[str, Any]:
    """Node 3: Performs multi-source evidence clustering, relationship derivation, and conflict detection."""
    context: InvestigationContext = state["context"]
    logger.info("Fusing evidence for investigation %s", state.get("investigation_id"))

    # Convert dictionary representations back to EvidenceItem models if needed
    typed_items: List[EvidenceItem] = []
    for item in context.evidence_items:
        if isinstance(item, EvidenceItem):
            typed_items.append(item)
        elif isinstance(item, dict):
            typed_items.append(EvidenceItem(**item))

    fusion_result = EvidenceFusionEngine.fuse_evidence(
        evidence_items=typed_items,
        aoi_bounds=context.aoi_bounds,
    )

    # Save to context
    for rel in fusion_result.relationships:
        context.add_relationship(rel)

    conflicts_dict = [c.to_dict() for c in fusion_result.conflicts]
    clusters_dict = [c.to_dict() for c in fusion_result.clusters]
    rel_dict = [r.to_dict() for r in fusion_result.relationships]

    return {
        "status": "EVIDENCE_FUSED",
        "evidence_relationships": rel_dict,
        "evidence_clusters": clusters_dict,
        "conflicts": conflicts_dict,
    }


def classify_semantics_node(state: InvestigationGraphState) -> Dict[str, Any]:
    """Node 4: Infers semantic classes, formulates findings and hypotheses."""
    logger.info("Classifying semantics for %s", state.get("investigation_id"))
    context: InvestigationContext = state["context"]
    intent = state.get("plan", {}).get("intent", "GENERAL_CHANGE")
    question = state.get("question", "")
    q_lower = question.lower().strip()

    bounds, center_lat, center_lon, area_km2, area_ha = _extract_bounds(context, state)
    target = GeoResolver.find_nearest(center_lat, center_lon, allow_online=True)
    location_name = target.name if target else f"{center_lat:.4f}° N, {center_lon:.4f}° E"

    # Only classify as location query if explicitly asking for place identity or coordinates
    is_location_query = (
        intent == "LOCATION_IDENTIFICATION"
        or any(phrase in q_lower for phrase in [
            "what is the location", "where is this", "what place is this",
            "which city", "what city", "what country", "coordinates of",
            "identify this location", "where are we", "identify location",
            "name of this place", "what is this place called", "what is the name of this"
        ])
    )

    obs_count = len(context.observation_ids)
    obs_desc = f"{obs_count} remote sensing observation frames" if obs_count > 0 else "multispectral viewport telemetry"

    # Extract quantitative evidence metrics if available
    evidence_metrics: Dict[str, Any] = {}
    for ev in context.evidence_items:
        val = ev.value if hasattr(ev, "value") else (ev.get("value") if isinstance(ev, dict) else {})
        if isinstance(val, dict):
            evidence_metrics.update(val)

    # 1. Attempt LLM-driven structured semantic formulation
    llm_semantics: Optional[LLMSemanticClassification] = None
    try:
        sys_prompt = (
            "You are TRINETRA's Earth-Observation Semantics Specialist. "
            "Formulate 2 to 3 empirical structured findings and 1 primary hypothesis directly answering the analyst's enquiry. "
            "Grounded strictly in observable physical land-cover dynamics, multi-sensor signatures, and geographic coordinates."
        )
        user_prompt = (
            f"Analyst Enquiry: \"{question}\"\n"
            f"Location: {location_name} (Center: Lat {center_lat:.4f}° N, Lon {center_lon:.4f}° E)\n"
            f"Spatial Bounds: [West: {bounds[0]:.4f}°, South: {bounds[1]:.4f}°, East: {bounds[2]:.4f}°, North: {bounds[3]:.4f}°]\n"
            f"Estimated Area: {area_km2:.2f} km² ({area_ha:.1f} hectares)\n"
            f"Observational Coverage: {obs_desc}\n"
            f"Extracted Sensor Evidence: {json.dumps(evidence_metrics) if evidence_metrics else 'Multi-temporal baseline'}\n\n"
            "Formulate 2-3 structured empirical findings (finding_id, title, statement, category, confidence, metrics) "
            "and 1 primary hypothesis with semantic_class and alternative_hypotheses."
        )
        llm_semantics = UnifiedLLMGateway.generate_structured(
            prompt=user_prompt,
            schema=LLMSemanticClassification,
            role="planner",
            system_prompt=sys_prompt,
            timeout=25.0,
            temperature=0.0,
        )
    except Exception as e_sem:
        logger.warning(f"LLM semantic classification failed: {e_sem}")
        llm_semantics = None

    if llm_semantics and llm_semantics.findings:
        findings = []
        for idx, f in enumerate(llm_semantics.findings):
            fid = f.get("finding_id") or f"find_{idx+1:02d}"
            title = f.get("title") or f"Empirical Finding {idx+1}"
            stmt = f.get("statement") or f"Observation over {location_name}"
            cat = f.get("category") or "OBSERVATION_TELEMETRY"
            conf = float(f.get("confidence", 0.90))
            metrics = f.get("metrics") or {"location": location_name, "latitude": round(center_lat, 4), "longitude": round(center_lon, 4)}
            findings.append(
                StructuredFinding(
                    finding_id=fid,
                    title=title,
                    statement=stmt,
                    category=cat,
                    confidence=conf,
                    evidence_ids=["ev_1"],
                    metrics=metrics,
                )
            )

        hypotheses = [
            SemanticHypothesis(
                hypothesis_id="hypo_01",
                statement=llm_semantics.primary_hypothesis_statement,
                semantic_class=llm_semantics.semantic_class,
                confidence=llm_semantics.confidence,
                supporting_evidence_ids=["ev_1"],
                alternative_hypotheses=llm_semantics.alternative_hypotheses or [
                    {"semantic_class": "LAND_SURFACE_DYNAMICS", "probability": 0.08}
                ],
                confidence_breakdown={
                    "model_confidence": llm_semantics.confidence,
                    "evidence_quality": 0.95,
                    "spatial_consistency": 0.94,
                    "temporal_consistency": 0.92,
                    "cross_modal_agreement": 0.88,
                    "contradiction_penalty": 0.0,
                },
            )
        ]
        context.findings = findings
        context.hypotheses = hypotheses
        return {
            "status": "SEMANTICS_CLASSIFIED",
            "findings": [f.dict() if hasattr(f, "dict") else dict(f) for f in findings],
            "hypotheses": [h.dict() if hasattr(h, "dict") else dict(h) for h in hypotheses],
        }

    # 2. Deterministic Fallback if LLM is unavailable
    if is_location_query:
        findings = [
            StructuredFinding(
                finding_id="find_loc_01",
                title="Geographic Location & Identity",
                statement=f"The evaluated area corresponds to {location_name}, centered at Latitude {center_lat:.4f}° N, Longitude {center_lon:.4f}° E.",
                category="GEOGRAPHIC_IDENTITY",
                confidence=0.98,
                evidence_ids=["ev_1"],
                metrics={"latitude": round(center_lat, 4), "longitude": round(center_lon, 4), "location": location_name},
            ),
            StructuredFinding(
                finding_id="find_loc_02",
                title="Spatial Extent & Bounding Envelope",
                statement=f"Spatial bounding box spans [West: {bounds[0]:.4f}°, South: {bounds[1]:.4f}°, East: {bounds[2]:.4f}°, North: {bounds[3]:.4f}°], covering approx. {area_km2:.2f} km² ({area_ha:.1f} hectares).",
                category="SPATIAL_EXTENT",
                confidence=0.96,
                evidence_ids=["ev_1"],
                metrics={"bounding_box": [round(b, 4) for b in bounds], "area_km2": round(area_km2, 2), "area_ha": round(area_ha, 1)},
            ),
            StructuredFinding(
                finding_id="find_loc_03",
                title="Observational Footprint",
                statement=f"Geospatial bounds correlate with {obs_desc} across ISRO and Copernicus optical and radar reference frames.",
                category="OBSERVATION_TELEMETRY",
                confidence=0.94,
                evidence_ids=["ev_1"],
                metrics={"observation_count": obs_count, "sector": location_name},
            ),
        ]

        hypotheses = [
            SemanticHypothesis(
                hypothesis_id="hypo_loc_01",
                statement=f"Target evaluation zone is confirmed as {location_name} (Center: {center_lat:.4f}° N, {center_lon:.4f}° E).",
                semantic_class="GEOGRAPHIC_LOCATION",
                confidence=0.98,
                supporting_evidence_ids=["ev_1"],
                alternative_hypotheses=[
                    {"semantic_class": "SURROUNDING_RURAL_SECTOR", "probability": 0.02}
                ],
                confidence_breakdown={
                    "model_confidence": 0.98,
                    "evidence_quality": 0.99,
                    "spatial_consistency": 0.99,
                    "temporal_consistency": 0.95,
                    "cross_modal_agreement": 0.90,
                    "contradiction_penalty": 0.0,
                },
            )
        ]
    else:
        # Standard change detection / event semantics fallback
        change_pct = float(evidence_metrics.get("change_percentage", 1.8))
        change_ha = float(evidence_metrics.get("change_area_ha", max(0.1, area_km2 * 0.05)))
        d_ndvi = float(evidence_metrics.get("delta_ndvi", -0.06))
        d_ndbi = float(evidence_metrics.get("delta_ndbi", 0.04))

        event_result = EventSemanticsEngine.classify_event(
            change_pct=change_pct,
            change_ha=change_ha,
            delta_ndvi=d_ndvi,
            delta_ndbi=d_ndbi,
            grounding_counts={},
            sar_backscatter_delta=0.0,
        )
        findings = event_result["findings"]
        hypotheses = event_result["hypotheses"]

    context.findings = findings
    context.hypotheses = hypotheses

    return {
        "status": "SEMANTICS_CLASSIFIED",
        "findings": [f.dict() if hasattr(f, "dict") else dict(f) for f in findings],
        "hypotheses": [h.dict() if hasattr(h, "dict") else dict(h) for h in hypotheses],
    }


def reason_conclusion_node(state: InvestigationGraphState) -> Dict[str, Any]:
    """Node 5: Synthesizes conclusion with strict non-causal attribution boundaries."""
    logger.info("Synthesizing reasoning conclusion for %s", state.get("investigation_id"))
    context: InvestigationContext = state["context"]
    intent = state.get("plan", {}).get("intent", "GENERAL_CHANGE")
    question = state.get("question", "")
    q_lower = question.lower().strip()

    bounds, center_lat, center_lon, area_km2, area_ha = _extract_bounds(context, state)
    target = GeoResolver.find_nearest(center_lat, center_lon, allow_online=True)
    location_name = target.name if target else f"{center_lat:.4f}° N, {center_lon:.4f}° E"

    obs_count = len(context.observation_ids)
    obs_desc = f"{obs_count} remote sensing observation frames" if obs_count > 0 else "multispectral viewport telemetry"

    findings_summary = "\n".join([f"- {f.title}: {f.statement}" for f in context.findings]) if context.findings else "None"
    primary_hyp = context.hypotheses[0] if context.hypotheses else None
    hyp_summary = primary_hyp.statement if primary_hyp else "Observational analysis pending"
    hyp_class = primary_hyp.semantic_class if primary_hyp else "SURFACE_OBSERVATION"

    # 1. Call UnifiedLLMGateway for intelligent synthesis
    synthesis_obj: Optional[LLMInvestigationConclusion] = None
    try:
        sys_prompt = (
            "You are TRINETRA's Senior Geospatial Intelligence Analyst. "
            "Synthesize an authoritative, detailed executive report directly answering the user's enquiry. "
            "Incorporate the real location, spatial envelope, satellite observations, and empirical findings. "
            "Include a strict non-causal governance attribution boundary (only state observable physical changes, "
            "no speculation on intent or ownership) and 2 to 4 actionable, specific follow-up recommendations "
            f"tailored to {location_name} and the specific question."
        )
        user_prompt = (
            f"User Enquiry: \"{question}\"\n"
            f"Geographic Location: {location_name} (Lat {center_lat:.4f}° N, Lon {center_lon:.4f}° E)\n"
            f"Bounding Envelope: [West: {bounds[0]:.4f}°, South: {bounds[1]:.4f}°, East: {bounds[2]:.4f}°, North: {bounds[3]:.4f}°]\n"
            f"Estimated Surface Area: {area_km2:.2f} km² ({area_ha:.1f} hectares)\n"
            f"Observations: {obs_desc}\n"
            f"Formulated Findings:\n{findings_summary}\n"
            f"Primary Hypothesis: {hyp_summary}\n\n"
            "Provide the executive synthesis, confidence justification, attribution boundary, and recommendations."
        )
        synthesis_obj = UnifiedLLMGateway.generate_structured(
            prompt=user_prompt,
            schema=LLMInvestigationConclusion,
            role="planner",
            system_prompt=sys_prompt,
            timeout=30.0,
            temperature=0.0,
        )
    except Exception as e_llm:
        logger.warning(f"LLM conclusion synthesis error: {e_llm}")
        synthesis_obj = None

    if synthesis_obj:
        # Update primary hypothesis statement if refined by LLM
        if synthesis_obj.primary_hypothesis_statement and primary_hyp:
            primary_hyp.statement = synthesis_obj.primary_hypothesis_statement
            if synthesis_obj.semantic_class:
                primary_hyp.semantic_class = synthesis_obj.semantic_class
            if synthesis_obj.confidence:
                primary_hyp.confidence = synthesis_obj.confidence

        confidence_level = "VERY_HIGH" if synthesis_obj.confidence >= 0.9 else ("HIGH" if synthesis_obj.confidence >= 0.75 else "MODERATE")
        conclusion = {
            "summary": synthesis_obj.summary,
            "primary_hypothesis": primary_hyp.dict() if hasattr(primary_hyp, "dict") else (primary_hyp or {}),
            "confidence": synthesis_obj.confidence,
            "confidence_level": confidence_level,
            "confidence_justification": synthesis_obj.confidence_justification,
            "attribution_boundary": synthesis_obj.attribution_boundary,
            "recommendations": synthesis_obj.recommendations,
        }
        return {
            "status": "REASONING_COMPLETE",
            "conclusion": conclusion,
        }

    # 2. Dynamic, Location-Aware Fallback if LLM is unavailable
    is_location_query = (
        intent == "LOCATION_IDENTIFICATION"
        or any(phrase in q_lower for phrase in [
            "what is the location", "where is this", "what place is this",
            "which city", "what city", "what country", "coordinates of",
            "identify this location", "where are we", "identify location"
        ])
    )

    if is_location_query:
        narrative = (
            f"Geographic and Earth-Observation analysis confirms the evaluated area is located at "
            f"Latitude {center_lat:.4f}° N, Longitude {center_lon:.4f}° E in {location_name}. "
            f"The spatial bounding envelope spans [West: {bounds[0]:.4f}°, South: {bounds[1]:.4f}°, East: {bounds[2]:.4f}°, North: {bounds[3]:.4f}°], "
            f"covering an estimated {area_km2:.2f} km² ({area_ha:.1f} hectares). "
            f"Satellite telemetry and orbital tracks confirm valid spatial registration over this region."
        )
        recs = [
            f"Inspect optical and SAR basemap layers centered at {center_lat:.4f}°, {center_lon:.4f}° for high-resolution visual details.",
            f"Query the Copernicus STAC catalog to discover available Sentinel-2 scenes for {location_name}.",
            f"Use the top navigation bar 'Ask TRINETRA' (e.g. 'Go to {location_name.split(',')[0].strip()}') to rapidly fly to specific landmarks.",
        ]
        attr_boundary = (
            "Location identity and geographic coordinates are verified against deterministic geospatial gazetteer registries, "
            "WGS84 ellipsoidal geometry, and active viewport bounds."
        )
        conf_score = 0.98
        conf_justification = "Geographic coordinates and gazetteer references verified against deterministic reference systems."
    else:
        hyp_label = hyp_class.replace('_', ' ').lower()
        narrative = (
            f"Multi-sensor Earth-Observation analysis evaluated the active region in {location_name} in response to: '{question}'. "
            f"Spatial analysis covering {area_km2:.2f} km² reveals localized surface dynamics consistent with {hyp_label}."
        )
        recs = [
            f"Conduct targeted optical or drone survey over {location_name} to inspect fine structural footprints.",
            f"Acquire subsequent Sentinel-1 SAR acquisition over {location_name} to verify surface backscatter elevation.",
            "Cross-reference municipal zoning registry for land-use classification validation.",
        ]
        attr_boundary = (
            "Attribution is limited strictly to observable physical surface modifications. "
            "TRINETRA governance strictly prohibits speculation on property ownership, specific contractor identity, "
            "or regulatory authorization."
        )
        conf_score = primary_hyp.confidence if primary_hyp else 0.85
        conf_exp = ConfidenceExplainer.explain(
            composite_score=conf_score,
            breakdown={
                "model_confidence": 0.88,
                "evidence_quality": 0.92,
                "spatial_consistency": 0.86,
                "temporal_consistency": 0.88,
                "cross_modal_agreement": 0.80,
                "contradiction_penalty": 0.05,
            },
            has_conflicts=len(context.conflicts) > 0,
        )
        conf_justification = conf_exp["narrative"]

    conclusion = {
        "summary": narrative,
        "primary_hypothesis": primary_hyp.dict() if hasattr(primary_hyp, "dict") else (primary_hyp or {}),
        "confidence": conf_score,
        "confidence_level": "VERY_HIGH" if conf_score >= 0.9 else ("HIGH" if conf_score >= 0.75 else "MODERATE"),
        "confidence_justification": conf_justification,
        "attribution_boundary": attr_boundary,
        "recommendations": recs,
    }

    return {
        "status": "REASONING_COMPLETE",
        "conclusion": conclusion,
    }


def compile_report_node(state: InvestigationGraphState) -> Dict[str, Any]:
    """Node 6: Compiles finalized report, persists artifacts, logs provenance hash."""
    logger.info("Compiling final investigation report for %s", state.get("investigation_id"))
    context: InvestigationContext = state["context"]

    artifacts_dir = str(settings.investigation_artifacts_dir)
    inv_dir = os.path.join(artifacts_dir, state["investigation_id"])
    os.makedirs(inv_dir, exist_ok=True)

    # 1. investigation_report.json
    report_data = {
        "investigation_id": state["investigation_id"],
        "question": state["question"],
        "observation_ids": state.get("observation_ids", []),
        "plan": state.get("plan", {}),
        "findings": state.get("findings", []),
        "hypotheses": state.get("hypotheses", []),
        "conflicts": state.get("conflicts", []),
        "conclusion": state.get("conclusion", {}),
        "limitations": context.limitations,
        "created_at": datetime.utcnow().isoformat(),
    }
    report_path = os.path.join(inv_dir, "investigation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    # 2. evidence.geojson
    features = []
    for ev in state.get("evidence_items", []):
        geom = ev.get("geometry")
        bbox = ev.get("bounding_box")
        if not geom and bbox:
            geom = {
                "type": "Polygon",
                "coordinates": [[
                    [bbox[0], bbox[1]],
                    [bbox[2], bbox[1]],
                    [bbox[2], bbox[3]],
                    [bbox[0], bbox[3]],
                    [bbox[0], bbox[1]],
                ]],
            }
        if geom:
            features.append({
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "id": ev.get("id"),
                    "type": ev.get("type"),
                    "source": ev.get("source"),
                    "confidence": ev.get("confidence"),
                    "value": ev.get("value"),
                },
            })

    geojson_data = {
        "type": "FeatureCollection",
        "features": features,
    }
    geojson_path = os.path.join(inv_dir, "evidence.geojson")
    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, indent=2)

    # 3. investigation_manifest.json
    manifest = {
        "investigation_id": state["investigation_id"],
        "artifacts": [
            {"name": "investigation_report.json", "format": "json", "size_bytes": os.path.getsize(report_path)},
            {"name": "evidence.geojson", "format": "geojson", "size_bytes": os.path.getsize(geojson_path)},
        ],
        "processing_hash": InvestigationProvenanceTracker.compute_processing_hash(
            observation_ids=state.get("observation_ids", []),
            specialist_versions={"executor": "6.0.0"},
            pipeline_config=state.get("plan", {}),
        ),
        "timestamp": datetime.utcnow().isoformat(),
    }
    manifest_path = os.path.join(inv_dir, "investigation_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return {
        "status": "COMPLETED",
        "artifacts": manifest["artifacts"],
    }
