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

export interface InvestigationItem {
  investigation_id: string
  question: string
  status: InvestigationStatus
  progress: InvestigationProgress
  created_at: string
  started_at?: string
  completed_at?: string
  plan?: any
  findings: StructuredFindingData[]
  hypotheses: SemanticHypothesisData[]
  conflicts: EvidenceConflictData[]
  conclusion?: InvestigationConclusion
  limitations: any[]
  artifacts: InvestigationArtifact[]
  result_data?: Record<string, any>
  error?: { code: string; message: string }
}

export interface InvestigationRequest {
  question: string
  observation_ids: string[]
  aoi?: any
  temporal_scope?: Record<string, any>
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
