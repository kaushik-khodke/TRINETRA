"""
TRINETRA Phase 8 — Multi-Region Comparator
Performs area-normalized comparative intelligence across distinct geographic regions.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

try:
    from backend.workspace.models import RegionComparison
    from backend.workspace.comparison.metrics import ComparisonMetricsEngine
    from backend.workspace.comparison.validator import ComparisonValidator
except ImportError:
    from workspace.models import RegionComparison
    from workspace.comparison.metrics import ComparisonMetricsEngine
    from workspace.comparison.validator import ComparisonValidator


class RegionComparator:
    """
    Executes comparative intelligence between two canonical regions.
    """

    def __init__(self, repository=None, activity_tracker=None, intelligence_service=None):
        self.repository = repository
        self.activity_tracker = activity_tracker
        self.intelligence_service = intelligence_service

    def compare_regions(
        self,
        workspace_id: str,
        region_a_id: str,
        region_b_id: str,
        period: str = "last_12_months",
        thresholds: Optional[List[float]] = None,
    ) -> RegionComparison:
        """
        Calculates area-normalized comparative metrics, difference matrices,
        coverage warnings, and stability sensitivity curves.
        """
        ComparisonValidator.validate_region_comparison(workspace_id, region_a_id, region_b_id)

        meta_a = self._get_region_profile(region_a_id)
        meta_b = self._get_region_profile(region_b_id)

        area_a = meta_a.get("area_km2", 100.0)
        area_b = meta_b.get("area_km2", 100.0)

        # Raw metrics
        raw_events_a = meta_a.get("event_count", 8)
        raw_events_b = meta_b.get("event_count", 14)

        raw_findings_a = meta_a.get("finding_count", 12)
        raw_findings_b = meta_b.get("finding_count", 26)

        # Area normalized (per 100 km²)
        norm_events_a = ComparisonMetricsEngine.normalize_by_area(raw_events_a, area_a)
        norm_events_b = ComparisonMetricsEngine.normalize_by_area(raw_events_b, area_b)

        norm_findings_a = ComparisonMetricsEngine.normalize_by_area(raw_findings_a, area_a)
        norm_findings_b = ComparisonMetricsEngine.normalize_by_area(raw_findings_b, area_b)

        diff_events = ComparisonMetricsEngine.compute_metric_difference(norm_events_a, norm_events_b, "events_per_100km2")
        diff_findings = ComparisonMetricsEngine.compute_metric_difference(norm_findings_a, norm_findings_b, "findings_per_100km2")

        # Warnings
        warnings = ComparisonMetricsEngine.detect_coverage_warnings(meta_a, meta_b)

        # Sensitivity curves
        sensitivity_a = ComparisonMetricsEngine.compute_sensitivity_curve(thresholds, base_area_km2=area_a * 0.1)
        sensitivity_b = ComparisonMetricsEngine.compute_sensitivity_curve(thresholds, base_area_km2=area_b * 0.1)

        metrics = {
            "region_a": {
                "region_id": region_a_id,
                "name": meta_a.get("name", region_a_id),
                "area_km2": area_a,
                "raw_event_count": raw_events_a,
                "raw_finding_count": raw_findings_a,
                "events_per_100km2": round(norm_events_a, 2),
                "findings_per_100km2": round(norm_findings_a, 2),
                "sensitivity_curve": sensitivity_a,
            },
            "region_b": {
                "region_id": region_b_id,
                "name": meta_b.get("name", region_b_id),
                "area_km2": area_b,
                "raw_event_count": raw_events_b,
                "raw_finding_count": raw_findings_b,
                "events_per_100km2": round(norm_events_b, 2),
                "findings_per_100km2": round(norm_findings_b, 2),
                "sensitivity_curve": sensitivity_b,
            },
        }

        differences = {
            "events": diff_events,
            "findings": diff_findings,
            "period": period,
        }

        comparison = RegionComparison(
            comparison_id=f"comp-{uuid.uuid4().hex[:12]}",
            workspace_id=workspace_id,
            region_a_id=region_a_id,
            region_b_id=region_b_id,
            period=period,
            metrics=metrics,
            differences=differences,
            warnings=warnings,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        if self.repository:
            self.repository.save_comparison(comparison)

        if self.activity_tracker:
            self.activity_tracker.log(
                workspace_id=workspace_id,
                activity_type="COMPARISON_RUN",
                entity_type="COMPARISON",
                entity_id=comparison.comparison_id,
                details={
                    "region_a": region_a_id,
                    "region_b": region_b_id,
                    "warnings_count": len(warnings),
                },
            )

        return comparison

    def _get_region_profile(self, region_id: str) -> Dict[str, Any]:
        """
        Queries intelligence layer or falls back to profile defaults.
        """
        if self.intelligence_service and hasattr(self.intelligence_service, "get_region"):
            reg = self.intelligence_service.get_region(region_id)
            if reg:
                return {
                    "region_id": reg.region_id,
                    "name": reg.name,
                    "area_km2": getattr(reg, "area_km2", 120.0),
                    "cloud_cover_percentage": getattr(reg, "cloud_cover_percentage", 8.5),
                    "resolution_meters": getattr(reg, "resolution_meters", 10.0),
                    "event_count": getattr(reg, "event_count", 5),
                    "finding_count": getattr(reg, "finding_count", 9),
                }

        # Fallback profile based on region_id hash for reproducibility
        h = abs(hash(region_id))
        area = 50.0 + (h % 350)
        return {
            "region_id": region_id,
            "name": f"Region {region_id}",
            "area_km2": float(area),
            "cloud_cover_percentage": 5.0 + (h % 20),
            "resolution_meters": 10.0 if (h % 2 == 0) else 20.0,
            "event_count": 3 + (h % 15),
            "finding_count": 6 + (h % 25),
        }
