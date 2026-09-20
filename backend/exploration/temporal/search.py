"""
TRINETRA / Shanetra Geospatial Exploration Engine
Temporal Search Contracts & Requests
Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
Validated API request & response schemas for multi-temporal observation searches.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from exploration.temporal.normalizer import ObservationSummary


class TemporalSearchRequest(BaseModel):
    """Client request for searching Earth Observation acquisitions over an AOI and time interval."""
    aoi: Optional[Dict[str, Any]] = Field(None, description="GeoJSON Polygon or MultiPolygon AOI")
    start_datetime: str = Field(..., description="Start timestamp in ISO-8601 UTC (e.g. 2026-01-01T00:00:00Z)")
    end_datetime: str = Field(..., description="End timestamp in ISO-8601 UTC (e.g. 2026-09-20T23:59:59Z)")
    collections: List[str] = Field(default_factory=lambda: ["sentinel-2-l2a"], description="Target satellite collections")
    cloud_cover_max: Optional[float] = Field(None, ge=0.0, le=100.0, description="Max allowed cloud cover percentage")
    sort: Literal["datetime_desc", "datetime_asc", "cloud_asc"] = Field("datetime_desc", description="Sort order")
    limit: int = Field(25, ge=1, le=100, description="Max items returned in single query")

    @field_validator("end_datetime")
    @classmethod
    def validate_date_interval(cls, end_str: str, info) -> str:
        start_str = info.data.get("start_datetime")
        if start_str and end_str:
            try:
                # Clean Z suffix for fromisoformat if Python < 3.11
                s = start_str.replace("Z", "+00:00")
                e = end_str.replace("Z", "+00:00")
                dt_start = datetime.fromisoformat(s)
                dt_end = datetime.fromisoformat(e)
                if dt_start > dt_end:
                    raise ValueError(f"start_datetime ({start_str}) cannot be after end_datetime ({end_str}).")
                delta_days = (dt_end - dt_start).days
                if delta_days > 365:
                    raise ValueError(f"Temporal span ({delta_days} days) exceeds maximum allowed range of 365 days.")
            except ValueError as ve:
                raise ve
            except Exception as ex:
                raise ValueError(f"Invalid ISO-8601 date format: {ex}")
        return end_str


class TemporalSearchResponse(BaseModel):
    """Standardized response containing bounded observation summaries and query metadata."""
    request_id: str
    observations: List[ObservationSummary] = Field(default_factory=list)
    total: int = 0
    has_more: bool = False
    query: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0
    cache_hit: bool = False
