/**
 * TRINETRA Phase 7 — Persistent EO Intelligence Type Contracts
 * Full TypeScript interfaces for canonical events, lifecycle states, findings,
 * similarity search, anomalies, regional density, monitoring, and templates.
 */

export type EventState =
  | "CANDIDATE"
  | "OBSERVED"
  | "CORROBORATED"
  | "PERSISTENT"
  | "RESOLVED"

export interface EventHistoryItem {
  timestamp: string
  from_state: string | null
  to_state: string
  reason: string
  finding_id?: string
}

export interface EOEvent {
  event_id: string
  title: string
  canonical_region_id: string
  semantic_class: string
  state: EventState
  confidence: number
  confidence_dimensions: Record<string, number>
  first_seen: string
  last_seen: string
  supporting_findings: string[]
  supporting_analyses: string[]
  geometry?: any
  bounding_box: number[]
  history: EventHistoryItem[]
  metadata: Record<string, any>
  version: number
  created_at: string
  updated_at: string
}

export interface PersistentFinding {
  finding_id: string
  investigation_id: string
  type: string
  label: string
  geometry?: any
  bounding_box: number[]
  confidence: number
  evidence_ids: string[]
  observation_ids: string[]
  metrics: Record<string, any>
  semantic_class: string
  created_at: string
}

export interface CanonicalRegion {
  canonical_region_id: string
  name: string
  geometry?: any
  bounding_box: number[]
  observed_region_ids: string[]
  first_seen: string
  last_seen: string
  description: string
  tags: string[]
  created_at: string
  updated_at: string
}

export interface HotspotCluster {
  cluster_id: string
  centroid_lat: number
  centroid_lon: number
  bounding_box: number[]
  event_count: number
  severity_score: number
  dominant_class: string
  event_ids: string[]
}

export interface AnomalyRecord {
  anomaly_id: string
  baseline_id: string
  metric_name: string
  observed_value: number
  baseline_mean: number
  baseline_std: number
  baseline_range: number[]
  anomaly_score: number
  confidence: number
  anomaly_type: string
  explanation: string
  region_id?: string
  event_id?: string
  finding_id?: string
  status: string
  created_at: string
}

export interface MonitorDefinition {
  monitor_id: string
  name: string
  aoi?: any
  bounding_box: number[]
  observation_collection: string
  schedule_cadence: string
  template_id?: string
  trigger_condition: any
  enabled: boolean
  max_runs: number
  cooldown_hours: number
  total_runs?: number
  last_triggered_at?: string
  created_at: string
  updated_at: string
}

export interface MonitorAlert {
  alert_id: string
  monitor_id: string
  event_id?: string
  finding_id?: string
  severity: "CRITICAL" | "WARNING" | "INFO"
  trigger_reason: string
  alert_fingerprint: string
  evidence?: Record<string, any>
  acknowledged: boolean
  created_at: string
}

export interface InvestigationTemplate {
  template_id: string
  name: string
  question: string
  analysis_mode: string
  required_evidence: string[]
  time_configuration: Record<string, any>
  semantic_targets: string[]
  filters: Record<string, any>
  created_at: string
}

export interface IntelligenceSearchResultItem {
  type: "event" | "finding" | "region"
  id: string
  title: string
  confidence: number
  semantic_class: string
  score: number
  match_reasons: string[]
  bounding_box: number[]
  temporal_range: Record<string, string>
  item_data: any
}

export interface IntelligenceSearchResponse {
  results: IntelligenceSearchResultItem[]
  total: number
  page: number
  limit: number
  generated_at: string
  data_as_of: string
}

export interface SimilarityResultItem {
  id: string
  score: number
  similarity_level: string
  match_factors: string[]
  title: string
  semantic_class: string
  confidence: number
  bounding_box: number[]
}

export interface SimilarityResponse {
  target_id: string
  matches: SimilarityResultItem[]
  generated_at: string
}

export interface RegionalSummary {
  region_id: string
  name: string
  bounding_box: number[]
  total_events: number
  event_breakdown: Record<string, number>
  state_breakdown: Record<string, number>
  density_events_per_sqkm: number
  activity_trajectory: Array<{ month: string; event_count: number }>
  hotspot_count: number
  last_updated: string
}
