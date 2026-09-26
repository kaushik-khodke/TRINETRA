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
    label: "True Color (High-Res Optical)",
    shortLabel: "True Color",
    bands: "RGB Natural Optical",
    description: "Sub-meter high-resolution Earth photography from commercial optical satellites (Maxar / Vantor). Captures true ground photography down to individual buildings.",
    tileUrl: "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: "Powered by Esri — Maxar, Earthstar Geographics",
    colorAccent: "#38bdf8",
    badgeText: "0.34m OPTICAL",
    maxZoom: 19,
  },
  {
    id: "sentinel2-cloudless",
    label: "Sentinel-2 Cloudless (Copernicus 10m)",
    shortLabel: "Sentinel-2",
    bands: "B04 (Red), B03 (Green), B02 (Blue)",
    description: "Copernicus 10-meter global cloud-free optical composite from the European Space Agency. Authentic, seamless global imagery.",
    tileUrl: "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2024_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg",
    attribution: "Copernicus Sentinel-2 / EOX IT Services GmbH",
    colorAccent: "#06b6d4",
    badgeText: "10m COPERNICUS",
    maxZoom: 18,
  },
  {
    id: "carto-dark",
    label: "Tactical Dark Matter",
    shortLabel: "Dark Base",
    bands: "High-Contrast Night Vector",
    description: "High-contrast dark cartographic basemap designed for tactical night observation and satellite feature tracking down to street level.",
    tileUrl: "https://a.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png",
    attribution: "© CartoDB / © OpenStreetMap",
    colorAccent: "#818cf8",
    badgeText: "STREET LEVEL",
    maxZoom: 19,
  },
  {
    id: "osm",
    label: "OpenStreetMap Streets & Citites",
    shortLabel: "Streets",
    bands: "Standard Cartographic Vector",
    description: "Global open street, road, building footprint, and civil infrastructure basemap.",
    tileUrl: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: "© OpenStreetMap contributors",
    colorAccent: "#34d399",
    badgeText: "VECTOR STREETS",
    maxZoom: 19,
  },
  {
    id: "esri-topo",
    label: "Topographic & Elevation Relief",
    shortLabel: "Topographic",
    bands: "USGS / Natural Earth Terrain",
    description: "Detailed topographic map with physical terrain relief, elevation contours, water networks, and landmarks.",
    tileUrl: "https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
    attribution: "Powered by Esri — USGS, Garmin",
    colorAccent: "#fb923c",
    badgeText: "TERRAIN RELIEF",
    maxZoom: 19,
  },
]
