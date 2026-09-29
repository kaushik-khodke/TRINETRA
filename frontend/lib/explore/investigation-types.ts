/**
 * TRINETRA Phase 6 — Semantic EO Intelligence & Evidence Fusion Types
 */

export type InvestigationStatus = "queued" | "running" | "completed" | "failed" | "cancelled"

export type InvestigationProgressStage =
  | "planning"
  | "specialists"
  | "fusion"
  | "semantics"
  | "trajectory"
  | "reasoning"
  | "completed"
  | "failed"
  | "cancelled"

export interface InvestigationProgress {
  current_stage: InvestigationProgressStage
  percent: number
  message: string
  step_index: number
  total_steps: number
  updated_at: string
}

export interface InvestigationArtifact {
  artifact_id: string
  name: string
  artifact_type: string
  file_path: string
  mime_type: string
  size_bytes?: number
  download_url: string
}

export interface AnalystNote {
  note_id?: string
  investigation_id: string
  text: string
  attachment_type?: string
  attachment_id?: string
  created_at?: string
  updated_at?: string
}

export type EvidenceType =
  | "SPATIAL"
  | "TEMPORAL"
  | "SPECTRAL"
  | "RADIOMETRIC"
  | "OBJECT"
  | "CHANGE"
  | "SAR"
  | "OPTICAL"
  | "MODEL"
  | "METADATA"
  | "GIS_STATISTIC"

export interface EvidenceCardData {
  id: string
  type: EvidenceType
  source: string
  observation_ids: string[]
  confidence: number
  quality: number
  value: any
  bounding_box?: [number, number, number, number]
  geometry?: any
  relationship_count: number
  has_conflict: boolean
  metadata?: Record<string, any>
}

export interface EvidenceRelationshipData {
  source_id: string
  target_id: string
  relationship_type: string
  confidence: number
  explanation?: string
}

export interface EvidenceConflictData {
  evidence_a_id: string
  evidence_b_id: string
  conflict_type: string
  severity: "low" | "medium" | "high"
  description: string
  resolution_strategy: string
}

export interface StructuredFindingData {
  finding_id: string
  category: string
  statement: string
  quantitative_value: Record<string, any>
  confidence: number
  supporting_evidence_ids: string[]
  limitations: string[]
  summary_badge?: string
}

export interface SemanticHypothesisData {
  hypothesis_id?: string
  semantic_class: string
  description: string
  confidence: number
  status?: "ACCEPTED" | "REJECTED" | "ALTERNATE"
  confidence_breakdown?: Record<string, number>
  alternative_hypotheses?: Array<{ semantic_class: string; probability: number }>
}

export interface InvestigationConclusion {
  summary: string
  primary_hypothesis?: SemanticHypothesisData
  confidence: number
  confidence_level: string
  confidence_justification: string
  attribution_boundary: string
  recommendations: string[]
}

export type SpecialistModelType =
  | "router"
  | "vision"
  | "sar"
  | "spectral"
  | "gis"
  | "fusion"
  | "classifier"
  | "reasoning"

export interface ChainOfThoughtStep {
  step_number: number
  node: string
  stage: string
  agent_role: string
  model_name: string
  model_type: SpecialistModelType
  input_summary: string
  observation: string
  thought_process: string
  prediction: string
  confidence: number
  metrics?: Record<string, any>
  timestamp?: string
}

export interface DeepAnalysisImagery {
  satellite: string
  layer_name: string
  timestamp: string
  resolution: string
  cloud_cover_percent?: number
  tile_url: string
  slippy_xyz: [number, number, number]
  optical_band_combination?: string
  description: string
  provider?: string
}

export interface DeepAnalysisChartSeries {
  metric: string
  delta: number
  unit: string
  direction: "increase" | "decrease" | "neutral"
  significance: "MODERATE" | "HIGH" | "CRITICAL" | "LOW"
}

export interface DeepAnalysisChartSegment {
  class_name: string
  area_ha: number
  percent: number
  color: string
}

export interface DeepAnalysisChartPoint {
  date: string
  value: number
  event_note: string
}

export interface DeepAnalysisChart {
  chart_id: string
  chart_type: "bar" | "donut" | "line"
  title: string
  x_label?: string
  y_label?: string
  total_area_ha?: number
  series?: DeepAnalysisChartSeries[]
  segments?: DeepAnalysisChartSegment[]
  points?: DeepAnalysisChartPoint[]
}

export interface DeepAnalysisDossierSection {
  section_id: string
  title: string
  content: string
}

export interface DeepAnalysisData {
  generated_at: string
  dossier_title: string
  target_sector: {
    label: string
    centroid: { lat: number; lon: number }
    area_hectares: number
    area_sq_km: number
    tile_coords_z16: { x: number; y: number; zoom: number }
  }
  imagery_comparison: {
    baseline_t0: DeepAnalysisImagery
    monitoring_t1: DeepAnalysisImagery
    high_resolution_context: DeepAnalysisImagery
  }
  dynamic_charts: DeepAnalysisChart[]
  technical_dossier_sections: DeepAnalysisDossierSection[]
}

export interface InvestigationItem {
  investigation_id: string
  question: string
  status: InvestigationStatus
  mode?: "normal" | "deep"
  progress: InvestigationProgress
  created_at: string
  started_at?: string
  completed_at?: string
  plan?: any
  findings: StructuredFindingData[]
  hypotheses: SemanticHypothesisData[]
  conflicts: EvidenceConflictData[]
  conclusion?: InvestigationConclusion
  chain_of_thought?: ChainOfThoughtStep[]
  limitations: any[]
  artifacts: InvestigationArtifact[]
  deep_analysis?: DeepAnalysisData
  result_data?: Record<string, any>
  error?: { code: string; message: string }
}

export interface InvestigationRequest {
  question: string
  observation_ids: string[]
  aoi?: any
  temporal_scope?: Record<string, any>
  options?: Record<string, any>
}

export interface InvestigationValidationResponse {
  valid: boolean
  intent: string
  estimated_compute_cost: "LOW" | "MEDIUM" | "HIGH"
  planned_specialists: string[]
  estimated_runtime_seconds: number
  warnings: string[]
  errors: string[]
}

export interface TimelineMilestone {
  index: number
  date: string
  observation_id: string
  platform: string
  event_type: string
  title: string
  description: string
  associated_evidence_ids: string[]
}
