/**
 * TRINETRA Phase 8 — Analyst Command Center & Multi-Region Workflows Type Contracts
 * Full TypeScript interfaces for analyst workspaces, DAG investigation plans,
 * multi-region comparisons, evidence board, review statuses, reporting, and tasks.
 */

export type WorkspaceStatus = "CREATED" | "ACTIVE" | "PAUSED" | "COMPLETED" | "ARCHIVED"

export type PlanStatus = "DRAFT" | "READY" | "RUNNING" | "COMPLETED" | "FAILED" | "PARTIAL" | "CANCELLED"

export type StepStatus = "PENDING" | "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED" | "SKIPPED" | "CANCELLED"

export type PlanStepType =
  | "OBSERVATION_SEARCH"
  | "ANALYZE_BITEMPORAL"
  | "ANALYZE_SAR_OPTICAL"
  | "ANALYZE_SINGLE_IMAGE"
  | "SEARCH_INTELLIGENCE"
  | "FIND_SIMILAR"
  | "CHECK_PERSISTENCE"
  | "CHECK_ANOMALY"
  | "COMPARE_REGIONS"
  | "COMPARE_EVENTS"
  | "BUILD_SYNTHESIS"
  | "BUILD_REPORT"

export type TaskPriority = "INTERACTIVE" | "NORMAL" | "BACKGROUND"

export type TaskStatus = "PENDING" | "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED" | "CANCELLED"

export type ReviewStatus = "UNREVIEWED" | "REVIEWED" | "NEEDS_FOLLOWUP" | "RESOLVED_BY_ANALYST"

export type ReportStatus = "DRAFT" | "VALIDATED" | "FINAL" | "ARCHIVED"

export interface Workspace {
  workspace_id: string
  name: string
  description?: string
  status: WorkspaceStatus
  current_aoi?: Record<string, any>
  created_at: string
  updated_at: string
  created_by?: string
}

export interface WorkspaceContext {
  workspace_id: string
  current_aoi: Record<string, any>
  active_regions: string[]
  selected_observations: string[]
  selected_events: string[]
  selected_findings: string[]
  open_investigation_id?: string | null
  active_comparison_id?: string | null
  active_report_id?: string | null
}

export interface WorkspaceActivity {
  activity_id: string
  workspace_id: string
  activity_type: string
  entity_type?: string | null
  entity_id?: string | null
  details: Record<string, any>
  timestamp: string
}

export interface InvestigationStep {
  step_id: string
  type: PlanStepType
  depends_on: string[]
  parameters: Record<string, any>
  status: StepStatus
  result_reference?: string | null
  error?: string | null
}

export interface InvestigationPlan {
  plan_id: string
  workspace_id: string
  title: string
  question: string
  steps: InvestigationStep[]
  constraints?: Record<string, any>
  required_evidence?: string[]
  status: PlanStatus
  created_at: string
  updated_at: string
}

export interface PlanRun {
  run_id: string
  plan_id: string
  execution_index: number
  status: PlanStatus
  step_results: Record<string, any>
  started_at: string
  completed_at?: string | null
}

export interface SensitivityPoint {
  threshold: number
  detected_area_km2: number
  rate_of_change: number
  stability: "STABLE" | "MODERATELY_SENSITIVE" | "HYPERSENSITIVE"
}

export interface RegionProfile {
  region_id: string
  name: string
  area_km2: number
  raw_event_count: number
  raw_finding_count: number
  events_per_100km2: number
  findings_per_100km2: number
  sensitivity_curve: SensitivityPoint[]
}

export interface ComparisonDifference {
  metric: string
  region_a_value: number
  region_b_value: number
  absolute_difference: number
  percentage_difference: number
  higher_region: string
}

export interface RegionComparison {
  comparison_id: string
  workspace_id: string
  region_a_id: string
  region_b_id: string
  period: string
  metrics: {
    region_a: RegionProfile
    region_b: RegionProfile
  }
  differences: {
    events?: ComparisonDifference
    findings?: ComparisonDifference
    period?: string
  }
  warnings: string[]
  created_at: string
}

export interface BatchTarget {
  target_id: string
  region_id?: string
  aoi?: Record<string, any>
  parameters?: Record<string, any>
  estimated_pixels?: number
}

export interface BatchItemOutcome {
  target_id: string
  status: "COMPLETED" | "FAILED" | "SKIPPED"
  result_ref?: string
  metrics?: Record<string, any>
  error?: string
  runtime_seconds: number
}

export interface BatchSummary {
  total_targets: number
  completed_count: number
  failed_count: number
  skipped_count: number
  total_runtime_seconds: number
  aggregate_metrics: {
    average_change_percentage?: number
    max_change_percentage?: number
    min_change_percentage?: number
    average_confidence?: number
    items_with_findings?: number
  }
}

export interface BatchJob {
  batch_id: string
  workspace_id: string
  template_id: string
  targets: BatchTarget[]
  status: string
  concurrency: number
  results: {
    summary?: BatchSummary
    items?: BatchItemOutcome[]
  }
  created_at: string
  updated_at: string
}

export interface EvidenceBoardItem {
  item_id: string
  workspace_id: string
  type: string
  source_id: string
  position: { x: number; y: number }
  title: string
  annotation?: string
  created_at: string
}

export interface EvidenceBoardRelation {
  relation_id: string
  workspace_id: string
  source_item_id: string
  target_item_id: string
  relation_type: "supports" | "contradicts" | "related_to" | "follow_up"
  metadata?: Record<string, any>
  created_at: string
}

export interface Annotation {
  annotation_id: string
  workspace_id: string
  geometry?: Record<string, any>
  text: string
  type: "TEXT" | "LABEL" | "REGION_NOTE" | "QUESTION"
  linked_entity_type?: string | null
  linked_entity_id?: string | null
  created_at: string
  updated_at: string
}

export interface ReviewRecord {
  review_id: string
  workspace_id: string
  entity_type: string
  entity_id: string
  status: ReviewStatus
  review_note?: string
  reviewed_at: string
  analyst_id: string
}

export interface FollowUp {
  follow_up_id: string
  workspace_id: string
  linked_entity_type: string
  linked_entity_id: string
  note: string
  status: "OPEN" | "IN_PROGRESS" | "COMPLETE" | "CANCELLED"
  created_at: string
  updated_at: string
}

export interface ReportClaim {
  claim_id: string
  text: string
  evidence_ids: string[]
  type?: string
}

export interface ReportSection {
  section_id: string
  type: string
  title: string
  content?: string
  source_ids?: string[]
  claims: ReportClaim[]
  author_type?: string
}

export interface ReportDocument {
  report_id: string
  workspace_id: string
  title: string
  status: ReportStatus
  sections: ReportSection[]
  version: number
  manifest?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface WorkspaceTask {
  task_id: string
  workspace_id: string
  type: string
  priority: TaskPriority
  status: TaskStatus
  parameters?: Record<string, any>
  progress: {
    stage: string
    percentage: number
  }
  result_reference?: string | null
  error?: Record<string, any> | null
  idempotency_key?: string | null
  created_at: string
  started_at?: string | null
  completed_at?: string | null
}

export interface WorkspaceSnapshot {
  snapshot_id: string
  workspace_id: string
  state: Record<string, any>
  created_at: string
}
