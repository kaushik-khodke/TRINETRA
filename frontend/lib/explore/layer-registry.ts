/**
 * TRINETRA / Shanetra Explore Architecture
 * Layer Registry — Canonical Source of Truth for Exploration Layers
 * Phase 2: Dynamic layer registration, raster tile templates, and opacity tracking.
 */

import { ExploreLayerDefinition } from "./types"

export const INITIAL_LAYER_REGISTRY: ExploreLayerDefinition[] = [
  {
    id: "layer-base-dark",
    label: "Dark Canvas Basemap",
    category: "base",
    rendererSupport: ["2d", "3d"],
    sourceType: "raster",
    defaultVisible: true,
    userControllable: true,
    aiControllable: false,
    expensive: false,
    opacity: 1.0,
    description: "High-contrast dark thematic reference base for EO intelligence.",
    attribution: "Esri / OpenStreetMap",
  },
  {
    id: "layer-local_sentinel2_nagpur_truecolor",
    label: "Sentinel-2 Nagpur True Color (RGB+NIR)",
    category: "imagery",
    rendererSupport: ["2d", "3d"],
    sourceType: "raster",
    tileTemplate: "/api/v1/explore/tiles/layer-local_sentinel2_nagpur_truecolor/{z}/{x}/{y}.png",
    minZoom: 4,
    maxZoom: 18,
    defaultVisible: false,
    userControllable: true,
    aiControllable: true,
    expensive: false,
    opacity: 1.0,
    description: "Multi-band 10m surface reflectance over Central India.",
    attribution: "TRINETRA / Sentinel-2 MSI",
    assetId: "local_sentinel2_nagpur_truecolor",
  },
  {
    id: "layer-local_sentinel1_mumbai_sar",
    label: "Sentinel-1 Mumbai Radar (SAR VV)",
    category: "imagery",
    rendererSupport: ["2d", "3d"],
    sourceType: "raster",
    tileTemplate: "/api/v1/explore/tiles/layer-local_sentinel1_mumbai_sar/{z}/{x}/{y}.png",
    minZoom: 4,
    maxZoom: 18,
    defaultVisible: false,
    userControllable: true,
    aiControllable: true,
    expensive: false,
    opacity: 1.0,
    description: "All-weather cloud-penetrating C-band radar backscatter over West Coast.",
    attribution: "TRINETRA / Sentinel-1 C-SAR",
    assetId: "local_sentinel1_mumbai_sar",
  },
  {
    id: "layer-borders",
    label: "Administrative Boundaries",
    category: "system",
    rendererSupport: ["2d", "3d"],
    sourceType: "vector",
    defaultVisible: false,
    userControllable: true,
    aiControllable: true,
    expensive: false,
    opacity: 0.8,
    description: "State, territorial, and national boundaries overlay.",
    attribution: "Survey of India / Natural Earth",
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
