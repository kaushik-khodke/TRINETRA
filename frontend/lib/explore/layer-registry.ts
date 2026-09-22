/**
 * TRINETRA / Shanetra Explore Architecture
 * Layer Registry — Canonical Source of Truth for Exploration Layers
 * Phase 2: Dynamic layer registration, raster tile templates, and opacity tracking.
 */

import { ExploreLayerDefinition } from "./types"

export const INITIAL_LAYER_REGISTRY: ExploreLayerDefinition[] = [
  {
    id: "layer-base-satellite",
    label: "Esri World Satellite (Default)",
    category: "base",
    rendererSupport: ["2d", "3d"],
    sourceType: "raster",
    tileTemplate: "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    defaultVisible: true,
    userControllable: true,
    aiControllable: false,
    expensive: false,
    opacity: 1.0,
    description: "Sub-meter high-resolution real Earth optical satellite photography.",
    attribution: "Powered by Esri — Maxar, Earthstar Geographics",
  },
  {
    id: "layer-sentinel2-cloudless",
    label: "Sentinel-2 Cloudless (Copernicus 10m)",
    category: "imagery",
    rendererSupport: ["2d", "3d"],
    sourceType: "raster",
    tileTemplate: "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2021_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg",
    minZoom: 0,
    maxZoom: 18,
    defaultVisible: false,
    userControllable: true,
    aiControllable: true,
    expensive: false,
    opacity: 1.0,
    description: "Global cloudless optical composite from Copernicus Sentinel-2.",
    attribution: "Copernicus Sentinel-2 / EOX IT Services GmbH",
  },
  {
    id: "layer-sentinel1-radar",
    label: "Sentinel-1 SAR Radar (All-Weather Mosaic)",
    category: "imagery",
    rendererSupport: ["2d", "3d"],
    sourceType: "raster",
    tileTemplate: "https://tiles.maps.eox.at/wmts/1.0.0/s1_2020_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg",
    minZoom: 0,
    maxZoom: 18,
    defaultVisible: false,
    userControllable: true,
    aiControllable: true,
    expensive: false,
    opacity: 1.0,
    description: "C-band synthetic aperture radar backscatter mosaic penetrating clouds and night.",
    attribution: "Copernicus Sentinel-1 / EOX IT Services GmbH",
  },
  {
    id: "layer-nasa-viirs",
    label: "NASA GIBS VIIRS True Color",
    category: "imagery",
    rendererSupport: ["2d", "3d"],
    sourceType: "raster",
    tileTemplate: "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_SNPP_CorrectedReflectance_TrueColor/default/default/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg",
    minZoom: 0,
    maxZoom: 9,
    defaultVisible: false,
    userControllable: true,
    aiControllable: true,
    expensive: false,
    opacity: 1.0,
    description: "Daily corrected reflectance global satellite imagery from Suomi NPP VIIRS.",
    attribution: "NASA Global Imagery Browse Services (GIBS)",
  },
  {
    id: "layer-borders",
    label: "Political Boundaries & Labels",
    category: "system",
    rendererSupport: ["2d", "3d"],
    sourceType: "raster",
    tileTemplate: "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
    minZoom: 1,
    maxZoom: 19,
    defaultVisible: false,
    userControllable: true,
    aiControllable: true,
    expensive: false,
    opacity: 0.8,
    description: "International, state, and territorial borders with place name labels.",
    attribution: "Esri / Natural Earth",
  },
  {
    id: "layer-osm",
    label: "OpenStreetMap Cartographic",
    category: "base",
    rendererSupport: ["2d", "3d"],
    sourceType: "raster",
    tileTemplate: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    minZoom: 0,
    maxZoom: 19,
    defaultVisible: false,
    userControllable: true,
    aiControllable: true,
    expensive: false,
    opacity: 1.0,
    description: "Community-driven global street and topography map.",
    attribution: "© OpenStreetMap contributors",
  },
]

class LayerRegistry {
  private layers: Map<string, ExploreLayerDefinition> = new Map()

  constructor() {
    INITIAL_LAYER_REGISTRY.forEach((l) => this.layers.set(l.id, { ...l }))
  }

  getAll(): ExploreLayerDefinition[] {
    return Array.from(this.layers.values())
  }

  getById(id: string): ExploreLayerDefinition | undefined {
    return this.layers.get(id)
  }

  getByCategory(category: ExploreLayerDefinition["category"]): ExploreLayerDefinition[] {
    return this.getAll().filter((l) => l.category === category)
  }

  getDefaultVisibleIds(): string[] {
    return this.getAll()
      .filter((l) => l.defaultVisible)
      .map((l) => l.id)
  }

  registerLayer(layer: ExploreLayerDefinition): void {
    this.layers.set(layer.id, { ...layer })
  }

  removeLayer(layerId: string): boolean {
    // Base layers cannot be unregistered
    const layer = this.layers.get(layerId)
    if (layer && layer.category === "base") return false
    return this.layers.delete(layerId)
  }

  updateLayer(layerId: string, partial: Partial<ExploreLayerDefinition>): void {
    const existing = this.layers.get(layerId)
    if (existing) {
      this.layers.set(layerId, { ...existing, ...partial })
    }
  }

  isSupportedByRenderer(id: string, mode: "2d" | "3d"): boolean {
    const layer = this.getById(id)
    if (!layer) return false
    return layer.rendererSupport.includes(mode)
  }

  getSupportedForMode(mode: "2d" | "3d"): ExploreLayerDefinition[] {
    return this.getAll().filter((l) => l.rendererSupport.includes(mode))
  }
}

export const layerRegistry = new LayerRegistry()
