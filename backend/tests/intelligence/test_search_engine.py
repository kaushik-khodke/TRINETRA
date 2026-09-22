"""
Unit tests for Persistent Intelligence Search Subsystem.
Tests query parsing, spatial/temporal filtering, keyword taxonomy matching, and ranked result execution.
"""

import pytest
from intelligence.repository import IntelligenceRepository
from intelligence.models import EOEvent, EventState, PersistentFinding
from intelligence.search.parser import SearchQueryParser
from intelligence.search.spatial import SpatialSearchFilter
from intelligence.search.temporal import TemporalSearchFilter
from intelligence.search.ranking import SearchRanker
from intelligence.search.executor import SearchExecutor
from intelligence.schemas import SearchRequest


@pytest.fixture
def populated_repo():
    repo = IntelligenceRepository(db_path=":memory:")

    # Add test events
    e1 = EOEvent(
        event_id="evt_srch_01",
        title="Nagpur Urban Settlement Extension",
        canonical_region_id="reg_nagpur",
        semantic_class="BUILT_UP_EXPANSION",
        state=EventState.PERSISTENT,
        confidence=0.92,
        bounding_box=[79.0, 21.1, 79.1, 21.2],
        metadata={"keywords": ["settlement", "urban", "built-up"]},
    )
    e2 = EOEvent(
        event_id="evt_srch_02",
        title="Forest Canopy Loss",
        canonical_region_id="reg_pench",
        semantic_class="VEGETATION_LOSS",
        state=EventState.OBSERVED,
        confidence=0.78,
        bounding_box=[79.2, 21.6, 79.4, 21.8],
        metadata={"keywords": ["canopy", "vegetation", "clearing"]},
    )
    repo.save_event(e1)
    repo.save_event(e2)

    # Add test findings
    f1 = PersistentFinding(
        finding_id="fnd_srch_01",
        investigation_id="inv_01",
        type="optical_change",
        label="Deforestation sector 4",
        bounding_box=[79.22, 21.62, 79.25, 21.65],
        confidence=0.85,
        semantic_class="VEGETATION_LOSS",
    )
    repo.save_finding(f1)
    return repo


def test_query_parser():
    parsed = SearchQueryParser.parse_query("Show all persistent built-up changes with confidence > 0.8")
    assert parsed.get("state") == "PERSISTENT"
    assert parsed.get("semantic_class") == "BUILT_UP_EXPANSION"

    parsed_veg = SearchQueryParser.parse_query("Show me all findings related to vegetation loss")
    assert parsed_veg.get("semantic_class") == "VEGETATION_LOSS"


def test_spatial_filter():
    box_query = [79.0, 21.0, 79.15, 21.25]
    item_box_in = [79.05, 21.12, 79.08, 21.15]
    item_box_out = [82.0, 25.0, 82.1, 25.1]

    assert SpatialSearchFilter.intersects_bbox(item_box_in, box_query) is True
    assert SpatialSearchFilter.intersects_bbox(item_box_out, box_query) is False


def test_search_executor(populated_repo):
    req = SearchRequest(
        query="persistent built-up changes",
        limit=10,
    )
    resp = SearchExecutor.search(req, populated_repo)
    assert resp.total >= 1
    assert len(resp.results) >= 1
    top_result = resp.results[0]
    assert top_result.id == "evt_srch_01"
    assert top_result.score > 0.5
    assert len(top_result.match_reasons) > 0


def test_search_filtering(populated_repo):
    req = SearchRequest(
        query="vegetation",
        semantic_class="VEGETATION_LOSS",
        limit=10,
    )
    resp = SearchExecutor.search(req, populated_repo)
    assert resp.total >= 1
    ids = [r.id for r in resp.results]
    assert "evt_srch_02" in ids or "fnd_srch_01" in ids
