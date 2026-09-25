/**
 * TRINETRA / Shanetra Explore Architecture
 * Copernicus-Style Multi-Spectral Presets Definition
 * High-significance satellite band combinations & scientific indices.
 */

export interface SpectralPreset {
  id: string
  label: string
  shortLabel: string
  bands: string
  description: string
  tileUrl: string
  attribution: string
  colorAccent: string
  badgeText: string
  maxZoom?: number
  legend?: {
    low: string
    high: string
    lowColor: string
    highColor: string
    description: string
  }
}

export const SPECTRAL_PRESETS: SpectralPreset[] = [
  {
    id: "satellite",
    label: "True Color (High-Res)",
    shortLabel: "True Color",
    bands: "RGB Natural Optical",
    description: "Sub-meter high-resolution Earth photography from commercial optical satellites (Maxar / Vantor). Captures visible light as perceived by the human eye.",
    tileUrl: "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: "Powered by Esri — Maxar, Earthstar Geographics",
    colorAccent: "#38bdf8",
    badgeText: "0.34m OPTICAL",
    maxZoom: 19,
  },
  {
    id: "sentinel2-cloudless",
    label: "Sentinel-2 Cloudless",
    shortLabel: "Sentinel-2",
    bands: "B04 (Red), B03 (Green), B02 (Blue)",
    description: "Copernicus 10-meter global cloud-free optical composite from the European Space Agency. Optimized for macro regional observation and land cover analysis.",
    tileUrl: "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg",
    attribution: "Copernicus Sentinel-2 / EOX IT Services GmbH",
    colorAccent: "#06b6d4",
    badgeText: "10m COPERNICUS",
    maxZoom: 18,
  },
  {
    id: "ndvi-vegetation",
    label: "NDVI (Vegetation Index)",
    shortLabel: "NDVI",
    bands: "(NIR - Red) / (NIR + Red)",
    description: "Normalized Difference Vegetation Index. Quantifies photosynthetic activity, crop health, forest canopy density, and drought severity.",
    tileUrl: "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_NDVI_8Day/default/default/GoogleMapsCompatible_Level9/{z}/{y}/{x}.png",
    attribution: "NASA GIBS / EOSDIS MODIS Terra NDVI",
    colorAccent: "#22c55e",
    badgeText: "CHLOROPHYLL INDEX",
    maxZoom: 9,
    legend: {
      low: "Barren / Desert (0.0)",
      high: "Dense Canopy (0.8+)",
      lowColor: "#b45309",
      highColor: "#15803d",
      description: "Brown = Barren/dry rock; Light Green = Grassland/Shrub; Dark Green = Lush forest/agriculture.",
    },
  },
  {
    id: "false-color-swir",
    label: "False Color SWIR (Burn Scars & Haze)",
    shortLabel: "SWIR / Fire",
    bands: "Bands 7-2-1 (SWIR-2, NIR, Red)",
    description: "Shortwave Infrared false color composite. Penetrates atmospheric smoke, fog, and haze. Wildfire burn scars appear brick red, active fires glow orange, healthy crops appear neon green.",
    tileUrl: "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_Bands721/default/default/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg",
    attribution: "NASA GIBS / EOSDIS MODIS Bands 7-2-1",
    colorAccent: "#f43f5e",
    badgeText: "HAZE / BURN SCARS",
    maxZoom: 9,
    legend: {
      low: "Burnt / Urban (Red)",
      high: "Vigorous Crops (Green)",
      lowColor: "#ef4444",
      highColor: "#10b981",
      description: "Red = Burnt land & urban cores; Green = Dense foliage; Dark Blue/Black = Water bodies.",
    },
  },
  {
    id: "viirs-night",
    label: "Nighttime Lights (VIIRS)",
    shortLabel: "Night Lights",
    bands: "Day/Night Band (DNB 500-900nm)",
    description: "Measures nocturnal artificial light emissions, mapping urban electrification grids, industrial hubs, gas flares, and nighttime human activity across the globe.",
    tileUrl: "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_SNPP_DayNightBand_ENCC/default/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpg",
    attribution: "NASA GIBS / Suomi NPP VIIRS DNB",
    colorAccent: "#c084fc",
    badgeText: "POWER GRID / NIGHT",
    maxZoom: 8,
  },
]
