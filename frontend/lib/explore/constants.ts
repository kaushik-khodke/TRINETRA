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
    label: "Esri World Satellite (High-Res)",
    shortLabel: "SAT",
    tileUrl: "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: "Powered by Esri — Source: Esri, Maxar, Earthstar Geographics",
    minZoom: 0,
    maxZoom: 19,
    description: "Sub-meter authentic optical satellite photography of the entire globe down to building level.",
  },
  "sentinel2-cloudless": {
    id: "sentinel2-cloudless",
    label: "Sentinel-2 Cloudless (Copernicus 10m)",
    shortLabel: "S2",
    tileUrl: "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2024_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg",
    attribution: "Sentinel-2 cloudless 2024 by EOX IT Services GmbH (Contains modified Copernicus Sentinel data)",
    minZoom: 0,
    maxZoom: 18,
    description: "Copernicus 10m global cloud-free optical composite.",
  },
  osm: {
    id: "osm",
    label: "OpenStreetMap Streets",
    shortLabel: "OSM",
    tileUrl: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: "© OpenStreetMap contributors",
    minZoom: 0,
    maxZoom: 19,
    description: "Global street-level cartographic and navigation basemap.",
  },
  "carto-dark": {
    id: "carto-dark",
    label: "Tactical Dark Matter",
    shortLabel: "DARK",
    tileUrl: "https://a.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png",
    attribution: "© CartoDB / © OpenStreetMap contributors",
    minZoom: 0,
    maxZoom: 19,
    description: "High-contrast dark cartographic basemap optimized for tactical night exploration.",
  },
  "esri-topo": {
    id: "esri-topo",
    label: "Esri World Topographic",
    shortLabel: "TOPO",
    tileUrl: "https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
    attribution: "Powered by Esri — Sources: Esri, HERE, Garmin, Intermap, USGS",
    minZoom: 0,
    maxZoom: 19,
    description: "Detailed topographic map with physical terrain relief and elevation contours.",
  },
  "carto-light": {
    id: "carto-light",
    label: "Positron Light Cartography",
    shortLabel: "LIGHT",
    tileUrl: "https://a.basemaps.cartocdn.com/rastertiles/light_all/{z}/{x}/{y}.png",
    attribution: "© CartoDB / © OpenStreetMap contributors",
    minZoom: 0,
    maxZoom: 19,
    description: "Clean, high-visibility light cartographic basemap.",
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
