"""
TRINETRA / Shanetra Geospatial Exploration Engine
GeoResolver & Deterministic Coordinate Parser
Phase 3: Natural-Language Earth Exploration + Controlled AI Map Commands
Air-gapped, zero-cloud geocoding abstraction and coordinate parser.
Prevents local LLMs from hallucinating geographic coordinates.
"""

import re
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class GeographicTarget:
    """Standardized representation of a resolved Earth location."""
    name: str
    latitude: float
    longitude: float
    bbox: Optional[List[float]] = None  # [min_lon, min_lat, max_lon, max_lat]
    source: str = "offline_gazetteer"
    confidence: float = 1.0
    is_ambiguous: bool = False
    candidates: List[str] = field(default_factory=list)


# Regular expressions for direct coordinate syntax
COORD_COMMA_REGEX = re.compile(
    r"^\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*$"
)
COORD_KEYWORD_REGEX = re.compile(
    r"lat(?:itude)?[:\s]+([+-]?\d+(?:\.\d+)?)[,\s]+lon(?:gitude)?[:\s]+([+-]?\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


class DeterministicCoordinateParser:
    """Parses explicit geographic coordinates directly without LLM involvement."""

    @classmethod
    def parse(cls, text: str) -> Optional[GeographicTarget]:
        if not text or not isinstance(text, str):
            return None

        clean = text.strip()

        # 1. Comma separated coordinates: "21.1458, 79.0882"
        match_comma = COORD_COMMA_REGEX.match(clean)
        if match_comma:
            lat = float(match_comma.group(1))
            lon = float(match_comma.group(2))
            if cls.validate_bounds(lat, lon):
                return GeographicTarget(
                    name=f"{lat:.4f}, {lon:.4f}",
                    latitude=lat,
                    longitude=lon,
                    source="coordinate_parser",
                    confidence=1.0,
                )
            return None

        # 2. Keyword coordinates: "lat 21.1458 lon 79.0882"
        match_kw = COORD_KEYWORD_REGEX.search(clean)
        if match_kw:
            lat = float(match_kw.group(1))
            lon = float(match_kw.group(2))
            if cls.validate_bounds(lat, lon):
                return GeographicTarget(
                    name=f"{lat:.4f}, {lon:.4f}",
                    latitude=lat,
                    longitude=lon,
                    source="coordinate_parser",
                    confidence=1.0,
                )

        return None

    @staticmethod
    def validate_bounds(lat: float, lon: float) -> bool:
        """Validates that latitude and longitude conform to standard WGS84 ranges."""
        return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0


# Embedded offline high-precision gazetteer
OFFLINE_GAZETTEER: Dict[str, Dict[str, Any]] = {
    # Central India / Space Centers
    "nagpur": {
        "name": "Nagpur, Maharashtra, India",
        "lat": 21.1458,
        "lon": 79.0882,
        "bbox": [79.00, 21.05, 79.18, 21.23],
    },
    "mumbai": {
        "name": "Mumbai, Maharashtra, India",
        "lat": 19.0760,
        "lon": 72.8777,
        "bbox": [72.75, 18.89, 73.00, 19.28],
    },
    "new delhi": {
        "name": "New Delhi, Delhi, India",
        "lat": 28.6139,
        "lon": 77.2090,
        "bbox": [77.10, 28.50, 77.35, 28.75],
    },
    "delhi": {
        "name": "Delhi, India",
        "lat": 28.6139,
        "lon": 77.2090,
        "bbox": [77.10, 28.50, 77.35, 28.75],
    },
    # Landmark & Geopolitical Aliases
    "capital of india": {
        "name": "New Delhi (Capital of India)",
        "lat": 28.6139,
        "lon": 77.2090,
        "bbox": [77.10, 28.50, 77.35, 28.75],
    },
    "capital of bharat": {
        "name": "New Delhi (Capital of India)",
        "lat": 28.6139,
        "lon": 77.2090,
        "bbox": [77.10, 28.50, 77.35, 28.75],
    },
    "national capital": {
        "name": "New Delhi (National Capital Region)",
        "lat": 28.6139,
        "lon": 77.2090,
        "bbox": [77.10, 28.50, 77.35, 28.75],
    },
    "financial capital of india": {
        "name": "Mumbai (Financial Capital of India)",
        "lat": 19.0760,
        "lon": 72.8777,
        "bbox": [72.75, 18.89, 73.00, 19.28],
    },
    "space city of india": {
        "name": "Bengaluru (Space City / ISRO HQ)",
        "lat": 12.9716,
        "lon": 77.5946,
        "bbox": [77.45, 12.85, 77.75, 13.15],
    },
    "silicon valley of india": {
        "name": "Bengaluru (Silicon Valley of India)",
        "lat": 12.9716,
        "lon": 77.5946,
        "bbox": [77.45, 12.85, 77.75, 13.15],
    },
    "taj mahal": {
        "name": "Taj Mahal, Agra, India",
        "lat": 27.1751,
        "lon": 78.0421,
        "bbox": [78.02, 27.15, 78.06, 27.19],
    },
    "bengaluru": {
        "name": "Bengaluru, Karnataka, India",
        "lat": 12.9716,
        "lon": 77.5946,
        "bbox": [77.45, 12.85, 77.75, 13.15],
    },
    "bangalore": {
        "name": "Bengaluru, Karnataka, India",
        "lat": 12.9716,
        "lon": 77.5946,
        "bbox": [77.45, 12.85, 77.75, 13.15],
    },
    "hyderabad": {
        "name": "Hyderabad, Telangana, India",
        "lat": 17.3850,
        "lon": 78.4867,
        "bbox": [78.35, 17.25, 78.60, 17.55],
    },
    "chennai": {
        "name": "Chennai, Tamil Nadu, India",
        "lat": 13.0827,
        "lon": 80.2707,
        "bbox": [80.15, 12.95, 80.35, 13.20],
    },
    "kolkata": {
        "name": "Kolkata, West Bengal, India",
        "lat": 22.5726,
        "lon": 88.3639,
        "bbox": [88.25, 22.45, 88.45, 22.68],
    },
    "pune": {
        "name": "Pune, Maharashtra, India",
        "lat": 18.5204,
        "lon": 73.8567,
        "bbox": [73.75, 18.42, 73.98, 18.62],
    },
    "sriharikota": {
        "name": "Satish Dhawan Space Centre (SHAR), Sriharikota, Andhra Pradesh",
        "lat": 13.7199,
        "lon": 80.2305,
        "bbox": [80.18, 13.65, 80.28, 13.80],
    },
    "shadnagar": {
        "name": "NRSC Earth Station, Shadnagar, Telangana",
        "lat": 17.0683,
        "lon": 78.2045,
        "bbox": [78.15, 17.00, 78.25, 17.15],
    },
    "dehradun": {
        "name": "Indian Institute of Remote Sensing (IIRS), Dehradun, Uttarakhand",
        "lat": 30.3165,
        "lon": 78.0322,
        "bbox": [77.95, 30.25, 78.10, 30.40],
    },
    # Key international reference coordinates
    "tokyo": {
        "name": "Tokyo, Japan",
        "lat": 35.6762,
        "lon": 139.6503,
        "bbox": [139.50, 35.50, 139.85, 35.80],
    },
    "cairo": {
        "name": "Cairo, Egypt",
        "lat": 30.0444,
        "lon": 31.2357,
        "bbox": [31.15, 29.95, 31.35, 30.15],
    },
    "london": {
        "name": "London, United Kingdom",
        "lat": 51.5074,
        "lon": -0.1278,
        "bbox": [-0.30, 51.40, 0.05, 51.60],
    },
    "paris": {
        "name": "Paris, France",
        "lat": 48.8566,
        "lon": 2.3522,
        "bbox": [2.20, 48.75, 2.45, 48.95],
    },
    "new york": {
        "name": "New York, USA",
        "lat": 40.7128,
        "lon": -74.0060,
        "bbox": [-74.15, 40.60, -73.85, 40.85],
    },
}

# Explicit ambiguous locations for testing safe ambiguity handling
AMBIGUOUS_LOCATIONS: Dict[str, List[str]] = {
    "springfield": ["Springfield, Illinois, USA", "Springfield, Massachusetts, USA", "Springfield, Missouri, USA"],
    "aurora": ["Aurora, Colorado, USA", "Aurora, Illinois, USA", "Aurora, Ontario, Canada"],
    "victoria": ["Victoria, BC, Canada", "Victoria, Australia", "Victoria, Seychelles"],
}


class GeoResolver:
    """Offline geocoding resolver with bounded LRU memory cache."""

    _cache: OrderedDict[str, GeographicTarget] = OrderedDict()
    _MAX_CACHE_SIZE: int = 256

    @classmethod
    def resolve(cls, query: str) -> Optional[GeographicTarget]:
        """
        Resolves query to GeographicTarget.
        Returns target, or target with is_ambiguous=True, or None.
        """
        if not query or not isinstance(query, str):
            return None

        clean = query.strip()
        clean_lower = clean.lower()

        # Multi-clause / compound sentences are not single geographic location entities
        if any(conj in clean_lower for conj in [" and ", " then ", " but ", " with "]):
            return None

        # 1. Deterministic coordinate parser
        coord_target = DeterministicCoordinateParser.parse(clean)
        if coord_target:
            return coord_target

        # 2. Check LRU Cache
        if clean_lower in cls._cache:
            cls._cache.move_to_end(clean_lower)
            return cls._cache[clean_lower]

        # 3. Ambiguity check
        if clean_lower in AMBIGUOUS_LOCATIONS:
            target = GeographicTarget(
                name=clean,
                latitude=0.0,
                longitude=0.0,
                source="offline_gazetteer",
                confidence=0.0,
                is_ambiguous=True,
                candidates=AMBIGUOUS_LOCATIONS[clean_lower],
            )
            cls._set_cache(clean_lower, target)
            return target

        # 4. Gazetteer lookup
        clean_norm = re.sub(r"^(?:the|to|at|in)\s+", "", clean_lower).strip()
        lookup_key = clean_lower if clean_lower in OFFLINE_GAZETTEER else (clean_norm if clean_norm in OFFLINE_GAZETTEER else None)
        if lookup_key:
            entry = OFFLINE_GAZETTEER[lookup_key]
            target = GeographicTarget(
                name=entry["name"],
                latitude=entry["lat"],
                longitude=entry["lon"],
                bbox=entry.get("bbox"),
                source="offline_gazetteer",
                confidence=1.0,
                is_ambiguous=False,
            )
            cls._set_cache(clean_lower, target)
            return target

        # 5. Substring / prefix match in gazetteer
        for key, entry in OFFLINE_GAZETTEER.items():
            if key in clean_lower or clean_lower in key or (clean_norm and (key in clean_norm or clean_norm in key)):
                target = GeographicTarget(
                    name=entry["name"],
                    latitude=entry["lat"],
                    longitude=entry["lon"],
                    bbox=entry.get("bbox"),
                    source="offline_gazetteer",
                    confidence=0.9,
                    is_ambiguous=False,
                )
                cls._set_cache(clean_lower, target)
                return target

        return None

    @classmethod
    def _set_cache(cls, key: str, target: GeographicTarget) -> None:
        cls._cache[key] = target
        if len(cls._cache) > cls._MAX_CACHE_SIZE:
            cls._cache.popitem(last=False)
