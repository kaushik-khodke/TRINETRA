/**
 * TRINETRA / Shanetra Explore Architecture
 * Strict TypeScript Type Definitions
 * Phase 2: Real Earth-Observation Data, STAC Discovery, Raster Tiling, and Layer Governance.
 */

export type ExploreViewMode = "2d" | "3d"

export interface GlobeCameraState {
  latitude: number
  longitude: number
  zoom: number
  heading: number
  pitch: number
  roll?: number
}

export interface ExploreAsset {
  id: string
  href: string
  mediaType: string
  role: string
  title?: string
  bands?: string[]
}

export interface ExploreDataset {
  id: string
  provider: string
  collection?: string
  title: string
  datetime?: string
  bbox?: number[]
  cloudCover?: number
  thumbnailUrl?: string
  assets: Record<string, ExploreAsset>
  properties?: Record<string, any>
}

export interface ExploreLayerDefinition {
  id: string
  label: string
  category: "base" | "imagery" | "analysis" | "system"
  rendererSupport: ("2d" | "3d")[]
  sourceType?: "raster" | "vector"
  tileTemplate?: string
  minZoom?: number
  maxZoom?: number
  defaultVisible: boolean
  userControllable: boolean
  aiControllable: boolean
  expensive: boolean
  opacity?: number
  description?: string
  attribution?: string
  assetId?: string
}

export interface ExploreState {
  viewMode: ExploreViewMode
  sidebarOpen: boolean
  camera: GlobeCameraState
  selectedLayerIds: string[]
  layerOpacities: Record<string, number>
  activeDatasetId: string | null
  catalogItems: ExploreDataset[]
  catalogLoading: boolean
  catalogProvider: "all" | "local" | "copernicus"
  rendererStatus: "idle" | "loading" | "ready" | "error"
  webglSupported: boolean
  errorMessage?: string | null
}

export type GlobeCommand =
  | {
      type: "SET_VIEW_MODE"
      mode: ExploreViewMode
    }
  | {
      type: "FLY_TO"
      latitude: number
      longitude: number
      zoom: number
      heading?: number
      pitch?: number
      duration?: number
    }
  | {
      type: "RESET_VIEW"
    }
  | {
      type: "SHOW_LAYER"
      layerId: string
    }
  | {
      type: "HIDE_LAYER"
      layerId: string
    }
  | {
      type: "TOGGLE_LAYER"
      layerId: string
    }
  | {
      type: "SET_LAYER_OPACITY"
      layerId: string
      opacity: number
    }
  | {
      type: "ADD_LAYER"
      layer: ExploreLayerDefinition
    }
  | {
      type: "REMOVE_LAYER"
      layerId: string
    }
  | {
      type: "SET_AOI"
      geometry: any
    }
  | {
      type: "CLEAR_AOI"
    }
  | {
      type: "SELECT_OBSERVATION"
      observation: ObservationSummary
      targetSlot?: "primary" | "compare_a" | "compare_b"
    }
  | {
      type: "SET_COMPARISON"
      mode: ComparisonMode
      observationA: ObservationSummary
      observationB: ObservationSummary
    }

export interface AOIValidationResult {
  valid: boolean
  area_km2?: number
  vertex_count?: number
  bbox?: number[]
  centroid?: [number, number]
  errors: string[]
  warnings: string[]
  hash?: string
  simplified_geometry?: any
}

export interface ObservationSummary {
  id: string
  collection: string
  datetime: string
  cloud_cover?: number | null
  platform?: string
  bbox: number[]
  thumbnail?: string | null
  preview_url?: string | null
  asset_keys: string[]
}

export interface ObservationDetails extends ObservationSummary {
  geometry?: any
  properties: Record<string, any>
  assets: Record<string, any>
}

export type ComparisonMode = "split" | "side_by_side" | "opacity"

export interface ComparisonValidationResponse {
  compatible: boolean
  warnings: string[]
  errors: string[]
  observation_a?: ObservationSummary
  observation_b?: ObservationSummary
  temporal_delta_days?: number
  spatial_overlap_pct?: number
}

export interface PerformanceMetrics {
  initTimeMs: number
  modeSwitchTimeMs: number
  lastFrameTimestamp: number
  estimatedFps: number
  activeRenderer: ExploreViewMode
}

export interface RendererAdapter {
  flyTo(target: { latitude: number; longitude: number; zoom?: number; heading?: number; pitch?: number; duration?: number }): void
  resetView(): void
  setLayerVisibility(layerId: string, visible: boolean): void
  setLayerOpacity?(layerId: string, opacity: number): void
  addLayerSource?(layer: ExploreLayerDefinition): void
  removeLayerSource?(layerId: string): void
  setAOI?(geometry: any): void
  clearAOI?(): void
  setObservationLayer?(slot: "primary" | "compare_a" | "compare_b", observation: ObservationSummary, opacity?: number): void
  getCameraState(): GlobeCameraState
  destroy(): void
}

