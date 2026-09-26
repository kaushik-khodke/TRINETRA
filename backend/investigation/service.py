"""
TRINETRA Phase 6 — Investigation Orchestration Service
Manages investigation lifecycles, concurrency limits, execution graph invocation,
artifact generation, and analyst workspace state.
"""

import os
import time
import asyncio
import logging
import threading
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from config.settings import settings
from investigation.models import (
    Investigation,
    InvestigationStatus,
    InvestigationProgress,
    InvestigationProgressStage,
    InvestigationArtifact,
    AnalystNote,
)
from investigation.schemas import (
    InvestigationRequest,
    InvestigationResult,
    InvestigationValidationResponse,
)
from investigation.planner import InvestigationPlanner
from investigation.graph.workflow import investigation_graph
from investigation.notes import analyst_notes_store
from investigation.reports.findings import FindingsFormatter
from investigation.reports.evidence_cards import EvidenceCardFormatter
from investigation.reports.timeline import TimelineFormatter
from investigation.reports.investigator import InvestigationReportGenerator

logger = logging.getLogger("trinetra.investigation.service")


class InvestigationService:
    """
    Central orchestration service for Earth-Observation investigations.
    """

    def __init__(self):
        self._investigations: Dict[str, Investigation] = {}
        self._lock = threading.Lock()
        self._semaphore = asyncio.Semaphore(getattr(settings, "investigation_max_concurrent_jobs", 2))

    def create_investigation(self, request: InvestigationRequest) -> Investigation:
        """
        Registers and initializes an investigation job in QUEUED status.
        """
        inv = Investigation(
            question=request.question,
            aoi=request.aoi,
            observation_ids=request.observation_ids,
            temporal_scope=getattr(request, "temporal_scope", None) or getattr(request, "temporal_range", None) or {},
        )
        with self._lock:
            self._investigations[inv.investigation_id] = inv
        logger.info("Created investigation job %s: '%s'", inv.investigation_id, inv.question)
        return inv

    def get_investigation(self, investigation_id: str) -> Optional[Investigation]:
        with self._lock:
            return self._investigations.get(investigation_id)

    def list_investigations(self, limit: int = 50) -> List[Investigation]:
        with self._lock:
            sorted_invs = sorted(self._investigations.values(), key=lambda i: i.created_at, reverse=True)
            return sorted_invs[:limit]

    def cancel_investigation(self, investigation_id: str) -> bool:
        with self._lock:
            inv = self._investigations.get(investigation_id)
            if not inv:
                return False
            inv.cancel_requested = True
            if inv.status in [InvestigationStatus.QUEUED, InvestigationStatus.RUNNING]:
                inv.status = InvestigationStatus.CANCELLED
                inv.completed_at = datetime.utcnow().isoformat()
                inv.progress.current_stage = InvestigationProgressStage.CANCELLED
                inv.progress.message = "Investigation cancelled by analyst."
            logger.info("Investigation %s was marked as cancelled", investigation_id)
            return True

    def validate_request(self, request: InvestigationRequest) -> InvestigationValidationResponse:
        """Fast pre-flight check without queuing an execution job."""
        return InvestigationPlanner.validate(request)

    async def run_investigation(self, investigation_id: str) -> Optional[Investigation]:
        """
        Executes the investigation asynchronously through the LangGraph StateGraph.
        """
        inv = self.get_investigation(investigation_id)
        if not inv:
            logger.error("Investigation %s not found for execution", investigation_id)
            return None

        if inv.cancel_requested:
            return inv

        async with self._semaphore:
            inv.status = InvestigationStatus.RUNNING
            inv.started_at = datetime.utcnow().isoformat()
            inv.progress.current_stage = InvestigationProgressStage.PLANNING
            inv.progress.percent = 10
            inv.progress.message = "Analyzing question and selecting specialists..."

            try:
                # Prepare initial LangGraph state
                initial_state = {
                    "investigation_id": inv.investigation_id,
                    "question": inv.question,
                    "observation_ids": inv.observation_ids,
                    "aoi": inv.aoi,
                    "status": "QUEUED",
                    "warnings": [],
                    "errors": [],
                }

                inv.progress.current_stage = InvestigationProgressStage.SPECIALISTS
                inv.progress.percent = 30
                inv.progress.message = "Executing analytical specialists in parallel..."

                # Execute compiled LangGraph workflow in thread pool
                final_state = await asyncio.to_thread(investigation_graph.invoke, initial_state)

                if inv.cancel_requested:
                    inv.status = InvestigationStatus.CANCELLED
                    return inv

                inv.progress.current_stage = InvestigationProgressStage.FUSION
                inv.progress.percent = 60
                inv.progress.message = "Fusing multi-source evidence and resolving discrepancies..."

                inv.progress.current_stage = InvestigationProgressStage.SEMANTICS
                inv.progress.percent = 80
                inv.progress.message = "Formulating semantic event hypotheses and findings..."

                inv.progress.current_stage = InvestigationProgressStage.REASONING
                inv.progress.percent = 95
                inv.progress.message = "Synthesizing conclusion within non-causal attribution boundaries..."

                # Extract artifacts and save HTML report
                inv_dir = os.path.join(str(settings.investigation_artifacts_dir), inv.investigation_id)
                os.makedirs(inv_dir, exist_ok=True)

                html_content = InvestigationReportGenerator.generate_html_report(final_state)
                html_path = os.path.join(inv_dir, "investigation_report.html")
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)

                artifacts = [
                    InvestigationArtifact(
                        name="investigation_report.json",
                        artifact_type="report_json",
                        file_path=os.path.join(inv_dir, "investigation_report.json"),
                        mime_type="application/json",
                        download_url=f"/api/v1/explore/investigations/{inv.investigation_id}/artifacts/report_json",
                    ),
                    InvestigationArtifact(
                        name="investigation_report.html",
                        artifact_type="report_html",
                        file_path=html_path,
                        mime_type="text/html",
                        download_url=f"/api/v1/explore/investigations/{inv.investigation_id}/artifacts/report_html",
                    ),
                    InvestigationArtifact(
                        name="evidence.geojson",
                        artifact_type="evidence_geojson",
                        file_path=os.path.join(inv_dir, "evidence.geojson"),
                        mime_type="application/geo+json",
                        download_url=f"/api/v1/explore/investigations/{inv.investigation_id}/artifacts/evidence_geojson",
                    ),
                    InvestigationArtifact(
                        name="investigation_manifest.json",
                        artifact_type="manifest",
                        file_path=os.path.join(inv_dir, "investigation_manifest.json"),
                        mime_type="application/json",
                        download_url=f"/api/v1/explore/investigations/{inv.investigation_id}/artifacts/manifest",
                    ),
                ]

                inv.artifacts = artifacts
                inv.result_data = final_state
                inv.status = InvestigationStatus.COMPLETED
                inv.completed_at = datetime.utcnow().isoformat()
                inv.progress.current_stage = InvestigationProgressStage.COMPLETED
                inv.progress.percent = 100
                inv.progress.message = "Investigation concluded successfully."
                logger.info("Investigation %s completed successfully", inv.investigation_id)


            except Exception as e:
                logger.exception("Investigation %s failed during execution: %s", inv.investigation_id, e)
                inv.status = InvestigationStatus.FAILED
                inv.completed_at = datetime.utcnow().isoformat()
                inv.progress.current_stage = InvestigationProgressStage.FAILED
                inv.progress.message = f"Execution failed: {str(e)}"
                inv.error = {"code": "INVESTIGATION_EXECUTION_ERROR", "message": str(e)}

        return inv

    # -------------------------------------------------------------------------
    # Workspace Data Getters
    # -------------------------------------------------------------------------

    def get_evidence(self, investigation_id: str) -> List[Dict[str, Any]]:
        inv = self.get_investigation(investigation_id)
        if not inv or not inv.result_data:
            return []
        items = inv.result_data.get("evidence_items", [])
        relationships = inv.result_data.get("evidence_relationships", [])
        conflicts = inv.result_data.get("conflicts", [])
        return EvidenceCardFormatter.format_cards(items, relationships, conflicts)

    def get_findings(self, investigation_id: str) -> List[Dict[str, Any]]:
        inv = self.get_investigation(investigation_id)
        if not inv or not inv.result_data:
            return []
        findings = inv.result_data.get("findings", [])
        return FindingsFormatter.format_findings(findings)

    def get_timeline(self, investigation_id: str) -> List[Dict[str, Any]]:
        inv = self.get_investigation(investigation_id)
        if not inv or not inv.result_data:
            return []
        obs = inv.result_data.get("context", {}).metadata.get("resolved_observations", []) if hasattr(inv.result_data.get("context"), "metadata") else []
        findings = inv.result_data.get("findings", [])
        evidence_items = inv.result_data.get("evidence_items", [])
        return TimelineFormatter.format_timeline(obs, findings, evidence_items)

    def get_artifacts(self, investigation_id: str) -> List[InvestigationArtifact]:
        inv = self.get_investigation(investigation_id)
        if not inv:
            return []
        return inv.artifacts

    def add_note(self, note: AnalystNote) -> AnalystNote:
        return analyst_notes_store.add_note(note)

    def get_notes(self, investigation_id: str) -> List[AnalystNote]:
        return analyst_notes_store.get_notes(investigation_id)

    def delete_note(self, investigation_id: str, note_id: str) -> bool:
        return analyst_notes_store.delete_note(investigation_id, note_id)


# Global singleton instance
investigation_service = InvestigationService()
