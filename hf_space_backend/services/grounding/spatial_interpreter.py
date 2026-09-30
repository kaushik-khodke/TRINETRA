"""
TRINETRA — Spatial Query Interpreter
Parses natural-language queries into structured spatial intent prior to grounding and detection.
Handles directional constraints, rankings, counts, geometries, and feature targets deterministically.
"""

import re
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class SpatialQueryIntent(BaseModel):
    target: str
    action: str = "detect"  # locate, detect, highlight, measure, compare
    region_constraint: Optional[str] = None  # north, south, east, west, northeast, northwest, southeast, southwest, center, boundary, upper, lower, left, right, etc.
    ranking: Optional[str] = None  # largest, smallest, nearest, farthest, primary
    count: str = "primary"  # all, single, primary
    geometry: str = "bbox"  # bbox, point, polygon
    is_spatial_query: bool = True
    confidence: float = 0.95
    raw_query: str = ""

class SpatialQueryInterpreter:
    """Deterministic spatial intent parser for Earth observation natural-language queries."""

    # Cardinal & relative directional patterns
    DIRECTIONS: Dict[str, List[str]] = {
        "northwest": [r"\bnorth-?west\b", r"\bnw\b", r"\bupper-?left\b", r"\btop-?left\b"],
        "northeast": [r"\bnorth-?east\b", r"\bne\b", r"\bupper-?right\b", r"\btop-?right\b"],
        "southwest": [r"\bsouth-?west\b", r"\bsw\b", r"\blower-?left\b", r"\bbottom-?left\b"],
        "southeast": [r"\bsouth-?east\b", r"\bse\b", r"\blower-?right\b", r"\bbottom-?right\b"],
        "north": [r"\bnorth\b", r"\bnorthern\b", r"\bupper\b", r"\btop\b"],
        "south": [r"\bsouth\b", r"\bsouthern\b", r"\blower\b", r"\bbottom\b"],
        "east": [r"\beast\b", r"\beastern\b", r"\bright\b"],
        "west": [r"\bwest\b", r"\bwestern\b", r"\bleft\b"],
        "center": [r"\bcenter\b", r"\bcentral\b", r"\bmiddle\b"],
        "boundary": [r"\bboundary\b", r"\bperiphery\b", r"\bedge\b", r"\bborder\b"]
    }

    # Action verbs
    ACTIONS: Dict[str, List[str]] = {
        "locate": [r"\blocate\b", r"\bwhere is\b", r"\bwhere are\b", r"\bpinpoint\b", r"\bfind\b", r"\bspot\b"],
        "highlight": [r"\bhighlight\b", r"\bmark\b", r"\boutline\b", r"\bsegment\b"],
        "detect": [r"\bdetect\b", r"\bshow\b", r"\bidentify\b", r"\bdiscover\b"],
        "measure": [r"\bmeasure\b", r"\barea of\b", r"\bsize of\b", r"\bhow large\b", r"\bhow big\b", r"\bextent\b"],
        "compare": [r"\bcompare\b", r"\bdifference\b", r"\bchange\b", r"\bshift\b"]
    }

    # Ranking modifiers
    RANKINGS: Dict[str, List[str]] = {
        "largest": [r"\blargest\b", r"\bbiggest\b", r"\bmaximum\b", r"\bmost extensive\b", r"\bmain\b", r"\bprimary\b"],
        "smallest": [r"\bsmallest\b", r"\btiniest\b", r"\bminimum\b", r"\bleast\b"],
        "nearest": [r"\bnearest\b", r"\bclosest\b"],
        "farthest": [r"\bfarthest\b", r"\bmost distant\b"]
    }

    # Count / cardinality modifiers
    COUNTS: Dict[str, List[str]] = {
        "all": [r"\ball\b", r"\bevery\b", r"\beach\b", r"\bentire\b", r"\bmultiple\b"],
        "single": [r"\ba\b", r"\ban\b", r"\bone\b", r"\bsingle\b"],
        "primary": [r"\bthe\b", r"\bprimary\b"]
    }

    # Geometry preference
    GEOMETRIES: Dict[str, List[str]] = {
        "point": [r"\bpoint\b", r"\bspot\b", r"\bpin\b", r"\bdot\b", r"\bexact location\b", r"\bcoordinate\b"],
        "polygon": [r"\bpolygon\b", r"\bcontour\b", r"\bperimeter\b", r"\bextent\b", r"\bboundary\b", r"\bflood extent\b", r"\bfootprint\b"],
        "bbox": [r"\bbox\b", r"\bbounding box\b", r"\bregion\b", r"\bframe\b"]
    }

    # Common remote sensing targets
    TARGET_PATTERNS = [
        ("water body", [r"\bwater bodies\b", r"\bwater body\b", r"\bwater\b", r"\bhydrological\b"]),
        ("lake", [r"\blakes\b", r"\blake\b"]),
        ("river", [r"\brivers\b", r"\briver\b", r"\bstream\b", r"\bcanal\b"]),
        ("ocean", [r"\bocean\b", r"\bsea\b", r"\bcoastline\b", r"\bshore\b"]),
        ("reservoir", [r"\breservoir\b", r"\bdam\b"]),
        ("vegetation loss", [r"\bvegetation loss\b", r"\bdeforestation\b", r"\btree loss\b", r"\bcanopy loss\b"]),
        ("vegetation", [r"\bvegetation\b", r"\bforest\b", r"\btrees\b", r"\bgreener\b", r"\bcanopy\b"]),
        ("agricultural land", [r"\bagricultural\b", r"\bfarmland\b", r"\bcrop\b", r"\bfields\b"]),
        ("building", [r"\bbuildings\b", r"\bbuilding\b", r"\bstructures\b", r"\bhouses\b", r"\broofs\b"]),
        ("built-up", [r"\bbuilt-up\b", r"\burban\b", r"\bcity\b", r"\bsettlement\b"]),
        ("airport", [r"\bairports?\b", r"\bairfield\b", r"\baerodrome\b"]),
        ("runway", [r"\brunways?\b", r"\btaxiway\b", r"\btarmac\b", r"\bairstrip\b"]),
        ("aircraft", [r"\baircraft\b", r"\bairplane\b", r"\bplane\b"]),
        ("road", [r"\broads?\b", r"\bhighway\b", r"\bmotorway\b", r"\bstreet\b"]),
        ("bridge", [r"\bbridges?\b", r"\boverpass\b"]),
        ("change area", [r"\bchange area\b", r"\barea of change\b", r"\bmodified region\b", r"\bnew development\b"]),
        ("flood", [r"\bflood(ed|ing)?\b", r"\binundat(ion|ed)\b", r"\bsubmerged\b"]),
        ("vessel", [r"\bvessels?\b", r"\bships?\b", r"\bboats?\b"])
    ]

    @classmethod
    def parse(cls, query: str) -> SpatialQueryIntent:
        clean_q = query.strip().lower()

        # 1. Detect Action
        detected_action = "detect"
        for act, patterns in cls.ACTIONS.items():
            if any(re.search(p, clean_q) for p in patterns):
                detected_action = act
                break

        # 2. Detect Direction / Region Constraint (compound directions first)
        region_constraint = None
        for direction in ["northwest", "northeast", "southwest", "southeast", "north", "south", "east", "west", "center", "boundary"]:
            patterns = cls.DIRECTIONS[direction]
            if any(re.search(p, clean_q) for p in patterns):
                region_constraint = direction
                break

        # 3. Detect Ranking
        ranking = None
        for rk, patterns in cls.RANKINGS.items():
            if any(re.search(p, clean_q) for p in patterns):
                ranking = rk
                break

        # 4. Detect Count
        count = "primary"
        for cnt, patterns in cls.COUNTS.items():
            if any(re.search(p, clean_q) for p in patterns):
                count = cnt
                break
        if ranking == "largest" or ranking == "smallest":
            count = "single"

        # 5. Detect Geometry
        geometry = "bbox"
        for geom, patterns in cls.GEOMETRIES.items():
            if any(re.search(p, clean_q) for p in patterns):
                geometry = geom
                break
        if detected_action == "highlight" and ("flood" in clean_q or "vegetation" in clean_q or "water" in clean_q):
            geometry = "polygon"

        # 6. Detect Target Feature
        detected_target = "salient feature"
        for target_name, patterns in cls.TARGET_PATTERNS:
            if any(re.search(p, clean_q) for p in patterns):
                detected_target = target_name
                break

        # If no specific target matched, extract noun phrase heuristic
        if detected_target == "salient feature":
            # Strip question/action prefix
            stripped = re.sub(r"^(find|show|locate|detect|where is|where are|highlight|spot|pinpoint|mark)\s+", "", clean_q)
            stripped = re.sub(r"^(the|all|a|an)\s+", "", stripped)
            # Remove directional suffix (e.g., "in the east", "on the right")
            stripped = re.sub(r"\s+(in|on|at|near)\s+the\s+(north|south|east|west|center|middle|left|right).*$", "", stripped)
            stripped = stripped.strip("?. ")
            if stripped:
                detected_target = stripped

        is_spatial = bool(
            region_constraint or
            ranking or
            detected_action in ["locate", "highlight", "detect"] or
            geometry in ["point", "polygon"] or
            any(w in clean_q for w in ["where", "corner", "side", "area", "region", "zone", "spot"])
        )

        return SpatialQueryIntent(
            target=detected_target,
            action=detected_action,
            region_constraint=region_constraint,
            ranking=ranking,
            count=count,
            geometry=geometry,
            is_spatial_query=is_spatial,
            raw_query=query
        )
