/**
 * TRINETRA Workstation — Scientific Analysis Library & Formula Registry
 * Formal Earth Observation spectral specifications matching copilot-prompt-and-validation.md.
 */

export interface AnalysisRecipe {
  id: string
  name: string
  category: "optical" | "sar" | "fusion"
  subtitle: string
  pipelineKey: string
  indexKey?: string
  sensor: string
  formula: string
  bandsRequired: string[]
  recommendedThreshold: number
  recommendedCloudMask: string
  recommendedResampling: string
  validRange: [number, number]
  physicsTheory: string
  bestFor: string
  limitations: string
}

export const ANALYSIS_LIBRARY_RECIPES: AnalysisRecipe[] = [
  {
    id: "ndwi_flood",
    name: "NDWI Surface Inundation & Flood Extent",
    category: "optical",
    subtitle: "Gao & McFeeters Normalised Difference Water Index",
    pipelineKey: "optical_change",
    indexKey: "NDWI",
    sensor: "Sentinel-2 MSI (B03, B08) / Landsat-8/9 (B03, B05)",
    formula: "(B03_Green - B08_NIR) / (B03_Green + B08_NIR)",
    bandsRequired: ["Green (560nm)", "NIR (842nm)"],
    recommendedThreshold: 0.20,
    recommendedCloudMask: "s2cloudless",
    recommendedResampling: "bilinear",
    validRange: [-1.0, 1.0],
    physicsTheory:
      "Exploits peak reflectance of liquid surface water in green spectral wavelengths (560 nm) and near-total absorption in the near-infrared spectrum (842 nm). Positive values delineate standing water boundaries.",
    bestFor: "River basin expansion, dam monitoring, flood inundation mapping, and wetland boundary tracking.",
    limitations: "Can confuse dark asphalt and deep mountain terrain shadows with shallow water in low-sun angles.",
  },
  {
    id: "ndvi_vegetation",
    name: "NDVI Canopy Health & Biomass Alteration",
    category: "optical",
    subtitle: "Rouse Normalized Difference Vegetation Index",
    pipelineKey: "optical_change",
    indexKey: "NDVI",
    sensor: "Sentinel-2 MSI (B04, B08) / Landsat-8/9 (B04, B05)",
    formula: "(B08_NIR - B04_Red) / (B08_NIR + B04_Red)",
    bandsRequired: ["Red (665nm)", "NIR (842nm)"],
    recommendedThreshold: 0.20,
    recommendedCloudMask: "s2cloudless",
    recommendedResampling: "bilinear",
    validRange: [-1.0, 1.0],
    physicsTheory:
      "Chlorophyll pigments strongly absorb red solar radiation for photosynthesis, while spongy mesophyll leaf tissue scatters and reflects near-infrared radiation. Significant drops in NDVI signal canopy loss or drought stress.",
    bestFor: "Deforestation monitoring, agricultural harvest verification, forest fire burn scars, and drought tracking.",
    limitations: "Saturates at dense, multi-layered forest canopies (LAI > 3) and is sensitive to soil background reflectance in arid zones.",
  },
  {
    id: "ndbi_urban",
    name: "NDBI Impervious Surface & Urban Expansion",
    category: "optical",
    subtitle: "Normalized Difference Built-Up Index",
    pipelineKey: "optical_change",
    indexKey: "NDBI",
    sensor: "Sentinel-2 MSI (B11 SWIR, B08 NIR)",
    formula: "(B11_SWIR - B08_NIR) / (B11_SWIR + B08_NIR)",
    bandsRequired: ["NIR (842nm)", "SWIR-1 (1610nm)"],
    recommendedThreshold: 0.15,
    recommendedCloudMask: "s2cloudless",
    recommendedResampling: "bilinear",
    validRange: [-1.0, 1.0],
    physicsTheory:
      "Constructed infrastructure materials (concrete, masonry, asphalt) exhibit higher reflectance in shortwave infrared (1610 nm) than in the near-infrared, separating built-up surfaces from vegetated and aquatic landcover.",
    bestFor: "Unauthorized construction detection, urban perimeter growth, industrial encroachment, and post-disaster debris tracking.",
    limitations: "Bare dry soil and exposed barren rock can produce spectral signatures overlapping with concrete.",
  },
  {
    id: "savi_arid",
    name: "SAVI Soil-Adjusted Vegetation Dynamics",
    category: "optical",
    subtitle: "Huete Soil-Adjusted Vegetation Index (L=0.5)",
    pipelineKey: "optical_change",
    indexKey: "SAVI",
    sensor: "Sentinel-2 MSI (B04, B08)",
    formula: "((B08_NIR - B04_Red) / (B08_NIR + B04_Red + 0.5)) * 1.5",
    bandsRequired: ["Red (665nm)", "NIR (842nm)"],
    recommendedThreshold: 0.18,
    recommendedCloudMask: "s2cloudless",
    recommendedResampling: "bilinear",
    validRange: [-1.0, 1.0],
    physicsTheory:
      "Introduces an empirical canopy background adjustment factor (L = 0.5) into the NDVI equation to cancel first-order soil brightness variability in arid or semi-arid rangelands.",
    bestFor: "Desertification tracking, semi-arid agriculture, scrubland monitoring, and sparse vegetation phenology.",
    limitations: "Less sensitive in dense vegetation zones where L factor reduces dynamic contrast range.",
  },
  {
    id: "sar_sigma0_flood",
    name: "SAR Coherent Backscatter Sigma0 Anomaly",
    category: "sar",
    subtitle: "Sentinel-1 GRD All-Weather Microwave Delta",
    pipelineKey: "sar_change",
    indexKey: "VV",
    sensor: "Sentinel-1 C-Band SAR (5.405 GHz)",
    formula: "10 * log10(σ0_target) - 10 * log10(σ0_baseline)",
    bandsRequired: ["VV Backscatter Amplitude"],
    recommendedThreshold: -3.0,
    recommendedCloudMask: "none",
    recommendedResampling: "bilinear",
    validRange: [-30.0, 30.0],
    physicsTheory:
      "C-Band microwave pulses penetrate cloud decks and precipitation. Smooth standing water acts as a specular reflector, bouncing radar energy away from the sensor and causing an acute backscatter drop (> 3 dB drop).",
    bestFor: "Monsoon floods under overcast cloud cover, cyclone impact assessment, maritime oil slicks, and night observations.",
    limitations: "High surface winds create capillary waves that roughen water surfaces, artificially raising radar backscatter.",
  },
  {
    id: "optical_sar_fusion",
    name: "Optical + SAR Dual-Sensor Confirmation",
    category: "fusion",
    subtitle: "Multimodal Cross-Sensor Inundation Fusion",
    pipelineKey: "multispectral_fusion",
    indexKey: "NDWI",
    sensor: "Sentinel-2 Optical (MSI) + Sentinel-1 Microwave (SAR)",
    formula: "(NDWI_target >= 0.20) ∧ (Δσ0_SAR <= -2.5 dB)",
    bandsRequired: ["S2 Green", "S2 NIR", "S1 VV"],
    recommendedThreshold: 0.20,
    recommendedCloudMask: "s2cloudless",
    recommendedResampling: "bilinear",
    validRange: [-1.0, 1.0],
    physicsTheory:
      "Combines spectral absorption signatures in optical bands with microwave surface roughness attenuation in radar backscatter. Fusing modalities eliminates cloud shadow false-positives and specular ambiguity.",
    bestFor: "High-consequence disaster response, insurance claim verification, and sovereign defense surveillance.",
    limitations: "Requires near-coincident temporal acquisitions (< 3 days) between optical and radar satellite passes.",
  },
]
