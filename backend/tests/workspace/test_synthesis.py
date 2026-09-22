"""
TRINETRA Phase 8 Tests — Intelligence Synthesis Subsystem
Verifies evidence graph construction, conflict detection, finding clustering, and synthesis payloads.
"""

import pytest
from workspace.synthesis.evidence import EvidenceGraphBuilder
from workspace.synthesis.conflicts import ConflictDetector
from workspace.synthesis.findings import FindingClusterer
from workspace.synthesis.builder import WorkspaceSynthesizer
from workspace.repository import WorkspaceRepository
from workspace.models import EvidenceBoardItem, EvidenceBoardRelation


@pytest.fixture
def repo():
    return WorkspaceRepository(":memory:")


@pytest.fixture
def synthesizer(repo):
    return WorkspaceSynthesizer(repository=repo)


def test_evidence_graph_builder():
    items = [
        {"item_id": "i-1", "type": "OBSERVATION", "title": "Sentinel-2 2025-01"},
        {"item_id": "i-2", "type": "FINDING", "title": "Lake Expansion 15%"},
        {"item_id": "i-3", "type": "EVENT", "title": "Glacial Lake Outburst"},
        {"item_id": "i-4", "type": "NOTE", "title": "Analyst note on cloud gap"},
    ]
    relations = [
        {"relation_id": "r-1", "source_item_id": "i-1", "target_item_id": "i-2", "relation_type": "supports"},
        {"relation_id": "r-2", "source_item_id": "i-2", "target_item_id": "i-3", "relation_type": "supports"},
    ]

    graph = EvidenceGraphBuilder.build_graph(items, relations)
    assert graph["node_count"] == 4
    assert graph["edge_count"] == 2
    # i-4 is isolated
    assert "i-4" in graph["isolated_nodes"]
    # i-2 has degree 2
    node_i2 = next(n for n in graph["nodes"] if n["item_id"] == "i-2")
    assert node_i2["degree"] == 2


def test_conflict_detector_trend_opposition():
    findings = [
        {"finding_id": "f-1", "region_id": "reg-basin", "metrics": {"change_pct": 28.5}},
        {"finding_id": "f-2", "region_id": "reg-basin", "metrics": {"change_pct": -22.0}},
    ]

    conflicts = ConflictDetector.detect_conflicts(findings)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "TREND_OPPOSITION"
    assert conflicts[0].severity == "HIGH"


def test_conflict_detector_explicit_contradiction_relation():
    relations = [
        {
            "relation_id": "rel-contra",
            "source_item_id": "item-optical",
            "target_item_id": "item-sar",
            "relation_type": "contradicts",
            "metadata": {"reason": "SAR backscatter does not confirm flood boundary"},
        }
    ]

    conflicts = ConflictDetector.detect_conflicts(findings=[], relations=relations)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "ANALYST_DECLARED_CONTRADICTION"


def test_workspace_synthesizer_flow(repo, synthesizer):
    ws_id = "ws-synth-test"
    repo.save_board_item(EvidenceBoardItem("item-1", ws_id, "FINDING", "f-1", title="Finding 1"))
    repo.save_board_item(EvidenceBoardItem("item-2", ws_id, "EVENT", "e-1", title="Event 1"))
    repo.save_board_relation(EvidenceBoardRelation("rel-1", ws_id, "item-1", "item-2", "supports"))

    res = synthesizer.synthesize(ws_id)
    assert res["workspace_id"] == ws_id
    assert res["evidence_summary"]["total_items"] == 2
    assert res["evidence_summary"]["total_relations"] == 1
    assert "findings_by_modality" in res
    assert "workflow_health" in res
