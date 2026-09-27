/**
 * TRINETRA Workstation — TypeScript Types & Contracts
 * Matches backend schemas from implementation-package.
 */

export interface Mission {
  id: string
  name: string
  slug: string
  description?: string
  status: "active" | "archived"
  default_srid: number
  settings: Record<string, any>
  created_by: string
  created_at: string
  updated_at: string
}

export interface AreaOfInterest {
  id: string
  mission_id: string
  name: string
  geometry: {
    type: string
    coordinates: any[]
  }
  bbox?: number[]
  start_at?: string
  end_at?: string
  source_type: "drawn" | "uploaded" | "derived"
  metadata?: Record<string, any>
  created_at: string
}

export interface AssetBand {
  id: string
  band_index: number
  name: string
  common_name?: string
  wavelength_min_nm?: number
  wavelength_max_nm?: number
  scale_factor: number
  add_offset: number
  unit?: string
}

export interface AssetVersion {
  id: string
  asset_id: string
  version_number: number
  object_uri: string
  thumbnail_uri?: string
  mime_type: string
  size_bytes: number
  crs_code: string
  width: number
  height: number
  band_count: number
  bands: AssetBand[]
  resolution_x: number
  resolution_y: number
  nodata_value?: number
  validation_report: Record<string, any>
  created_at: string
}

export interface Asset {
  id: string
  mission_id: string
  asset_type: "uploaded" | "catalog_item" | "derived"
  title: string
  source_provider: string
  external_id?: string
  collection_id: string
  footprint?: {
    type: string
    coordinates: any[]
  }
  acquired_at?: string
  status: "registered" | "validating" | "ready" | "warning" | "invalid" | "unavailable"
  versions: AssetVersion[]
  metadata: Record<string, any>
  created_at: string
}

export interface PipelineDefinition {
  key: string
  version: string
  label: string
  description: string
  supportedCollections: string[]
  requiredBands: string[]
  inputRoles: string[]
  outputTypes: string[]
  parameterBounds: Record<string, any>
  scientificNotes: string[]
}

export interface AnalysisPlanInputBinding {
  role: string
  assetVersionId: string
  assetId?: string
  label?: string
}

export interface AnalysisPlan {
  schemaVersion: string
  planId: string
  missionId: string
  questionId?: string
  questionText?: string
  aoiId?: string
  pipeline: {
    key: string
    version: string
    label?: string
  }
  inputs: AnalysisPlanInputBinding[]
  timeRange: {
    before?: { start: string; end: string }
    after?: { start: string; end: string }
    [key: string]: any
  }
  parameters: Record<string, any>
  assumptions: string[]
  blockingErrors: string[]
  warnings: string[]
  expectedOutputs: string[]
  limitations: string[]
  status: "draft" | "validated" | "approved" | "superseded" | "rejected"
  approved_by?: string
  approved_at?: string
  created_at: string
}

export interface RunOutput {
  id: string
  run_id: string
  output_type: string
  name: string
  object_uri: string
  tile_uri?: string
  mime_type: string
  geometry?: any
  statistics: Record<string, any>
  quality_flags: string[]
  metadata: Record<string, any>
}

export interface RunEvent {
  id: string
  run_id: string
  stage: string
  message: string
  progress_percent: number
  payload: Record<string, any>
  occurred_at: string
}

export interface ProvenanceRecord {
  id: string
  run_id: string
  manifest_uri: string
  pipeline: Record<string, any>
  source_assets: any[]
  parameters: Record<string, any>
  software_digest: string
  environment: Record<string, any>
  created_at: string
}

export interface AnalysisRun {
  id: string
  mission_id: string
  question_id?: string
  analysis_plan_id: string
  run_number: number
  status: "queued" | "preparing" | "running" | "succeeded" | "succeeded_with_warnings" | "failed" | "cancel_requested" | "cancelled"
  pipeline_key: string
  pipeline_version: string
  plan_snapshot: Record<string, any>
  started_at?: string
  finished_at?: string
  progress_percent: number
  current_stage: string
  error_code?: string
  error_message?: string
  outputs: RunOutput[]
  events: RunEvent[]
  provenance?: ProvenanceRecord
  created_at: string
}

export interface NotebookEntry {
  id: string
  mission_id: string
  question_id?: string
  run_id?: string
  title: string
  body: string
  entry_type: "question" | "result" | "note" | "finding" | "decision"
  findings_data: Record<string, any>
  created_by: string
  created_at: string
}

export interface CatalogScene {
  id: string
  collection: string
  datetime: string
  cloud_cover: number
  bands: string[]
  resolution_m: number
  provider: string
  thumbnail_url: string
  tile_url: string
  footprint: any
}
