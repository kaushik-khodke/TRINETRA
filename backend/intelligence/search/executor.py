"""
TRINETRA Phase 7 — Search Execution Engine
Integrates deterministic parser, spatial/temporal filtering, and multi-dimensional ranking.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from intelligence.schemas import SearchRequest, SearchResponse, SearchResultItem
from intelligence.repository import IntelligenceRepository
from intelligence.search.parser import SearchQueryParser
from intelligence.search.spatial import SpatialSearchFilter
from intelligence.search.temporal import TemporalSearchFilter
from intelligence.search.semantic import SemanticSearchMatcher
from intelligence.search.ranking import SearchRanker


class SearchExecutor:
    """
    Executes hybrid search across persistent EO events, findings, and regions.
    """

    @classmethod
    def search(
        cls,
        request: SearchRequest,
        repository: IntelligenceRepository,
    ) -> SearchResponse:
        now = datetime.utcnow().isoformat()

        # 1. Parse natural language constraints
        inferred = SearchQueryParser.parse_query(request.query)

        # 2. Merge explicit request overrides
        semantic_target = request.semantic_class or inferred.get("semantic_class")
        state_target = request.state or inferred.get("state")
        min_conf = request.min_confidence if request.min_confidence is not None else inferred.get("min_confidence")
        temporal_range = request.temporal_range or inferred.get("temporal_range")
        start_date = temporal_range.get("start_date") if temporal_range else None
        end_date = temporal_range.get("end_date") if temporal_range else None
        bbox_target = request.bounding_box

        # Extract bbox from AOI if provided
        if not bbox_target and request.aoi:
            geom = request.aoi
            if geom.get("type") == "Polygon" and geom.get("coordinates"):
                coords = geom["coordinates"][0]
                lons = [c[0] for c in coords]
                lats = [c[1] for c in coords]
                bbox_target = [min(lons), min(lats), max(lons), max(lats)]

        items: List[SearchResultItem] = []

        # 3. Search Events
        events = repository.list_events(limit=200)
        for event in events:
            # Semantic filter
            if semantic_target and not SemanticSearchMatcher.matches_semantic(event.semantic_class, semantic_target):
                continue

            # State filter
            if state_target and event.state.value != state_target:
                continue

            # Confidence filter
            if min_conf is not None and event.confidence < min_conf:
                continue

            # Spatial filter
            if bbox_target and not SpatialSearchFilter.intersects_bbox(event.bounding_box, bbox_target):
                continue

            # Temporal filter
            if not TemporalSearchFilter.matches_range(event.last_seen, start_date, end_date):
                continue

            score, reasons = SearchRanker.score_event(event, inferred, bbox_target)
            items.append(
                SearchResultItem(
                    type="event",
                    id=event.event_id,
                    title=event.title,
                    confidence=event.confidence,
                    semantic_class=event.semantic_class,
                    state=event.state.value,
                    match_reasons=reasons,
                    score=score,
                    first_seen=event.first_seen,
                    last_seen=event.last_seen,
                    bounding_box=event.bounding_box,
                    metrics={"version": event.version, "findings_count": len(event.supporting_findings)},
                )
            )

        # 4. Search Findings
        findings = repository.list_findings(limit=200)
        for finding in findings:
            if semantic_target and not SemanticSearchMatcher.matches_semantic(finding.semantic_class, semantic_target):
                continue

            if min_conf is not None and finding.confidence < min_conf:
                continue

            if bbox_target and not SpatialSearchFilter.intersects_bbox(finding.bounding_box, bbox_target):
                continue

            if not TemporalSearchFilter.matches_range(finding.created_at, start_date, end_date):
                continue

            score, reasons = SearchRanker.score_finding(finding, inferred, bbox_target)
            items.append(
                SearchResultItem(
                    type="finding",
                    id=finding.finding_id,
                    title=finding.label or f"Finding {finding.finding_id[-4:]}",
                    confidence=finding.confidence,
                    semantic_class=finding.semantic_class,
                    state=None,
                    match_reasons=reasons,
                    score=score,
                    first_seen=finding.created_at,
                    last_seen=finding.created_at,
                    bounding_box=finding.bounding_box,
                    metrics=finding.metrics,
                )
            )

        # Sort by relevance score descending
        items.sort(key=lambda x: x.score, reverse=True)

        total = len(items)
        page = max(1, request.page)
        limit = max(1, min(100, request.limit))
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_items = items[start_idx:end_idx]

        return SearchResponse(
            results=paginated_items,
            total=total,
            page=page,
            limit=limit,
            generated_at=now,
            data_as_of=now,
        )
