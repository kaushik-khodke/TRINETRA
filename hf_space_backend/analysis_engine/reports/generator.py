"""
TRINETRA Analysis Engine — Report Generator
Compiles the comprehensive, structured TRINETRA analysis report.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from analysis_engine.schemas import (
    AnalysisResult,
    AnalysisFinding,
    AnalysisLimitation,
    AnalysisMode,
    ConfidenceLevel,
)
from analysis_engine.evidence.models import EvidencePack
from analysis_engine.reasoning.schemas import AnalysisNarrativeSchema
from analysis_engine.models import AnalysisArtifact


class ReportGenerator:
    @staticmethod
    def generate_result(
        run_id: str,
        request_id: str,
        mode: str,
        query: str,
        observation_ids: List[str],
        pack: EvidencePack,
        narrative: AnalysisNarrativeSchema,
        provenance_manifest: Dict[str, Any],
        artifacts: List[AnalysisArtifact],
        limitations: List[AnalysisLimitation],
        execution_time_seconds: float,
    ) -> AnalysisResult:
        """
        Assembles the authoritative AnalysisResult contract.
        """
        # Map narrative findings to AnalysisFinding schemas
        findings: List[AnalysisFinding] = []
        region_map = {r.id: r for r in pack.change_regions}

        for f in narrative.findings:
            area_m2 = None
            area_ha = None
            geom = None
            # If finding links to a change region, attach geometry and area
            for eid in f.evidence_ids:
                if eid in region_map:
                    reg = region_map[eid]
                    area_m2 = reg.area_m2
                    area_ha = reg.area_ha
                    geom = reg.geometry
                    break

            try:
                conf_level = ConfidenceLevel(f.confidence)
            except Exception:
                conf_level = ConfidenceLevel.MEDIUM

            findings.append(
                AnalysisFinding(
                    id=f.id,
                    title=f.title,
                    label=f.title,
                    statement=f.statement,
                    confidence=conf_level,
                    evidence_ids=f.evidence_ids,
                    area_m2=area_m2,
                    area_ha=area_ha,
                    geometry=geom,
                    limitation_ids=f.limitation_ids,
                )
            )

        artifacts_dict = [a.dict() for a in artifacts]

        visualizations = {
            "annotated_preview": next((a.relative_url for a in artifacts if a.artifact_type == "png"), None),
            "regions_geojson": next((a.relative_url for a in artifacts if a.artifact_type == "geojson"), None),
        }

        confidence_summary = {
            "overall": narrative.overall_confidence,
            "evidence_quality": pack.statistics.get("confidence_evaluation", {}).get("evidence_quality_score", 0.85),
            "model_confidence": pack.statistics.get("confidence_evaluation", {}).get("model_confidence", 0.88),
        }

        return AnalysisResult(
            run_id=run_id,
            request_id=request_id,
            status="completed",
            mode=AnalysisMode(mode),
            query=query,
            summary=narrative.executive_summary,
            observation_ids=observation_ids,
            evidence=pack.dict(),
            findings=findings,
            confidence=confidence_summary,
            limitations=limitations,
            provenance=provenance_manifest,
            visualizations=visualizations,
            artifacts=artifacts_dict,
            created_at=datetime.utcnow().isoformat(),
            completed_at=datetime.utcnow().isoformat(),
            execution_time_seconds=round(execution_time_seconds, 3),
        )
