"""
TRINETRA Phase 6 — Investigation Tool Registry
Abstracts analytical specialists behind uniform, capability-oriented interfaces.
"""

from typing import Dict, Any, List, Optional, Callable


class InvestigationCapability:
    def __init__(
        self,
        name: str,
        description: str,
        required_modalities: List[str],
        produces_evidence_types: List[str],
        handler: Optional[Callable] = None,
    ):
        self.name = name
        self.description = description
        self.required_modalities = required_modalities
        self.produces_evidence_types = produces_evidence_types
        self.handler = handler

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "required_modalities": self.required_modalities,
            "produces_evidence_types": self.produces_evidence_types,
        }


class InvestigationToolRegistry:
    """
    Central registry mapping capability names to specialist model handlers.
    """
    _capabilities: Dict[str, InvestigationCapability] = {}

    @classmethod
    def register(cls, capability: InvestigationCapability) -> None:
        cls._capabilities[capability.name] = capability

    @classmethod
    def get(cls, name: str) -> Optional[InvestigationCapability]:
        return cls._capabilities.get(name)

    @classmethod
    def list_capabilities(cls) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in cls._capabilities.values()]

    @classmethod
    def initialize_defaults(cls) -> None:
        if cls._capabilities:
            return

        cls.register(
            InvestigationCapability(
                name="change_detection",
                description="Bi-temporal differential change detection via Siamese neural network",
                required_modalities=["optical"],
                produces_evidence_types=["CHANGE", "SPATIAL", "GIS_STATISTIC"],
            )
        )
        cls.register(
            InvestigationCapability(
                name="grounding",
                description="Text-guided object and region grounding with localized bounding boxes",
                required_modalities=["optical"],
                produces_evidence_types=["OBJECT", "SPATIAL"],
            )
        )
        cls.register(
            InvestigationCapability(
                name="vqa",
                description="Visual Question Answering for localized scene properties",
                required_modalities=["optical"],
                produces_evidence_types=["METADATA", "SPATIAL"],
            )
        )
        cls.register(
            InvestigationCapability(
                name="caption",
                description="Automated EO scene description and land-cover tagging",
                required_modalities=["optical"],
                produces_evidence_types=["METADATA"],
            )
        )
        cls.register(
            InvestigationCapability(
                name="sar_analysis",
                description="Microwave SAR backscatter delta and polarization analysis",
                required_modalities=["sar"],
                produces_evidence_types=["SAR", "RADIOMETRIC"],
            )
        )
        cls.register(
            InvestigationCapability(
                name="optical_analysis",
                description="Multispectral optical surface reflectance and quality masking",
                required_modalities=["optical"],
                produces_evidence_types=["OPTICAL", "RADIOMETRIC"],
            )
        )
        cls.register(
            InvestigationCapability(
                name="spectral_analysis",
                description="Multispectral vegetation, water, and built-up index calculation (NDVI, NDWI, NDBI)",
                required_modalities=["optical"],
                produces_evidence_types=["SPECTRAL"],
            )
        )
        cls.register(
            InvestigationCapability(
                name="gis_statistics",
                description="Geodesic surface area, perimeter, centroid, and spatial overlap metrics",
                required_modalities=[],
                produces_evidence_types=["GIS_STATISTIC", "SPATIAL"],
            )
        )
        cls.register(
            InvestigationCapability(
                name="temporal_statistics",
                description="Multi-date trajectory, persistence scoring, and transition matrices",
                required_modalities=[],
                produces_evidence_types=["TEMPORAL"],
            )
        )
        cls.register(
            InvestigationCapability(
                name="object_tracking",
                description="Cross-temporal object matching and lifecycle state tracking",
                required_modalities=["optical"],
                produces_evidence_types=["OBJECT", "TEMPORAL"],
            )
        )


InvestigationToolRegistry.initialize_defaults()
