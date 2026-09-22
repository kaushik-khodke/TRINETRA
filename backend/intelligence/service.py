"""
TRINETRA Phase 7 — Central Intelligence Service
Coordinator for intelligence ingestion, hybrid search, similarity retrieval, anomalies, and templates.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from intelligence.models import (
    CanonicalRegion,
    EOEvent,
    PersistentFinding,
    PersistentEvidence,
    InvestigationTemplate,
    AnomalyRecord,
    Baseline,
)
from intelligence.schemas import (
    SearchRequest,
    SearchResponse,
    SimilarityResponse,
    SimilarEntityItem,
    RegionalSummaryResponse,
    HotspotResponse,
)
from intelligence.repository import IntelligenceRepository, intelligence_repo
from intelligence.events.builder import EventBuilder
from intelligence.search.executor import SearchExecutor
from intelligence.similarity.fingerprint import EOFingerprint
from intelligence.similarity.index import similarity_index, SimilarityIndex
from intelligence.anomalies.detector import AnomalyDetector
from intelligence.anomalies.statistical import StatisticalBaselineBuilder
from intelligence.regional.aggregator import RegionalAggregator
from intelligence.regional.hotspots import HotspotClusterer
from intelligence.monitoring.service import monitoring_service, MonitoringService
from intelligence.provenance import IntelligenceProvenance


class IntelligenceService:
    """
    Central controller uniting persistence, search, similarity, anomalies, and monitoring.
    """

    def __init__(
        self,
        repository: Optional[IntelligenceRepository] = None,
        sim_index: Optional[SimilarityIndex] = None,
        monitor_svc: Optional[MonitoringService] = None,
        repo: Optional[IntelligenceRepository] = None,
    ):
        self.repo = repo or repository or intelligence_repo
        self.similarity_index = sim_index or similarity_index
        self.monitoring = monitor_svc or monitoring_service
        self._seed_default_baselines_if_empty()

    def _seed_default_baselines_if_empty(self) -> None:
        """Ensures baseline distributions exist for change percentage and area metrics."""
        existing = self.repo.find_baseline("change_percentage", "general")
        if not existing:
            # Historical 2-year distribution (12 samples)
            hist_changes = [1.2, 2.1, 1.8, 2.5, 3.1, 1.9, 2.2, 2.8, 1.7, 2.0, 3.4, 2.3]
            base = StatisticalBaselineBuilder.build(
                metric_name="change_percentage",
                spatial_unit="general",
                values=hist_changes,
                temporal_window="730d",
            )
            if base:
                self.repo.save_baseline(base)

        existing_area = self.repo.find_baseline("change_area_ha", "general")
        if not existing_area:
            hist_areas = [2.1, 3.4, 1.8, 4.2, 2.9, 3.1, 2.5, 3.8, 2.0, 4.0, 3.2, 2.7]
            base_area = StatisticalBaselineBuilder.build(
                metric_name="change_area_ha",
                spatial_unit="general",
                values=hist_areas,
                temporal_window="730d",
            )
            if base_area:
                self.repo.save_baseline(base_area)

    # --- Ingestion Pipeline ---

    def ingest_finding(self, finding: PersistentFinding) -> EOEvent:
        """
        Post-analysis hook: persists finding, indexes fingerprint, updates event, and checks monitors.
        """
        # 1. Save finding with cryptographic fingerprint
        fp = IntelligenceProvenance.compute_finding_fingerprint(
            investigation_id=finding.investigation_id,
            semantic_class=finding.semantic_class,
            bounding_box=finding.bounding_box,
            metrics=finding.metrics,
        )
        self.repo.save_finding(finding, fingerprint=fp)

        # 2. Register in similarity index
        finding_fp = EOFingerprint.from_finding(finding)
        self.similarity_index.insert(finding.finding_id, finding_fp)

        # 3. Build or evolve canonical EOEvent
        event = EventBuilder.ingest_finding(finding, self.repo)
        event_fp = EOFingerprint.from_event(event)
        self.similarity_index.insert(event.event_id, event_fp)

        # 4. Spatially route to active monitors and trigger alerts if conditions met
        self.monitoring.evaluate_monitors_for_finding(finding, event)

        # 5. Check statistical anomaly against baseline
        change_pct = float(finding.metrics.get("change_percentage", 0.0))
        if change_pct > 0.0:
            baseline = self.repo.find_baseline("change_percentage", "general")
            if baseline:
                anom = AnomalyDetector.evaluate_metric(
                    metric_name="change_percentage",
                    observed_value=change_pct,
                    baseline=baseline,
                    region_id=event.canonical_region_id,
                    event_id=event.event_id,
                    finding_id=finding.finding_id,
                )
                if anom:
                    self.repo.save_anomaly(anom)

        return event

    def ingest_findings_batch(self, findings: List[PersistentFinding]) -> List[EOEvent]:
        events = []
        for f in findings:
            evt = self.ingest_finding(f)
            if evt not in events:
                events.append(evt)
        return events

    def ingest_findings(self, findings: List[PersistentFinding]) -> List[EOEvent]:
        return self.ingest_findings_batch(findings)


    # --- Search ---

    def search(self, request: SearchRequest) -> SearchResponse:
        return SearchExecutor.search(request, self.repo)

    # --- Similarity Retrieval ---

    def find_similar(
        self,
        entity_id: str,
        entity_type: str = "finding",
        limit: int = 10,
        threshold: float = 0.40,
    ) -> SimilarityResponse:
        target_fp: Optional[EOFingerprint] = None

        if entity_type == "finding":
            f = self.repo.get_finding(entity_id)
            if f:
                target_fp = EOFingerprint.from_finding(f)
        else:
            e = self.repo.get_event(entity_id)
            if e:
                target_fp = EOFingerprint.from_event(e)

        if not target_fp:
            return SimilarityResponse(source_id=entity_id, similar_items=[], evaluated_count=0)

        # Ensure target is present in index
        self.similarity_index.insert(entity_id, target_fp)

        raw_results = self.similarity_index.search(
            target_fingerprint=target_fp,
            top_k=limit,
            min_threshold=threshold,
        )

        items: List[SimilarEntityItem] = []
        for cand_id, score, level, factors in raw_results:
            # Resolve entity title and class
            if cand_id.startswith("evt_"):
                cand_e = self.repo.get_event(cand_id)
                cand_title = cand_e.title if cand_e else f"Event {cand_id[-4:]}"
                cand_class = cand_e.semantic_class if cand_e else "GENERAL_CHANGE"
                cand_type = "event"
            else:
                cand_f = self.repo.get_finding(cand_id)
                cand_title = cand_f.label if cand_f else f"Finding {cand_id[-4:]}"
                cand_class = cand_f.semantic_class if cand_f else "GENERAL_CHANGE"
                cand_type = "finding"

            items.append(
                SimilarEntityItem(
                    id=cand_id,
                    entity_type=cand_type,
                    title=cand_title,
                    similarity=score,
                    semantic_class=cand_class,
                    similarity_level=level,
                    match_factors=factors,
                )
            )

        return SimilarityResponse(
            source_id=entity_id,
            similar_items=items,
            evaluated_count=len(items),
        )

    # --- Regional Intelligence & Hotspots ---

    def get_regional_summary(self, region_id: str) -> Optional[Dict[str, Any]]:
        return RegionalAggregator.aggregate_region(region_id, self.repo)

    def list_hotspots(self, min_events: int = 2) -> List[Dict[str, Any]]:
        events = self.repo.list_events(limit=200)
        return HotspotClusterer.find_hotspots(events, min_events=min_events)

    # --- Anomalies ---

    def list_anomalies(
        self,
        status: Optional[str] = None,
        region_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[AnomalyRecord]:
        return self.repo.list_anomalies(status=status, region_id=region_id, limit=limit)

    # --- Investigation Templates & Execution ---

    def create_template(
        self,
        name: str,
        question: str,
        analysis_mode: str = "BI_TEMPORAL",
        required_evidence: Optional[List[str]] = None,
        time_configuration: Optional[Dict[str, Any]] = None,
        semantic_targets: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> InvestigationTemplate:
        tmpl_id = f"tmpl_{uuid.uuid4().hex[:8]}"
        tmpl = InvestigationTemplate(
            template_id=tmpl_id,
            name=name,
            question=question,
            analysis_mode=analysis_mode,
            required_evidence=required_evidence or ["change_map", "spectral_indices"],
            time_configuration=time_configuration or {},
            semantic_targets=semantic_targets or [],
            filters=filters or {},
        )
        self.repo.save_template(tmpl)
        return tmpl

    def run_template(
        self,
        template_id: str,
        observation_ids: List[str],
        aoi: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes an immutable investigation run using the stored template specification.
        """
        template = self.repo.get_template(template_id)
        if not template:
            raise ValueError(f"Investigation template '{template_id}' not found.")

        from investigation.schemas import InvestigationRequest
        from investigation.service import investigation_service

        req = InvestigationRequest(
            question=template.question,
            aoi=aoi,
            observation_ids=observation_ids,
            options={"template_id": template.template_id, "analysis_mode": template.analysis_mode},
        )

        inv = investigation_service.create_investigation(req)
        return {
            "template_id": template.template_id,
            "investigation_id": inv.investigation_id,
            "status": "QUEUED",
            "message": f"Launched reusable investigation run {inv.investigation_id} from template '{template.name}'.",
        }


# Global singleton instance
intelligence_service = IntelligenceService()
