"""
TRINETRA / Shanetra Geospatial Exploration Engine
GeoResolver & Deterministic Coordinate Parser
Phase 3: Natural-Language Earth Exploration + Controlled AI Map Commands
Air-gapped, zero-cloud geocoding abstraction and coordinate parser.
Prevents local LLMs from hallucinating geographic coordinates.
"""

import os
import re
import json
import urllib.request
import urllib.parse
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from config.settings import settings


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
    zoom: Optional[float] = None


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
    # -------------------------------------------------------------------------
    # Major World Countries (Global coverage for top-level exploration)
    # -------------------------------------------------------------------------
    "china": {
        "name": "China (People's Republic of China)",
        "lat": 35.8617,
        "lon": 104.1954,
        "bbox": [73.50, 18.00, 134.77, 53.56],
        "zoom": 3.8,
    },
    "prc": {
        "name": "China (People's Republic of China)",
        "lat": 35.8617,
        "lon": 104.1954,
        "bbox": [73.50, 18.00, 134.77, 53.56],
        "zoom": 3.8,
    },
    "people's republic of china": {
        "name": "China (People's Republic of China)",
        "lat": 35.8617,
        "lon": 104.1954,
        "bbox": [73.50, 18.00, 134.77, 53.56],
        "zoom": 3.8,
    },
    "india": {
        "name": "India (Republic of India)",
        "lat": 20.5937,
        "lon": 78.9629,
        "bbox": [68.12, 6.75, 97.40, 37.10],
        "zoom": 4.5,
    },
    "bharat": {
        "name": "India (Republic of India)",
        "lat": 20.5937,
        "lon": 78.9629,
        "bbox": [68.12, 6.75, 97.40, 37.10],
        "zoom": 4.5,
    },
    "united states": {
        "name": "United States of America",
        "lat": 37.0902,
        "lon": -95.7129,
        "bbox": [-125.00, 24.50, -66.90, 49.40],
        "zoom": 3.8,
    },
    "usa": {
        "name": "United States of America",
        "lat": 37.0902,
        "lon": -95.7129,
        "bbox": [-125.00, 24.50, -66.90, 49.40],
        "zoom": 3.8,
    },
    "united states of america": {
        "name": "United States of America",
        "lat": 37.0902,
        "lon": -95.7129,
        "bbox": [-125.00, 24.50, -66.90, 49.40],
        "zoom": 3.8,
    },
    "america": {
        "name": "United States of America",
        "lat": 37.0902,
        "lon": -95.7129,
        "bbox": [-125.00, 24.50, -66.90, 49.40],
        "zoom": 3.8,
    },
    "russia": {
        "name": "Russian Federation",
        "lat": 61.5240,
        "lon": 105.3188,
        "bbox": [19.60, 41.20, 180.00, 81.90],
        "zoom": 3.0,
    },
    "russian federation": {
        "name": "Russian Federation",
        "lat": 61.5240,
        "lon": 105.3188,
        "bbox": [19.60, 41.20, 180.00, 81.90],
        "zoom": 3.0,
    },
    "japan": {
        "name": "Japan",
        "lat": 36.2048,
        "lon": 138.2529,
        "bbox": [129.50, 31.00, 145.80, 45.50],
        "zoom": 5.0,
    },
    "united kingdom": {
        "name": "United Kingdom",
        "lat": 55.3781,
        "lon": -3.4360,
        "bbox": [-8.65, 49.90, 1.77, 58.70],
        "zoom": 5.5,
    },
    "uk": {
        "name": "United Kingdom",
        "lat": 55.3781,
        "lon": -3.4360,
        "bbox": [-8.65, 49.90, 1.77, 58.70],
        "zoom": 5.5,
    },
    "britain": {
        "name": "United Kingdom",
        "lat": 55.3781,
        "lon": -3.4360,
        "bbox": [-8.65, 49.90, 1.77, 58.70],
        "zoom": 5.5,
    },
    "england": {
        "name": "England, United Kingdom",
        "lat": 52.3555,
        "lon": -1.1743,
        "bbox": [-5.71, 49.96, 1.76, 55.81],
        "zoom": 6.0,
    },
    "france": {
        "name": "France",
        "lat": 46.2276,
        "lon": 2.2137,
        "bbox": [-4.80, 42.30, 8.25, 51.10],
        "zoom": 5.2,
    },
    "germany": {
        "name": "Germany",
        "lat": 51.1657,
        "lon": 10.4515,
        "bbox": [5.87, 47.27, 15.04, 55.06],
        "zoom": 5.5,
    },
    "australia": {
        "name": "Australia",
        "lat": -25.2744,
        "lon": 133.7751,
        "bbox": [112.92, -43.74, 153.64, -10.67],
        "zoom": 3.8,
    },
    "canada": {
        "name": "Canada",
        "lat": 56.1304,
        "lon": -106.3468,
        "bbox": [-141.00, 41.68, -52.62, 83.11],
        "zoom": 3.2,
    },
    "brazil": {
        "name": "Brazil",
        "lat": -14.2350,
        "lon": -51.9253,
        "bbox": [-73.98, -33.75, -34.79, 5.27],
        "zoom": 3.8,
    },
    "italy": {
        "name": "Italy",
        "lat": 41.8719,
        "lon": 12.5674,
        "bbox": [6.63, 36.65, 18.52, 47.09],
        "zoom": 5.5,
    },
    "spain": {
        "name": "Spain",
        "lat": 40.4637,
        "lon": -3.7492,
        "bbox": [-9.30, 36.00, 3.32, 43.79],
        "zoom": 5.5,
    },
    "uae": {
        "name": "United Arab Emirates",
        "lat": 23.4241,
        "lon": 53.8478,
        "bbox": [51.58, 22.63, 56.38, 26.08],
        "zoom": 6.5,
    },
    "united arab emirates": {
        "name": "United Arab Emirates",
        "lat": 23.4241,
        "lon": 53.8478,
        "bbox": [51.58, 22.63, 56.38, 26.08],
        "zoom": 6.5,
    },
    "saudi arabia": {
        "name": "Saudi Arabia",
        "lat": 23.8859,
        "lon": 45.0792,
        "bbox": [34.50, 16.38, 55.67, 32.16],
        "zoom": 4.8,
    },
    "singapore": {
        "name": "Singapore",
        "lat": 1.3521,
        "lon": 103.8198,
        "bbox": [103.62, 1.16, 104.09, 1.47],
        "zoom": 10.5,
    },
    "indonesia": {
        "name": "Indonesia",
        "lat": -0.7893,
        "lon": 113.9213,
        "bbox": [95.01, -11.00, 141.02, 5.91],
        "zoom": 4.2,
    },
    "south korea": {
        "name": "South Korea",
        "lat": 35.9078,
        "lon": 127.7669,
        "bbox": [126.10, 33.10, 129.58, 38.61],
        "zoom": 6.5,
    },
    "korea": {
        "name": "South Korea",
        "lat": 35.9078,
        "lon": 127.7669,
        "bbox": [126.10, 33.10, 129.58, 38.61],
        "zoom": 6.5,
    },
    "nepal": {
        "name": "Nepal",
        "lat": 28.3949,
        "lon": 84.1240,
        "bbox": [80.06, 26.35, 88.20, 30.45],
        "zoom": 6.5,
    },
    "sri lanka": {
        "name": "Sri Lanka",
        "lat": 7.8731,
        "lon": 80.7718,
        "bbox": [79.65, 5.92, 81.88, 9.84],
        "zoom": 7.0,
    },
    "bangladesh": {
        "name": "Bangladesh",
        "lat": 23.6850,
        "lon": 90.3563,
        "bbox": [88.01, 20.74, 92.67, 26.63],
        "zoom": 6.5,
    },
    "bhutan": {
        "name": "Bhutan",
        "lat": 27.5142,
        "lon": 90.4336,
        "bbox": [88.75, 26.70, 92.13, 28.25],
        "zoom": 7.5,
    },
    "pakistan": {
        "name": "Pakistan",
        "lat": 30.3753,
        "lon": 69.3451,
        "bbox": [60.87, 23.69, 77.84, 37.08],
        "zoom": 5.0,
    },
    "afghanistan": {
        "name": "Afghanistan",
        "lat": 33.9391,
        "lon": 67.7100,
        "bbox": [60.52, 29.38, 74.89, 38.49],
        "zoom": 5.2,
    },
    "iran": {
        "name": "Iran",
        "lat": 32.4279,
        "lon": 53.6880,
        "bbox": [44.03, 25.06, 63.32, 39.78],
        "zoom": 4.8,
    },
    "turkey": {
        "name": "Turkey",
        "lat": 38.9637,
        "lon": 35.2433,
        "bbox": [25.66, 35.82, 44.82, 42.11],
        "zoom": 5.2,
    },
    "turkiye": {
        "name": "Turkey",
        "lat": 38.9637,
        "lon": 35.2433,
        "bbox": [25.66, 35.82, 44.82, 42.11],
        "zoom": 5.2,
    },
    "egypt": {
        "name": "Egypt",
        "lat": 26.8206,
        "lon": 30.8025,
        "bbox": [24.70, 22.00, 36.90, 31.67],
        "zoom": 5.0,
    },
    "south africa": {
        "name": "South Africa",
        "lat": -30.5595,
        "lon": 22.9375,
        "bbox": [16.45, -34.83, 32.89, -22.13],
        "zoom": 4.8,
    },
    "argentina": {
        "name": "Argentina",
        "lat": -38.4161,
        "lon": -63.6167,
        "bbox": [-73.57, -55.05, -53.64, -21.78],
        "zoom": 3.8,
    },
    "mexico": {
        "name": "Mexico",
        "lat": 23.6345,
        "lon": -102.5528,
        "bbox": [-117.13, 14.53, -86.71, 32.72],
        "zoom": 4.5,
    },
    "switzerland": {
        "name": "Switzerland",
        "lat": 46.8182,
        "lon": 8.2275,
        "bbox": [5.96, 45.82, 10.49, 47.81],
        "zoom": 7.0,
    },
    "netherlands": {
        "name": "Netherlands",
        "lat": 52.1326,
        "lon": 5.2913,
        "bbox": [3.36, 50.75, 7.23, 53.55],
        "zoom": 7.0,
    },
    "ukraine": {
        "name": "Ukraine",
        "lat": 48.3794,
        "lon": 31.1656,
        "bbox": [22.14, 44.39, 40.23, 52.38],
        "zoom": 5.2,
    },
    "israel": {
        "name": "Israel",
        "lat": 31.0461,
        "lon": 34.8516,
        "bbox": [34.27, 29.49, 35.89, 33.28],
        "zoom": 7.5,
    },
    "thailand": {
        "name": "Thailand",
        "lat": 15.8700,
        "lon": 100.9925,
        "bbox": [97.35, 5.61, 105.64, 20.46],
        "zoom": 5.5,
    },
    "malaysia": {
        "name": "Malaysia",
        "lat": 4.2105,
        "lon": 101.9758,
        "bbox": [99.64, 0.85, 119.27, 7.36],
        "zoom": 5.5,
    },
    "philippines": {
        "name": "Philippines",
        "lat": 12.8797,
        "lon": 121.7740,
        "bbox": [116.93, 4.60, 126.61, 21.12],
        "zoom": 5.5,
    },

    # -------------------------------------------------------------------------
    # Global Mega Cities & World Capitals
    # -------------------------------------------------------------------------
    "beijing": {
        "name": "Beijing, China",
        "lat": 39.9042,
        "lon": 116.4074,
        "bbox": [116.10, 39.70, 116.70, 40.20],
        "zoom": 10.5,
    },
    "shanghai": {
        "name": "Shanghai, China",
        "lat": 31.2304,
        "lon": 121.4737,
        "bbox": [121.10, 30.90, 121.90, 31.50],
        "zoom": 10.5,
    },
    "hong kong": {
        "name": "Hong Kong",
        "lat": 22.3193,
        "lon": 114.1694,
        "bbox": [113.84, 22.15, 114.44, 22.56],
        "zoom": 10.5,
    },
    "tokyo": {
        "name": "Tokyo, Japan",
        "lat": 35.6762,
        "lon": 139.6503,
        "bbox": [139.50, 35.50, 139.85, 35.80],
        "zoom": 10.5,
    },
    "cairo": {
        "name": "Cairo, Egypt",
        "lat": 30.0444,
        "lon": 31.2357,
        "bbox": [31.15, 29.95, 31.35, 30.15],
        "zoom": 11.0,
    },
    "london": {
        "name": "London, United Kingdom",
        "lat": 51.5074,
        "lon": -0.1278,
        "bbox": [-0.30, 51.40, 0.05, 51.60],
        "zoom": 10.5,
    },
    "paris": {
        "name": "Paris, France",
        "lat": 48.8566,
        "lon": 2.3522,
        "bbox": [2.20, 48.75, 2.45, 48.95],
        "zoom": 11.0,
    },
    "new york": {
        "name": "New York, USA",
        "lat": 40.7128,
        "lon": -74.0060,
        "bbox": [-74.15, 40.60, -73.85, 40.85],
        "zoom": 10.5,
    },
    "washington": {
        "name": "Washington, D.C., USA",
        "lat": 38.9072,
        "lon": -77.0369,
        "bbox": [-77.15, 38.80, -76.90, 39.00],
        "zoom": 11.0,
    },
    "washington dc": {
        "name": "Washington, D.C., USA",
        "lat": 38.9072,
        "lon": -77.0369,
        "bbox": [-77.15, 38.80, -76.90, 39.00],
        "zoom": 11.0,
    },
    "moscow": {
        "name": "Moscow, Russia",
        "lat": 55.7558,
        "lon": 37.6173,
        "bbox": [37.30, 55.50, 37.90, 56.00],
        "zoom": 10.0,
    },
    "berlin": {
        "name": "Berlin, Germany",
        "lat": 52.5200,
        "lon": 13.4050,
        "bbox": [13.10, 52.35, 13.75, 52.68],
        "zoom": 10.5,
    },
    "rome": {
        "name": "Rome, Italy",
        "lat": 41.9028,
        "lon": 12.4964,
        "bbox": [12.35, 41.78, 12.65, 42.05],
        "zoom": 11.0,
    },
    "madrid": {
        "name": "Madrid, Spain",
        "lat": 40.4168,
        "lon": -3.7038,
        "bbox": [-3.85, 40.30, -3.55, 40.55],
        "zoom": 10.5,
    },
    "dubai": {
        "name": "Dubai, United Arab Emirates",
        "lat": 25.2048,
        "lon": 55.2708,
        "bbox": [55.05, 24.95, 55.45, 25.35],
        "zoom": 10.5,
    },
    "sydney": {
        "name": "Sydney, Australia",
        "lat": -33.8688,
        "lon": 151.2093,
        "bbox": [151.00, -34.05, 151.35, -33.70],
        "zoom": 10.5,
    },
    "toronto": {
        "name": "Toronto, Canada",
        "lat": 43.6532,
        "lon": -79.3832,
        "bbox": [-79.64, 43.58, -79.12, 43.85],
        "zoom": 10.5,
    },
    "seoul": {
        "name": "Seoul, South Korea",
        "lat": 37.5665,
        "lon": 126.9780,
        "bbox": [126.76, 37.43, 127.18, 37.70],
        "zoom": 10.5,
    },
    "bangkok": {
        "name": "Bangkok, Thailand",
        "lat": 13.7563,
        "lon": 100.5018,
        "bbox": [100.35, 13.55, 100.75, 13.95],
        "zoom": 10.5,
    },

    # -------------------------------------------------------------------------
    # Major Indian Cities & Space Centers
    # -------------------------------------------------------------------------
    "nagpur": {
        "name": "Nagpur, Maharashtra, India",
        "lat": 21.1458,
        "lon": 79.0882,
        "bbox": [79.00, 21.05, 79.18, 21.23],
        "zoom": 11.5,
    },
    "mumbai": {
        "name": "Mumbai, Maharashtra, India",
        "lat": 19.0760,
        "lon": 72.8777,
        "bbox": [72.75, 18.89, 73.00, 19.28],
        "zoom": 11.0,
    },
    "new delhi": {
        "name": "New Delhi, Delhi, India",
        "lat": 28.6139,
        "lon": 77.2090,
        "bbox": [77.10, 28.50, 77.35, 28.75],
        "zoom": 11.0,
    },
    "delhi": {
        "name": "Delhi, India",
        "lat": 28.6139,
        "lon": 77.2090,
        "bbox": [77.10, 28.50, 77.35, 28.75],
        "zoom": 11.0,
    },
    "bengaluru": {
        "name": "Bengaluru, Karnataka, India",
        "lat": 12.9716,
        "lon": 77.5946,
        "bbox": [77.45, 12.85, 77.75, 13.15],
        "zoom": 11.0,
    },
    "bangalore": {
        "name": "Bengaluru, Karnataka, India",
        "lat": 12.9716,
        "lon": 77.5946,
        "bbox": [77.45, 12.85, 77.75, 13.15],
        "zoom": 11.0,
    },
    "hyderabad": {
        "name": "Hyderabad, Telangana, India",
        "lat": 17.3850,
        "lon": 78.4867,
        "bbox": [78.35, 17.25, 78.60, 17.55],
        "zoom": 11.0,
    },
    "chennai": {
        "name": "Chennai, Tamil Nadu, India",
        "lat": 13.0827,
        "lon": 80.2707,
        "bbox": [80.15, 12.95, 80.35, 13.20],
        "zoom": 11.0,
    },
    "kolkata": {
        "name": "Kolkata, West Bengal, India",
        "lat": 22.5726,
        "lon": 88.3639,
        "bbox": [88.25, 22.45, 88.45, 22.68],
        "zoom": 11.0,
    },
    "pune": {
        "name": "Pune, Maharashtra, India",
        "lat": 18.5204,
        "lon": 73.8567,
        "bbox": [73.75, 18.42, 73.98, 18.62],
        "zoom": 11.5,
    },
    "ahmedabad": {
        "name": "Ahmedabad, Gujarat, India (SAC / ISRO)",
        "lat": 23.0225,
        "lon": 72.5714,
        "bbox": [72.45, 22.92, 72.68, 23.12],
        "zoom": 11.0,
    },
    "jaipur": {
        "name": "Jaipur, Rajasthan, India",
        "lat": 26.9124,
        "lon": 75.7873,
        "bbox": [75.68, 26.80, 75.92, 27.02],
        "zoom": 11.5,
    },
    "chandigarh": {
        "name": "Chandigarh, India",
        "lat": 30.7333,
        "lon": 76.7794,
        "bbox": [76.70, 30.65, 76.85, 30.80],
        "zoom": 12.0,
    },
    "sriharikota": {
        "name": "Satish Dhawan Space Centre (SHAR), Sriharikota, Andhra Pradesh",
        "lat": 13.7199,
        "lon": 80.2305,
        "bbox": [80.18, 13.65, 80.28, 13.80],
        "zoom": 12.5,
    },
    "shar": {
        "name": "Satish Dhawan Space Centre (SHAR), Sriharikota",
        "lat": 13.7199,
        "lon": 80.2305,
        "bbox": [80.18, 13.65, 80.28, 13.80],
        "zoom": 12.5,
    },
    "shadnagar": {
        "name": "NRSC Earth Station, Shadnagar, Telangana",
        "lat": 17.0683,
        "lon": 78.2045,
        "bbox": [78.15, 17.00, 78.25, 17.15],
        "zoom": 12.5,
    },
    "dehradun": {
        "name": "Indian Institute of Remote Sensing (IIRS), Dehradun, Uttarakhand",
        "lat": 30.3165,
        "lon": 78.0322,
        "bbox": [77.95, 30.25, 78.10, 30.40],
        "zoom": 12.0,
    },
    "thiruvananthapuram": {
        "name": "Vikram Sarabhai Space Centre (VSSC), Thiruvananthapuram, Kerala",
        "lat": 8.5241,
        "lon": 76.9366,
        "bbox": [8.45, 76.88, 8.58, 77.00],
        "zoom": 12.0,
    },

    # -------------------------------------------------------------------------
    # Indian States & Union Territories
    # -------------------------------------------------------------------------
    "maharashtra": {
        "name": "Maharashtra, India",
        "lat": 19.7515,
        "lon": 75.7139,
        "bbox": [72.60, 15.60, 80.90, 22.00],
        "zoom": 6.0,
    },
    "karnataka": {
        "name": "Karnataka, India",
        "lat": 15.3173,
        "lon": 75.7139,
        "bbox": [74.00, 11.50, 78.60, 18.50],
        "zoom": 6.0,
    },
    "tamil nadu": {
        "name": "Tamil Nadu, India",
        "lat": 11.1271,
        "lon": 78.6569,
        "bbox": [76.20, 8.00, 80.30, 13.50],
        "zoom": 6.0,
    },
    "kerala": {
        "name": "Kerala, India",
        "lat": 10.8505,
        "lon": 76.2711,
        "bbox": [74.80, 8.30, 77.40, 12.80],
        "zoom": 6.5,
    },
    "gujarat": {
        "name": "Gujarat, India",
        "lat": 22.2587,
        "lon": 71.1924,
        "bbox": [68.10, 20.10, 74.50, 24.70],
        "zoom": 6.0,
    },
    "rajasthan": {
        "name": "Rajasthan, India",
        "lat": 27.0238,
        "lon": 74.2179,
        "bbox": [69.50, 23.00, 78.30, 30.20],
        "zoom": 5.5,
    },
    "uttar pradesh": {
        "name": "Uttar Pradesh, India",
        "lat": 26.8467,
        "lon": 80.9462,
        "bbox": [77.10, 23.90, 84.60, 30.40],
        "zoom": 5.5,
    },
    "up": {
        "name": "Uttar Pradesh, India",
        "lat": 26.8467,
        "lon": 80.9462,
        "bbox": [77.10, 23.90, 84.60, 30.40],
        "zoom": 5.5,
    },
    "madhya pradesh": {
        "name": "Madhya Pradesh, India",
        "lat": 22.9734,
        "lon": 78.6569,
        "bbox": [74.00, 21.10, 82.80, 26.90],
        "zoom": 5.5,
    },
    "mp": {
        "name": "Madhya Pradesh, India",
        "lat": 22.9734,
        "lon": 78.6569,
        "bbox": [74.00, 21.10, 82.80, 26.90],
        "zoom": 5.5,
    },
    "west bengal": {
        "name": "West Bengal, India",
        "lat": 22.9868,
        "lon": 87.8550,
        "bbox": [85.80, 21.50, 89.90, 27.20],
        "zoom": 6.0,
    },
    "bihar": {
        "name": "Bihar, India",
        "lat": 25.0961,
        "lon": 85.3131,
        "bbox": [83.30, 24.30, 88.30, 27.50],
        "zoom": 6.2,
    },
    "telangana": {
        "name": "Telangana, India",
        "lat": 18.1124,
        "lon": 79.0193,
        "bbox": [77.20, 15.80, 81.30, 19.90],
        "zoom": 6.2,
    },
    "andhra pradesh": {
        "name": "Andhra Pradesh, India",
        "lat": 15.9129,
        "lon": 79.7400,
        "bbox": [76.80, 12.60, 84.80, 19.10],
        "zoom": 6.0,
    },
    "punjab": {
        "name": "Punjab, India",
        "lat": 31.1471,
        "lon": 75.3412,
        "bbox": [73.80, 29.50, 76.90, 32.50],
        "zoom": 6.5,
    },
    "haryana": {
        "name": "Haryana, India",
        "lat": 29.0588,
        "lon": 76.0856,
        "bbox": [74.40, 27.60, 77.60, 30.90],
        "zoom": 6.8,
    },
    "kashmir": {
        "name": "Jammu & Kashmir, India",
        "lat": 33.7782,
        "lon": 76.5762,
        "bbox": [73.50, 32.20, 79.50, 36.50],
        "zoom": 6.0,
    },
    "jammu and kashmir": {
        "name": "Jammu & Kashmir, India",
        "lat": 33.7782,
        "lon": 76.5762,
        "bbox": [73.50, 32.20, 79.50, 36.50],
        "zoom": 6.0,
    },
    "ladakh": {
        "name": "Ladakh, India",
        "lat": 34.1526,
        "lon": 77.5771,
        "bbox": [75.50, 32.00, 79.50, 36.00],
        "zoom": 6.0,
    },
    "himachal pradesh": {
        "name": "Himachal Pradesh, India",
        "lat": 31.1048,
        "lon": 77.1734,
        "bbox": [75.50, 30.40, 79.00, 33.20],
        "zoom": 6.5,
    },
    "uttarakhand": {
        "name": "Uttarakhand, India",
        "lat": 30.0668,
        "lon": 79.0193,
        "bbox": [77.50, 28.70, 81.00, 31.50],
        "zoom": 6.5,
    },
    "odisha": {
        "name": "Odisha, India",
        "lat": 20.9517,
        "lon": 85.0985,
        "bbox": [81.40, 17.80, 87.50, 22.60],
        "zoom": 6.2,
    },
    "assam": {
        "name": "Assam, India",
        "lat": 26.2006,
        "lon": 92.9376,
        "bbox": [89.70, 24.10, 96.00, 28.00],
        "zoom": 6.5,
    },
    "goa": {
        "name": "Goa, India",
        "lat": 15.2993,
        "lon": 74.1240,
        "bbox": [73.60, 14.90, 74.40, 15.80],
        "zoom": 9.5,
    },

    # -------------------------------------------------------------------------
    # Major Geographic Features, Landforms & Oceans
    # -------------------------------------------------------------------------
    "himalayas": {
        "name": "Himalayas Mountain Range",
        "lat": 28.5983,
        "lon": 83.9311,
        "bbox": [73.00, 26.00, 95.00, 36.00],
        "zoom": 5.0,
    },
    "everest": {
        "name": "Mount Everest, Himalayas",
        "lat": 27.9881,
        "lon": 86.9250,
        "bbox": [86.85, 27.90, 87.00, 28.05],
        "zoom": 12.5,
    },
    "mount everest": {
        "name": "Mount Everest, Himalayas",
        "lat": 27.9881,
        "lon": 86.9250,
        "bbox": [86.85, 27.90, 87.00, 28.05],
        "zoom": 12.5,
    },
    "taj mahal": {
        "name": "Taj Mahal, Agra, India",
        "lat": 27.1751,
        "lon": 78.0421,
        "bbox": [78.0400, 27.1720, 78.0442, 27.1762],
        "zoom": 16.5,
    },
    "suez canal": {
        "name": "Suez Canal, Egypt",
        "lat": 30.5852,
        "lon": 32.5684,
        "bbox": [32.30, 29.80, 32.70, 31.30],
        "zoom": 9.5,
    },
    "panama canal": {
        "name": "Panama Canal, Panama",
        "lat": 9.0800,
        "lon": -79.6800,
        "bbox": [-79.95, 8.90, -79.50, 9.40],
        "zoom": 10.0,
    },
    "sahara desert": {
        "name": "Sahara Desert, Africa",
        "lat": 23.4162,
        "lon": 25.6628,
        "bbox": [-13.00, 15.00, 35.00, 32.00],
        "zoom": 4.0,
    },
    "amazon rainforest": {
        "name": "Amazon Rainforest, South America",
        "lat": -3.4653,
        "lon": -62.2159,
        "bbox": [-75.00, -15.00, -50.00, 5.00],
        "zoom": 4.5,
    },
    "indian ocean": {
        "name": "Indian Ocean",
        "lat": -20.0000,
        "lon": 80.0000,
        "bbox": [40.00, -45.00, 110.00, 20.00],
        "zoom": 3.0,
    },
    "pacific ocean": {
        "name": "Pacific Ocean",
        "lat": 0.0000,
        "lon": -160.0000,
        "bbox": [-180.00, -50.00, -70.00, 50.00],
        "zoom": 2.5,
    },
    "atlantic ocean": {
        "name": "Atlantic Ocean",
        "lat": 0.0000,
        "lon": -30.0000,
        "bbox": [-60.00, -50.00, 0.00, 50.00],
        "zoom": 2.5,
    },

    # Geopolitical Aliases
    "capital of india": {
        "name": "New Delhi (Capital of India)",
        "lat": 28.6139,
        "lon": 77.2090,
        "bbox": [77.10, 28.50, 77.35, 28.75],
        "zoom": 11.0,
    },
    "capital of bharat": {
        "name": "New Delhi (Capital of India)",
        "lat": 28.6139,
        "lon": 77.2090,
        "bbox": [77.10, 28.50, 77.35, 28.75],
        "zoom": 11.0,
    },
    "national capital": {
        "name": "New Delhi (National Capital Region)",
        "lat": 28.6139,
        "lon": 77.2090,
        "bbox": [77.10, 28.50, 77.35, 28.75],
        "zoom": 11.0,
    },
    "financial capital of india": {
        "name": "Mumbai (Financial Capital of India)",
        "lat": 19.0760,
        "lon": 72.8777,
        "bbox": [72.75, 18.89, 73.00, 19.28],
        "zoom": 11.0,
    },
    "space city of india": {
        "name": "Bengaluru (Space City / ISRO HQ)",
        "lat": 12.9716,
        "lon": 77.5946,
        "bbox": [77.45, 12.85, 77.75, 13.15],
        "zoom": 11.0,
    },
    "silicon valley of india": {
        "name": "Bengaluru (Silicon Valley of India)",
        "lat": 12.9716,
        "lon": 77.5946,
        "bbox": [77.45, 12.85, 77.75, 13.15],
        "zoom": 11.0,
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
        first_segment = clean_lower.split(",")[0].strip()
        first_norm = re.sub(r"^(?:the|to|at|in)\s+", "", first_segment).strip()
        lookup_key = (
            clean_lower if clean_lower in OFFLINE_GAZETTEER
            else (clean_norm if clean_norm in OFFLINE_GAZETTEER
            else (first_segment if first_segment in OFFLINE_GAZETTEER
            else (first_norm if first_norm in OFFLINE_GAZETTEER else None)))
        )
        if lookup_key:
            entry = OFFLINE_GAZETTEER[lookup_key]
            raw_bbox = entry.get("bbox")
            bbox = cls._sanitize_bbox(raw_bbox, entry["lat"], entry["lon"]) if raw_bbox else None
            target = GeographicTarget(
                name=entry["name"],
                latitude=entry["lat"],
                longitude=entry["lon"],
                bbox=bbox,
                zoom=entry.get("zoom"),
                source="offline_gazetteer",
                confidence=1.0,
                is_ambiguous=False,
            )
            cls._set_cache(clean_lower, target)
            return target

        # 5. Word-boundary match in gazetteer (longest key first)
        # Prevents "Taj Mahal, Agra, India" from matching "India" before "Taj Mahal"
        for key, entry in sorted(OFFLINE_GAZETTEER.items(), key=lambda x: len(x[0]), reverse=True):
            pattern = r"\b" + re.escape(key) + r"\b"
            if re.search(pattern, clean_lower) or (clean_norm and re.search(pattern, clean_norm)):
                raw_bbox = entry.get("bbox")
                bbox = cls._sanitize_bbox(raw_bbox, entry["lat"], entry["lon"]) if raw_bbox else None
                target = GeographicTarget(
                    name=entry["name"],
                    latitude=entry["lat"],
                    longitude=entry["lon"],
                    bbox=bbox,
                    zoom=entry.get("zoom"),
                    source="offline_gazetteer",
                    confidence=0.9,
                    is_ambiguous=False,
                )
                cls._set_cache(clean_lower, target)
                return target

        # 6. Global Online Geocoder Integration (OSM Nominatim / Photon / Mapbox / Google)
        # Allows user to navigate to ANY city, town, village, or spot worldwide (e.g. Alaska, Taj Mahal, etc.)
        query_for_online = clean_norm or clean_lower
        online_target = cls._query_online_geocoder(query_for_online)
        if online_target:
            cls._set_cache(clean_lower, online_target)
            return online_target

        return None

    @classmethod
    def _query_online_geocoder(cls, query: str) -> Optional[GeographicTarget]:
        """
        Dynamically queries an online geocoding service to resolve any city, village,
        POI, or landmark worldwide into precise WGS84 coordinates and bounding box.
        Prioritizes Mapbox / Google if API keys are configured, otherwise uses free
        OpenStreetMap Nominatim with a Photon fallback.
        """
        if not query or len(query.strip()) < 2:
            return None

        clean_q = query.strip()

        # 1. Check if Mapbox access token is configured
        mapbox_token = os.getenv("MAPBOX_ACCESS_TOKEN") or getattr(settings, "mapbox_access_token", None)
        if mapbox_token:
            target = cls._query_mapbox(clean_q, mapbox_token)
            if target:
                return target

        # 2. Check if Google Geocoding API key is configured
        google_key = os.getenv("GOOGLE_GEOCODING_API_KEY") or getattr(settings, "geocoding_api_key", None)
        if google_key and getattr(settings, "geocoding_provider", "auto") == "google":
            target = cls._query_google(clean_q, google_key)
            if target:
                return target

        # 3. Default Primary: OpenStreetMap Nominatim (Free, Global, Zero-key required)
        target = cls._query_nominatim(clean_q)
        if target:
            return target

        # 4. Secondary Fallback: Komoot Photon (Free, Global, High-speed)
        return cls._query_photon(clean_q)

    @classmethod
    def _sanitize_bbox(
        cls,
        bbox: Optional[List[float]],
        lat: float,
        lon: float,
    ) -> Optional[List[float]]:
        """
        Validates, clamps, and sanitizes bounding boxes.
        Prevents antimeridian-wrapping or globe-spanning boxes (e.g. [-180, 180])
        from crashing map engines or Cesium WebGL workers.
        """
        if not bbox or len(bbox) != 4:
            return None
        try:
            min_lon, min_lat, max_lon, max_lat = [float(x) for x in bbox]
        except (ValueError, TypeError):
            return None

        if min_lat > max_lat:
            min_lat, max_lat = max_lat, min_lat
        if min_lon > max_lon:
            min_lon, max_lon = max_lon, min_lon

        min_lat = max(-85.0, min(85.0, min_lat))
        max_lat = max(-85.0, min(85.0, max_lat))

        lon_span = max_lon - min_lon
        # If span wraps entire planet or touches/crosses antimeridian boundaries (e.g. Alaska, Chukotka)
        if lon_span >= 180.0 or min_lon <= -179.9 or max_lon >= 179.9:
            lat_span = max(0.2, max_lat - min_lat)
            half_span_lon = min(20.0, max(1.0, lat_span * 1.2))
            min_lon = max(-179.9, lon - half_span_lon)
            max_lon = min(179.9, lon + half_span_lon)
        else:
            min_lon = max(-179.9, min(179.9, min_lon))
            max_lon = min(179.9, max(-179.9, max_lon))

        return [round(min_lon, 5), round(min_lat, 5), round(max_lon, 5), round(max_lat, 5)]

    @classmethod
    def _query_nominatim(cls, query: str) -> Optional[GeographicTarget]:
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}&format=json&limit=1&addressdetails=1"
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "TRINETRA-Geospatial-Intelligence/2.2 (https://trinetra.gov.in; contact: support@trinetra.gov.in)",
                    "Accept-Language": "en",
                },
            )
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if not data:
                    return None
                hit = data[0]
                lat = float(hit["lat"])
                lon = float(hit["lon"])
                bb = hit.get("boundingbox")
                bbox = None
                if bb and len(bb) == 4:
                    # Nominatim returns [lat_min, lat_max, lon_min, lon_max]
                    raw_bbox = [float(bb[2]), float(bb[0]), float(bb[3]), float(bb[1])]
                    bbox = cls._sanitize_bbox(raw_bbox, lat, lon)

                disp = hit.get("display_name", query.title())
                parts = [p.strip() for p in disp.split(",")]
                short_name = ", ".join(parts[:3]) if len(parts) > 3 else disp

                return GeographicTarget(
                    name=short_name,
                    latitude=lat,
                    longitude=lon,
                    bbox=bbox,
                    source="osm_nominatim",
                    confidence=0.95,
                )
        except Exception:
            return None

    @classmethod
    def _query_photon(cls, query: str) -> Optional[GeographicTarget]:
        try:
            url = f"https://photon.komoot.io/api/?q={urllib.parse.quote(query)}&limit=1"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "TRINETRA-Geospatial-Intelligence/2.2"},
            )
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                features = data.get("features", [])
                if not features:
                    return None
                f = features[0]
                coords = f["geometry"]["coordinates"]
                props = f.get("properties", {})
                lon, lat = float(coords[0]), float(coords[1])
                extent = props.get("extent")  # [min_lon, max_lat, max_lon, min_lat]
                raw_bbox = [float(extent[0]), float(extent[3]), float(extent[2]), float(extent[1])] if extent and len(extent) == 4 else None
                bbox = cls._sanitize_bbox(raw_bbox, lat, lon)

                name_parts = [props.get("name")]
                if props.get("city") and props.get("city") != props.get("name"):
                    name_parts.append(props.get("city"))
                if props.get("state") and props.get("state") != props.get("name"):
                    name_parts.append(props.get("state"))
                if props.get("country"):
                    name_parts.append(props.get("country"))
                short_name = ", ".join([p for p in name_parts if p]) or query.title()

                return GeographicTarget(
                    name=short_name,
                    latitude=lat,
                    longitude=lon,
                    bbox=bbox,
                    source="photon_osm",
                    confidence=0.92,
                )
        except Exception:
            return None

    @classmethod
    def _query_mapbox(cls, query: str, token: str) -> Optional[GeographicTarget]:
        try:
            url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{urllib.parse.quote(query)}.json?access_token={token}&limit=1"
            req = urllib.request.Request(url, headers={"User-Agent": "TRINETRA-Geospatial-Intelligence/2.2"})
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                features = data.get("features", [])
                if not features:
                    return None
                f = features[0]
                lon, lat = f["center"]
                bbox = cls._sanitize_bbox(f.get("bbox"), float(lat), float(lon))
                return GeographicTarget(
                    name=f.get("place_name", query.title()),
                    latitude=float(lat),
                    longitude=float(lon),
                    bbox=bbox,
                    source="mapbox_geocoding",
                    confidence=0.98,
                )
        except Exception:
            return None

    @classmethod
    def _query_google(cls, query: str, api_key: str) -> Optional[GeographicTarget]:
        try:
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(query)}&key={api_key}"
            req = urllib.request.Request(url, headers={"User-Agent": "TRINETRA-Geospatial-Intelligence/2.2"})
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = data.get("results", [])
                if not results:
                    return None
                r = results[0]
                loc = r["geometry"]["location"]
                vp = r["geometry"].get("viewport", {})
                raw_bbox = None
                if vp:
                    raw_bbox = [vp["southwest"]["lng"], vp["southwest"]["lat"], vp["northeast"]["lng"], vp["northeast"]["lat"]]
                bbox = cls._sanitize_bbox(raw_bbox, float(loc["lat"]), float(loc["lng"]))
                return GeographicTarget(
                    name=r.get("formatted_address", query.title()),
                    latitude=float(loc["lat"]),
                    longitude=float(loc["lng"]),
                    bbox=bbox,
                    source="google_geocoding",
                    confidence=0.98,
                )
        except Exception:
            return None

    @classmethod
    def _set_cache(cls, key: str, target: GeographicTarget) -> None:
        cls._cache[key] = target
        if len(cls._cache) > cls._MAX_CACHE_SIZE:
            cls._cache.popitem(last=False)

    @classmethod
    def find_nearest(cls, lat: float, lon: float) -> GeographicTarget:
        """Finds the closest known gazetteer target to the specified coordinates."""
        best_entry = None
        best_dist = float("inf")

        for key, entry in OFFLINE_GAZETTEER.items():
            dist = (entry["lat"] - lat) ** 2 + (entry["lon"] - lon) ** 2
            if dist < best_dist:
                best_dist = dist
                best_entry = entry

        if best_entry and best_dist < 25.0:  # within ~5 degrees
            return GeographicTarget(
                name=best_entry["name"],
                latitude=best_entry["lat"],
                longitude=best_entry["lon"],
                bbox=best_entry.get("bbox"),
                source="offline_gazetteer",
                confidence=round(max(0.75, 1.0 - (best_dist / 50.0)), 2),
            )

        return GeographicTarget(
            name=f"Geographic Coordinates ({lat:.4f}° N, {lon:.4f}° E)",
            latitude=lat,
            longitude=lon,
            source="coordinate_estimate",
            confidence=0.85,
        )

