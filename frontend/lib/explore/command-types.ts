/**
 * TRINETRA / Shanetra Explore Architecture
 * Command Types & AI Contract Interfaces
 * Phase 3: Natural-Language Earth Exploration + Controlled AI Map Commands
 */

export type CommandExecutionStatus =
  | "accepted"
  | "executed"
  | "no_op"
  | "rejected"
  | "failed"
  | "cancelled"

export interface AICommandItem {
  command_id: string
  type: string
  status: CommandExecutionStatus
  message: string
  details?: Record<string, any>
}

export interface AICameraPatch {
  latitude?: number
  longitude?: number
  zoom?: number
  heading?: number
  pitch?: number
  duration?: number
}

export interface AIStatePatch {
  camera?: AICameraPatch | null
  visible_layer_ids?: string[] | null
  layer_opacities?: Record<string, number> | null
  active_dataset_id?: string | null
}

export interface AIQueryResponse {
  request_id: string
  status: "completed" | "partial_failure" | "rejected" | "error"
  summary: string
  intent: string
  fast_path: boolean
  commands: AICommandItem[]
  state_patch: AIStatePatch
  error_code?: string | null
  latency_ms: number
}

export interface AIStatusInfo {
  available: boolean
  model: string
  router_model: string
  planner_model: string
  structured_output: boolean
  offline_fallback_active: boolean
}
