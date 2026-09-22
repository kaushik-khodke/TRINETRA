"""
TRINETRA Phase 6 — Semantic Taxonomy
Controlled vocabulary of Earth-observation land-cover and structural transformations.
"""

from enum import Enum
from typing import Dict, Any, List


class SemanticClass(str, Enum):
    BUILT_UP_EXPANSION = "BUILT_UP_EXPANSION"
    VEGETATION_LOSS = "VEGETATION_LOSS"
    VEGETATION_GAIN = "VEGETATION_GAIN"
    WATER_EXPANSION = "WATER_EXPANSION"
    WATER_REDUCTION = "WATER_REDUCTION"
    ROAD_DEVELOPMENT = "ROAD_DEVELOPMENT"
    STRUCTURE_APPEARANCE = "STRUCTURE_APPEARANCE"
    STRUCTURE_REMOVAL = "STRUCTURE_REMOVAL"
    BARE_SOIL_EXPANSION = "BARE_SOIL_EXPANSION"
    AGRICULTURAL_CHANGE = "AGRICULTURAL_CHANGE"
    UNCERTAIN_LAND_COVER_CHANGE = "UNCERTAIN_LAND_COVER_CHANGE"
    UNCLASSIFIED_CHANGE = "UNCLASSIFIED_CHANGE"


TAXONOMY_DESCRIPTIONS: Dict[SemanticClass, str] = {
    SemanticClass.BUILT_UP_EXPANSION: "Expansion of artificial surfaces, asphalt, or masonry clusters.",
    SemanticClass.VEGETATION_LOSS: "Significant reduction in photosynthetic green canopy density.",
    SemanticClass.VEGETATION_GAIN: "Vegetative regrowth, canopy replenishment, or afforestation.",
    SemanticClass.WATER_EXPANSION: "Increased surface water extent, inundation, or reservoir rise.",
    SemanticClass.WATER_REDUCTION: "Recession of water surface, reservoir drawdown, or wetland drying.",
    SemanticClass.ROAD_DEVELOPMENT: "Linear infrastructure, highway corridor, or road clearing expansion.",
    SemanticClass.STRUCTURE_APPEARANCE: "Detection of new discrete buildings, hangars, or industrial facilities.",
    SemanticClass.STRUCTURE_REMOVAL: "Demolition or loss of previously verified structures.",
    SemanticClass.BARE_SOIL_EXPANSION: "Exposed soil, earthworks, or site leveling prior to construction.",
    SemanticClass.AGRICULTURAL_CHANGE: "Seasonal crop phenology, field tilling, or harvest rotation.",
    SemanticClass.UNCERTAIN_LAND_COVER_CHANGE: "Measurable surface transformation with ambiguous spectral characteristics.",
    SemanticClass.UNCLASSIFIED_CHANGE: "Low-confidence or unconstrained radiometric variance.",
}
