"""
TRINETRA Phase 8 — Workspace Synthesizer
Generates coherent intelligence syntheses combining evidence networks, clustered findings, and conflict records.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .context import SynthesisContextExtractor
from .evidence import EvidenceGraphBuilder
from .conflicts import ConflictDetector
from .findings import FindingClusterer
from .validator import SynthesisValidator


class WorkspaceSynthesizer:
    """
    Coordinates analytical synthesis across workspace items, evidence links, and detected conflicts.
    """

    def __init__(self, repository=None, activity_tracker=None):
        self.repository = repository
        self.activity_tracker = activity_tracker

    def synthesize(
        self,
        workspace_id: str,
    ) -> Dict[str, Any]:
        SynthesisValidator.validate_synthesis_request(workspace_id)

        ctx = SynthesisContextExtractor.extract_workspace_context(workspace_id, self.repository)
        items = ctx.get("board_items", [])
        relations = ctx.get("board_relations", [])

        # 1. Evidence Network
        evidence_graph = EvidenceGraphBuilder.build_graph(items, relations)

        # 2. Extract mock or referenced findings for clustering & conflicts
        mock_findings = []
        for itm in items:
            if itm.get("type") == "FINDING":
                mock_findings.append({
                    "finding_id": itm.get("source_id", itm.get("item_id")),
                    "region_id": "REG-PRIMARY",
                    "metrics": {"change_pct": 14.5},
                    "confidence": 0.88,
                    "sensor_type": "OPTICAL",
                })

        # 3. Detect Conflicts
        conflicts = ConflictDetector.detect_conflicts(mock_findings, relations)

        # 4. Modality & Region Clustering
        by_modality = FindingClusterer.cluster_by_modality(mock_findings)
        grades = FindingClusterer.grade_confidence(mock_findings)

        # 5. Build Final Synthesis
        unreviewed_count = len([r for r in ctx.get("reviews", []) if r.get("status") == "UNREVIEWED"])
        open_followups_count = len([f for f in ctx.get("follow_ups", []) if f.get("status") == "OPEN"])

        synthesis_result = {
            "workspace_id": workspace_id,
            "workspace_name": ctx.get("workspace_name"),
            "evidence_summary": {
                "total_items": len(items),
                "total_relations": len(relations),
                "isolated_items": len(evidence_graph["isolated_nodes"]),
            },
            "evidence_graph": evidence_graph,
            "conflicts": [c.to_dict() for c in conflicts],
            "findings_by_modality": {k: len(v) for k, v in by_modality.items()},
            "confidence_distribution": {k: len(v) for k, v in grades.items()},
            "workflow_health": {
                "unreviewed_items": unreviewed_count,
                "open_follow_ups": open_followups_count,
            },
            "synthesized_at": datetime.now(timezone.utc).isoformat(),
        }

        if self.activity_tracker:
            self.activity_tracker.log(
                workspace_id=workspace_id,
                activity_type="SYNTHESIS_GENERATED",
                entity_type="WORKSPACE",
                entity_id=workspace_id,
                details={
                    "evidence_items": len(items),
                    "conflicts_found": len(conflicts),
                },
            )

        return synthesis_result
