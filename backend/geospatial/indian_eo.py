"""
TRINETRA Indian Earth Observation (EO) & ISRO Relevance Validation Engine (Stage 11)
Governed by 11_STAGE_11_FINAL_VALIDATION.md and NON_NEGOTIABLE_PRINCIPLES.md.

Manages and evaluates Indian EO data:
- Resourcesat-2 / 2A (LISS-IV 5.8m, AWiFS 56m)
- Cartosat-2 / 3 (High-Resolution Panchromatic & Multispectral)
- RISAT-1 / 1A (EOS-04 C-band Synthetic Aperture Radar)
- Bhuvan Services (ISRO Geo-Platform Web Map / Tile Services)

NON-NEGOTIABLE COMPLIANCE:
- Principle #11: "No claiming ground truth without a real reference label."
  Unless authoritative ground-truth labels are explicitly verified, data is strictly
  classified as UNANNOTATED_SENSOR_DATA or SENSOR_DERIVED_PROXY, never "ground truth".
- Principle #29: "Indian/ISRO relevance should supplement, not replace, independent benchmarks."
- Principle #30: "When evidence is missing, report 'not validated' instead of guessing."
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from pydantic import BaseModel, Field


class IndianEOSensor(str, Enum):
    """Indian Earth Observation satellite sensor platforms."""
    RESOURCESAT_LISS4 = "Resourcesat-2/2A LISS-IV (5.8m)"
    RESOURCESAT_AWIFS = "Resourcesat-2/2A AWiFS (56m)"
    CARTOSAT_PAN = "Cartosat-2/3 Panchromatic (0.28m-0.65m)"
    RISAT_SAR_CBAND = "RISAT-1/1A (EOS-04) C-Band SAR"
    BHUVAN_WMTS = "ISRO Bhuvan Geo-Platform Service"


class ReferenceLabelType(str, Enum):
    """Categorization of reference and ground truth labels."""
    AUTHORITATIVE_GROUND_TRUTH = "authoritative_ground_truth"
    SENSOR_DERIVED_PROXY = "sensor_derived_proxy"
    UNANNOTATED_SENSOR_DATA = "unannotated_sensor_data"
    NOT_VALIDATED = "not_validated"


class IndianEOScene(BaseModel):
    """Metadata specification for an Indian EO satellite scene."""
    scene_id: str
    sensor: IndianEOSensor
    acquisition_date: str
    region_name: str
    geographic_bounds: Tuple[float, float, float, float]  # (min_lon, min_lat, max_lon, max_lat)
    spatial_resolution_meters: float
    reference_type: ReferenceLabelType
    authoritative_source: Optional[str] = None
    crs: str = "EPSG:4326"
    channels: List[str] = Field(default_factory=list)

    def is_true_ground_truth(self) -> bool:
        """Returns True only if backed by verified authoritative reference labels."""
        return self.reference_type == ReferenceLabelType.AUTHORITATIVE_GROUND_TRUTH


class IndianEOCatalog:
    """Pre-registered catalog of canonical Indian EO reference scenes."""
    _CANONICAL_SCENES: Dict[str, IndianEOScene] = {
        "ISRO_HYD_LISS4_2023": IndianEOScene(
            scene_id="ISRO_HYD_LISS4_2023",
            sensor=IndianEOSensor.RESOURCESAT_LISS4,
            acquisition_date="2023-04-12",
            region_name="Hyderabad Urban Region, Telangana",
            geographic_bounds=(78.35, 17.30, 78.55, 17.50),
            spatial_resolution_meters=5.8,
            reference_type=ReferenceLabelType.UNANNOTATED_SENSOR_DATA,
            authoritative_source=None,
            crs="EPSG:4326",
            channels=["Green", "Red", "NIR"]
        ),
        "ISRO_MUM_RISAT1_2022": IndianEOScene(
            scene_id="ISRO_MUM_RISAT1_2022",
            sensor=IndianEOSensor.RISAT_SAR_CBAND,
            acquisition_date="2022-09-18",
            region_name="Mumbai Coastal & Creek, Maharashtra",
            geographic_bounds=(72.78, 18.88, 73.02, 19.15),
            spatial_resolution_meters=3.0,
            reference_type=ReferenceLabelType.UNANNOTATED_SENSOR_DATA,
            authoritative_source=None,
            crs="EPSG:4326",
            channels=["HH", "HV"]
        ),
        "ISRO_THAR_AWIFS_2023": IndianEOScene(
            scene_id="ISRO_THAR_AWIFS_2023",
            sensor=IndianEOSensor.RESOURCESAT_AWIFS,
            acquisition_date="2023-01-20",
            region_name="Thar Desert Arid Zone, Rajasthan",
            geographic_bounds=(70.50, 26.50, 72.00, 28.00),
            spatial_resolution_meters=56.0,
            reference_type=ReferenceLabelType.UNANNOTATED_SENSOR_DATA,
            authoritative_source=None,
            crs="EPSG:4326",
            channels=["Green", "Red", "NIR", "SWIR"]
        ),
        "NRSC_BHUVAN_URBAN_PROXY": IndianEOScene(
            scene_id="NRSC_BHUVAN_URBAN_PROXY",
            sensor=IndianEOSensor.BHUVAN_WMTS,
            acquisition_date="2023-11-05",
            region_name="Bengaluru Metropolitan, Karnataka",
            geographic_bounds=(77.50, 12.85, 77.75, 13.10),
            spatial_resolution_meters=2.5,
            reference_type=ReferenceLabelType.SENSOR_DERIVED_PROXY,
            authoritative_source="OpenStreetMap Building Polygon Derived Proxy",
            crs="EPSG:4326",
            channels=["Red", "Green", "Blue"]
        ),
    }

    @classmethod
    def get_scene(cls, scene_id: str) -> Optional[IndianEOScene]:
        return cls._CANONICAL_SCENES.get(scene_id)

    @classmethod
    def list_scenes(cls) -> List[IndianEOScene]:
        return list(cls._CANONICAL_SCENES.values())


class IndianEOValidationReport(BaseModel):
    """Comprehensive validation report for Indian Earth Observation data."""
    scene_id: str
    sensor: str
    reference_type: str
    authoritative_label_status: str
    geometric_sanity_pass: bool
    radiometric_sanity_pass: bool
    domain_shift_uncertainty_score: float
    spatial_consistency_score: float
    quality_summary: str
    disclaimer: str


class IndianEOValidator:
    """
    Validates Indian EO satellite rasters for geometric alignment, radiometric
    dynamic range, and model stability without falsely fabricating ground truth.
    """

    # Bounding envelope of Indian territory & territorial waters (approx):
    INDIA_BOUNDS = (68.0, 6.0, 98.0, 38.0)  # (min_lon, min_lat, max_lon, max_lat)

    @classmethod
    def validate_scene(
        cls,
        scene: IndianEOScene,
        raster_data: np.ndarray,
        model_predictions: Optional[np.ndarray] = None
    ) -> IndianEOValidationReport:
        """
        Validates an Indian EO scene raster and prediction consistency.
        Guarantees strict labeling: NEVER marks unannotated scenes as ground truth.
        """
        # 1. Geographic envelope check
        min_lon, min_lat, max_lon, max_lat = scene.geographic_bounds
        geom_pass = (
            min_lon >= cls.INDIA_BOUNDS[0] and
            max_lon <= cls.INDIA_BOUNDS[2] and
            min_lat >= cls.INDIA_BOUNDS[1] and
            max_lat <= cls.INDIA_BOUNDS[3] and
            min_lon < max_lon and
            min_lat < max_lat
        )

        # 2. Radiometric check
        # Raster should not be constant, should not be all-zeros or saturated
        radio_pass = False
        if raster_data is not None and raster_data.size > 0:
            std_dev = float(np.std(raster_data))
            zero_ratio = float(np.mean(raster_data == 0))
            # Healthy remote sensing data has variance and isn't >90% nodata
            radio_pass = (std_dev > 1e-4) and (zero_ratio < 0.90)

        # 3. Domain-shift uncertainty score
        # When evaluating foreign-trained models on Indian terrain, predict entropy
        domain_shift_score = 0.0
        if model_predictions is not None and model_predictions.size > 0:
            # Normalized Shannon entropy
            probs = np.clip(model_predictions, 1e-6, 1.0 - 1e-6)
            if probs.ndim > 1 and probs.shape[-1] > 1:
                entropy = -np.sum(probs * np.log(probs), axis=-1)
                domain_shift_score = float(np.mean(entropy) / np.log(probs.shape[-1]))
            else:
                p = np.clip(probs, 1e-6, 1.0 - 1e-6)
                binary_entropy = -(p * np.log2(p) + (1 - p) * np.log2(1 - p))
                domain_shift_score = float(np.mean(binary_entropy))

        # 4. Spatial consistency score (local spatial gradient smoothness)
        spatial_consistency = 0.0
        if raster_data is not None and raster_data.ndim >= 2:
            grad_x = np.diff(raster_data, axis=-1)
            spatial_consistency = float(np.clip(1.0 / (1.0 + np.mean(np.abs(grad_x))), 0.0, 1.0))

        # Ground truth status wording
        if scene.reference_type == ReferenceLabelType.AUTHORITATIVE_GROUND_TRUTH:
            label_status = f"Verified Ground Truth: {scene.authoritative_source}"
        elif scene.reference_type == ReferenceLabelType.SENSOR_DERIVED_PROXY:
            label_status = f"Sensor-Derived Proxy (Not authoritative ground truth): {scene.authoritative_source}"
        else:
            label_status = "Unannotated Sensor Imagery (No ground truth claimed)"

        disclaimer = (
            "NOTICE (NON-NEGOTIABLE SCIENTIFIC INTEGRITY): "
            "Evaluated on Indian Earth Observation rasters. In accordance with TRINETRA non-negotiable "
            "principles, unannotated data is analyzed for physical/geometric consistency and model stability, "
            "and is strictly NOT labeled as authoritative ground truth."
        )

        quality_summary = (
            f"Sensor {scene.sensor.value} validated over {scene.region_name}. "
            f"Geometric bounds pass: {geom_pass}. Radiometric profile pass: {radio_pass}."
        )

        return IndianEOValidationReport(
            scene_id=scene.scene_id,
            sensor=scene.sensor.value,
            reference_type=scene.reference_type.value,
            authoritative_label_status=label_status,
            geometric_sanity_pass=geom_pass,
            radiometric_sanity_pass=radio_pass,
            domain_shift_uncertainty_score=round(domain_shift_score, 4),
            spatial_consistency_score=round(spatial_consistency, 4),
            quality_summary=quality_summary,
            disclaimer=disclaimer
        )
