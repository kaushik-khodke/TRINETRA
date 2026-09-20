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

// Fast, reliable raster basemap tiles for MapLibre GL (Zero API key / zero watermark)
export const DEFAULT_2D_BASEMAP_STYLE = {
  version: 8,
  sources: {
    "esri-dark": {
      type: "raster",
      tiles: [
        "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
      ],
      tileSize: 256,
      attribution: '&copy; <a href="https://www.esri.com/">Esri</a> &copy; <a href="https://openstreetmap.org">OpenStreetMap contributors</a>',
    },
  },
  layers: [
    {
      id: "esri-dark-layer",
      type: "raster",
      source: "esri-dark",
      minzoom: 0,
      maxzoom: 20,
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
