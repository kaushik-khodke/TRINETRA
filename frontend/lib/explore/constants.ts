/**
 * TRINETRA / Shanetra Explore Architecture
 * System Constants & Centralized Configuration
 * Phase 1 Foundation
 */

import { ExploreViewMode, GlobeCameraState } from "./types"

// Default Center: Geographic Center of India (Nagpur / Central Subcontinent)
export const DEFAULT_CAMERA_STATE: GlobeCameraState = {
  latitude: 21.1458,
  longitude: 79.0882,
  zoom: 4.8,
  heading: 0,
  pitch: -90, // Nadir down in 2D, tilted in 3D
  roll: 0,
}

export const ISRO_HQ_LOCATION: GlobeCameraState = {
  latitude: 12.9716,
  longitude: 77.5946,
  zoom: 11.5,
  heading: 0,
  pitch: -45,
}

export const SUPPORTED_VIEW_MODES: ExploreViewMode[] = ["2d", "3d"]

export const SIDEBAR_WIDTH_PX = 320
export const COLLAPSED_SIDEBAR_WIDTH_PX = 0

// Canonical Basemap Presets & Globe Sources
export interface BasemapPreset {
  id: string
  label: string
  shortLabel: string
  tileUrl: string
  attribution: string
  minZoom?: number
  maxZoom?: number
  description: string
  requiresKey?: boolean
  keyType?: "cesium" | "google"
}

export const BASEMAP_PRESETS: Record<string, BasemapPreset> = {
  satellite: {
    id: "satellite",
    label: "Esri World Satellite",
    shortLabel: "SAT",
    tileUrl: "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: "Powered by Esri — Source: Esri, Maxar, Earthstar Geographics",
    minZoom: 0,
    maxZoom: 19,
    description: "Keyless high-resolution true-color Earth photography.",
  },
  "sentinel2-cloudless": {
    id: "sentinel2-cloudless",
    label: "Sentinel-2 Cloudless",
    shortLabel: "S2",
    tileUrl: "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg",
    attribution: "Sentinel-2 cloudless by EOX IT Services GmbH (Contains modified Copernicus Sentinel data)",
    minZoom: 0,
    maxZoom: 18,
    description: "Copernicus 10m global cloud-free optical composite.",
  },
  "ndvi-vegetation": {
    id: "ndvi-vegetation",
    label: "NDVI Vegetation Index",
    shortLabel: "NDVI",
    tileUrl: "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_NDVI_8Day/default/default/GoogleMapsCompatible_Level9/{z}/{y}/{x}.png",
    attribution: "NASA GIBS / EOSDIS MODIS Terra NDVI",
    minZoom: 0,
    maxZoom: 9,
    description: "Normalized Difference Vegetation Index tracking vegetation health, crop chlorophyll, and green biomass.",
  },
  "false-color-swir": {
    id: "false-color-swir",
    label: "False Color SWIR (Fire & Haze)",
    shortLabel: "SWIR",
    tileUrl: "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_Bands721/default/default/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg",
    attribution: "NASA GIBS / EOSDIS MODIS Bands 7-2-1",
    minZoom: 0,
    maxZoom: 9,
    description: "Shortwave Infrared false color composite penetrating smoke and atmospheric haze.",
  },
  "viirs-night": {
    id: "viirs-night",
    label: "VIIRS Nighttime Lights",
    shortLabel: "Night",
    tileUrl: "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_SNPP_DayNightBand_ENCC/default/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpg",
    attribution: "NASA GIBS / Suomi NPP VIIRS DNB",
    minZoom: 0,
    maxZoom: 8,
    description: "Nocturnal light emissions mapping human activity, electrical power grids, and nighttime features.",
  },
  "sentinel1-radar": {
    id: "sentinel1-radar",
    label: "Sentinel-1 SAR Radar",
    shortLabel: "SAR",
    tileUrl: "https://tiles.maps.eox.at/wmts/1.0.0/s1_2020_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg",
    attribution: "Sentinel-1 SAR 2020 by EOX IT Services GmbH (Contains modified Copernicus Sentinel data)",
    minZoom: 0,
    maxZoom: 18,
    description: "All-weather cloud-penetrating synthetic aperture radar backscatter.",
  },
  "nasa-viirs": {
    id: "nasa-viirs",
    label: "NASA GIBS VIIRS True Color",
    shortLabel: "NASA",
    tileUrl: "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_SNPP_CorrectedReflectance_TrueColor/default/default/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg",
    attribution: "NASA GIBS / EOSDIS",
    minZoom: 0,
    maxZoom: 9,
    description: "Daily corrected reflectance global composite.",
  },
  osm: {
    id: "osm",
    label: "OpenStreetMap Cartographic",
    shortLabel: "OSM",
    tileUrl: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: "© OpenStreetMap contributors",
    minZoom: 0,
    maxZoom: 19,
    description: "Detailed street and topographic cartographic base.",
  },
  "google-3d": {
    id: "google-3d",
    label: "Google Photorealistic 3D",
    shortLabel: "3D",
    tileUrl: "",
    attribution: "Google / Cesium Ion",
    description: "Cinematic 3D photorealistic mesh tileset (requires Google or Ion key).",
    requiresKey: true,
    keyType: "google",
  },
}

export const REEARTH_TERRAIN_URL = "https://terrain.reearth.land/cesium-mesh/ellipsoid"
export const BORDERS_OVERLAY_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"

// Authentic satellite imagery basemap for MapLibre GL (Zero API key / sub-meter resolution)
export const DEFAULT_2D_BASEMAP_STYLE = {
  version: 8,
  sources: {
    "esri-satellite": {
      type: "raster",
      tiles: [
        "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      ],
      tileSize: 256,
      attribution: "Powered by Esri — Source: Esri, Maxar, Earthstar Geographics",
      maxzoom: 18,
    },
  },
  layers: [
    {
      id: "esri-satellite-layer",
      type: "raster",
      source: "esri-satellite",
      minzoom: 0,
      maxzoom: 22,
    },
  ],
}

// Performance thresholds
export const PERFORMANCE_THRESHOLDS = {
  targetFps: 60,
  warningFps: 30,
  maxInitTimeMs: 2500,
  maxModeSwitchTimeMs: 800,
}
