"""
TRINETRA Workstation — Versioned Pipeline Registry
Loads allowlisted analytical pipeline contracts matching implementation-package/examples/pipeline-registry.json.
"""

from typing import Dict, List, Optional
from .schemas import PipelineDefinition


PIPELINE_REGISTRY: Dict[str, PipelineDefinition] = {
    "optical_change": PipelineDefinition(
        key="optical_change",
        version="1.0.0",
        label="Optical Surface & Vegetation Change Detection",
        description="Bi-temporal spectral difference analysis with cloud masking, calibrated index thresholding, and zonal change area accounting.",
        supportedCollections=["sentinel-2-l2a", "user-multispectral", "user-upload", "user-raster", "landsat-8-9"],
        requiredBands=["red", "nir"],
        inputRoles=["before_scene", "after_scene", "optional_mask"],
        outputTypes=["raster", "table", "report"],
        parameterBounds={
            "index": ["NDVI", "NDWI", "NDBI", "SAVI", "NBR"],
            "threshold": {"min": -1.0, "max": 1.0, "default": 0.2},
            "cloudMask": ["s2cloudless", "qa60", "provided_mask", "none"],
            "resampling": ["nearest", "bilinear"],
        },
        scientificNotes=[
            "Sentinel-2 Level-2A surface reflectance required for normalized indices.",
            "Pixel values are masked using S2Cloudless probability maps (>40% mask).",
            "Spectral difference does not establish human vs natural causality.",
        ],
    ),
    "sar_change": PipelineDefinition(
        key="sar_change",
        version="1.0.0",
        label="SAR Coherent Backscatter Change Detection",
        description="All-weather microwave backscatter anomaly detection comparing calibrated Sentinel-1 GRD sigma0 decibel deltas.",
        supportedCollections=["sentinel-1-grd", "user-sar", "user-upload", "user-raster"],
        requiredBands=["VV"],
        inputRoles=["before_scene", "after_scene"],
        outputTypes=["raster", "table", "report"],
        parameterBounds={
            "polarization": ["VV", "VH", "cross_ratio"],
            "thresholdDb": {"min": -30.0, "max": 30.0, "default": -3.0},
            "resampling": ["nearest", "bilinear"],
        },
        scientificNotes=[
            "Radiometrically terrain-corrected gamma0/sigma0 recommended.",
            "Identical orbit track/pass direction required to prevent look-angle bias.",
        ],
    ),
    "rgb_false_color": PipelineDefinition(
        key="rgb_false_color",
        version="1.0.0",
        label="Multispectral RGB & False-Color Compositing",
        description="Dynamic radiometric stretch and band synthesis for visual feature identification and false-color NIR vegetation inspection.",
        supportedCollections=["sentinel-2-l2a", "user-multispectral", "user-upload", "user-raster"],
        requiredBands=["red", "green", "blue"],
        inputRoles=["source_scene"],
        outputTypes=["raster", "thumbnail"],
        parameterBounds={
            "composition": ["TrueColor_RGB", "ColorInfrared_NIR_R_G", "Agriculture_SWIR_NIR_B", "Geology_SWIR2_SWIR1_B"],
            "resampling": ["nearest", "bilinear"],
            "stretch": ["2_percent_linear", "equalize", "gamma"],
        },
        scientificNotes=[
            "Color infrared composites clearly discriminate active photosynthetic tissue from dry soil.",
        ],
    ),
    "multispectral_fusion": PipelineDefinition(
        key="multispectral_fusion",
        version="1.0.0",
        label="Optical-SAR Multimodal Fusion & Feature Inference",
        description="Joint fusion of optical spectral response with microwave surface roughness for robust land-cover event grounding.",
        supportedCollections=["sentinel-2-l2a", "sentinel-1-grd", "user-multispectral", "user-upload", "user-raster"],
        requiredBands=["red", "green", "blue", "nir", "VV"],
        inputRoles=["optical_scene", "sar_scene", "optional_boundary"],
        outputTypes=["raster", "table", "report"],
        parameterBounds={
            "fusionMethod": ["brovey", "pca", "wavelet", "deep_learned"],
            "resampling": ["bilinear"],
        },
        scientificNotes=[
            "Combines cloud-free optical reflection with radar structural geometry using trained optical_sar_model checkpoint.",
        ],
    ),
    "optical_single_index": PipelineDefinition(
        key="optical_single_index",
        version="1.0.0",
        label="Single-Scene Spectral Index & Coverage Analysis",
        description="Calculates exact physical surface index coverage (NDWI water, NDVI canopy, NDBI urban) for a single observation inside the AOI.",
        supportedCollections=["sentinel-2-l2a", "user-multispectral", "user-upload", "user-raster", "landsat-8-9"],
        requiredBands=["red", "green", "blue"],
        inputRoles=["target_scene"],
        outputTypes=["raster", "table", "report"],
        parameterBounds={
            "index": ["NDWI", "NDVI", "NDBI", "SAVI"],
            "threshold": {"min": -1.0, "max": 1.0, "default": 0.0},
            "cloudMask": ["s2cloudless", "qa60", "none"],
        },
        scientificNotes=[
            "Directly answers instantaneous state questions (e.g. water percentage or forest canopy) within the target AOI.",
            "Water mask uses standard McFeeters/Gao NDWI zero-threshold (NDWI > 0.0).",
        ],
    ),
    "ai_vqa": PipelineDefinition(
        key="ai_vqa",
        version="1.0.0",
        label="AI Visual Question Answering (RS-VQA)",
        description="Answers complex natural domain questions about satellite imagery using the trained RS-VQA Multimodal Bilinear checkpoint.",
        supportedCollections=["sentinel-2-l2a", "user-multispectral", "user-upload", "user-raster"],
        requiredBands=["red", "green", "blue"],
        inputRoles=["target_scene"],
        outputTypes=["table", "report"],
        parameterBounds={
            "confidenceThreshold": {"min": 0.1, "max": 0.9, "default": 0.5},
        },
        scientificNotes=[
            "Executes neural forward pass on backend/models/checkpoints/rs_vqa_model/model.pt.",
            "Combines spatial feature map extraction with cryptographic token embeddings.",
        ],
    ),
    "ai_grounding": PipelineDefinition(
        key="ai_grounding",
        version="1.0.0",
        label="Text-Guided Tactical Grounding (RS-Grounding)",
        description="Detects and highlights bounding box contours of specific objects or features described in text queries using rs_grounding_model.",
        supportedCollections=["sentinel-2-l2a", "user-multispectral", "user-upload", "user-raster"],
        requiredBands=["red", "green", "blue"],
        inputRoles=["target_scene"],
        outputTypes=["vector", "table", "report"],
        parameterBounds={
            "nmsThreshold": {"min": 0.1, "max": 0.9, "default": 0.45},
            "minConfidence": {"min": 0.1, "max": 0.9, "default": 0.35},
        },
        scientificNotes=[
            "Extracts tactical GeoJSON bounding box overlays anchored to ground coordinates.",
            "Runs on backend/models/checkpoints/rs_grounding_model/model.pt.",
        ],
    ),
    "ai_neural_change": PipelineDefinition(
        key="ai_neural_change",
        version="1.0.0",
        label="Deep Learning Siamese Change Detection",
        description="Bi-temporal deep learning change detection using Siamese Differential Convolutional Net to identify structural alterations.",
        supportedCollections=["sentinel-2-l2a", "user-multispectral", "user-upload", "user-raster"],
        requiredBands=["red", "green", "blue"],
        inputRoles=["before_scene", "after_scene"],
        outputTypes=["raster", "table", "report"],
        parameterBounds={
            "probabilityThreshold": {"min": 0.1, "max": 0.9, "default": 0.5},
        },
        scientificNotes=[
            "Detects structural, building, and road changes using backend/models/checkpoints/change_specialist_model/model.pt.",
            "Robust against seasonal illumination and agricultural false positives.",
        ],
    ),
    "hyperspectral_spectroscopy": PipelineDefinition(
        key="hyperspectral_spectroscopy",
        version="1.0.0",
        label="Hyperspectral 200-Band Cube Spectroscopy",
        description="Full 3D spectral cube spectroscopy extracting continuous spectral absorption dips using HyperFree-B foundation specialist.",
        supportedCollections=["user-hyperspectral", "user-upload", "user-raster"],
        requiredBands=["bands_all"],
        inputRoles=["target_scene"],
        outputTypes=["table", "report"],
        parameterBounds={
            "spectralRange": ["400-2500nm", "VNIR", "SWIR"],
        },
        scientificNotes=[
            "Runs on backend/models/checkpoints/hyperfree_model/model.pt foundation checkpoint.",
        ],
    ),
}


def get_pipeline(pipeline_key: str) -> Optional[PipelineDefinition]:
    return PIPELINE_REGISTRY.get(pipeline_key)


def list_pipelines() -> List[PipelineDefinition]:
    return list(PIPELINE_REGISTRY.values())
