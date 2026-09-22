/**
 * TRINETRA Phase 8 — Workspace REST Client
 * Typed fetch client interacting with /api/v1/workspace endpoints.
 */

import {
  Workspace,
  WorkspaceContext,
  WorkspaceActivity,
  InvestigationPlan,
  PlanRun,
  RegionComparison,
  BatchJob,
  EvidenceBoardItem,
  EvidenceBoardRelation,
  Annotation,
  ReviewRecord,
  FollowUp,
  ReportDocument,
  WorkspaceTask,
  WorkspaceSnapshot,
} from "./workspace-types"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  })
  if (!res.ok) {
    const errorText = await res.text()
    throw new Error(`API Error ${res.status}: ${errorText || res.statusText}`)
  }
  return res.json()
}

export const workspaceApi = {
  // 1. Workspaces Core
  async listWorkspaces(status?: string, limit = 50, offset = 0): Promise<Workspace[]> {
    const query = new URLSearchParams()
    if (status) query.set("status", status)
    query.set("limit", limit.toString())
    query.set("offset", offset.toString())
    return fetchJson<Workspace[]>(`/api/v1/workspace?${query.toString()}`)
  },

  async createWorkspace(data: { name: string; description?: string; current_aoi?: any }): Promise<Workspace> {
    return fetchJson<Workspace>("/api/v1/workspace", {
      method: "POST",
      body: JSON.stringify(data),
    })
  },

  async getWorkspace(workspaceId: string): Promise<Workspace> {
    return fetchJson<Workspace>(`/api/v1/workspace/${workspaceId}`)
  },

  async updateWorkspace(workspaceId: string, patch: Partial<Workspace>): Promise<Workspace> {
    return fetchJson<Workspace>(`/api/v1/workspace/${workspaceId}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    })
  },

  async deleteWorkspace(workspaceId: string): Promise<boolean> {
    const res = await fetchJson<{ deleted: boolean }>(`/api/v1/workspace/${workspaceId}`, {
      method: "DELETE",
    })
    return res.deleted
  },

  // 2. Context & Activity
  async getContext(workspaceId: string): Promise<WorkspaceContext> {
    return fetchJson<WorkspaceContext>(`/api/v1/workspace/${workspaceId}/context`)
  },

  async updateContext(workspaceId: string, patch: Partial<WorkspaceContext>): Promise<WorkspaceContext> {
    return fetchJson<WorkspaceContext>(`/api/v1/workspace/${workspaceId}/context`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    })
  },

  async listActivities(workspaceId: string, limit = 50): Promise<WorkspaceActivity[]> {
    return fetchJson<WorkspaceActivity[]>(`/api/v1/workspace/${workspaceId}/activities?limit=${limit}`)
  },

  // 3. Evidence Board
  async listBoardItems(workspaceId: string): Promise<EvidenceBoardItem[]> {
    return fetchJson<EvidenceBoardItem[]>(`/api/v1/workspace/${workspaceId}/board/items`)
  },

  async pinBoardItem(workspaceId: string, item: Partial<EvidenceBoardItem>): Promise<EvidenceBoardItem> {
    return fetchJson<EvidenceBoardItem>(`/api/v1/workspace/${workspaceId}/board/items`, {
      method: "POST",
      body: JSON.stringify(item),
    })
  },

  async deleteBoardItem(workspaceId: string, itemId: string): Promise<boolean> {
    const res = await fetchJson<{ deleted: boolean }>(`/api/v1/workspace/${workspaceId}/board/items/${itemId}`, {
      method: "DELETE",
    })
    return res.deleted
  },

  async listBoardRelations(workspaceId: string): Promise<EvidenceBoardRelation[]> {
    return fetchJson<EvidenceBoardRelation[]>(`/api/v1/workspace/${workspaceId}/board/relations`)
  },

  async linkBoardItems(workspaceId: string, relation: Partial<EvidenceBoardRelation>): Promise<EvidenceBoardRelation> {
    return fetchJson<EvidenceBoardRelation>(`/api/v1/workspace/${workspaceId}/board/relations`, {
      method: "POST",
      body: JSON.stringify(relation),
    })
  },

  async deleteBoardRelation(workspaceId: string, relationId: string): Promise<boolean> {
    const res = await fetchJson<{ deleted: boolean }>(`/api/v1/workspace/${workspaceId}/board/relations/${relationId}`, {
      method: "DELETE",
    })
    return res.deleted
  },

  // 4. Investigation Plans
  async listPlans(workspaceId: string): Promise<InvestigationPlan[]> {
    return fetchJson<InvestigationPlan[]>(`/api/v1/workspace/${workspaceId}/plans`)
  },

  async createPlan(workspaceId: string, plan: Partial<InvestigationPlan>): Promise<InvestigationPlan> {
    return fetchJson<InvestigationPlan>(`/api/v1/workspace/${workspaceId}/plans`, {
      method: "POST",
      body: JSON.stringify(plan),
    })
  },

  async getPlan(workspaceId: string, planId: string): Promise<InvestigationPlan> {
    return fetchJson<InvestigationPlan>(`/api/v1/workspace/${workspaceId}/plans/${planId}`)
  },

  async executePlan(workspaceId: string, planId: string): Promise<PlanRun> {
    return fetchJson<PlanRun>(`/api/v1/workspace/${workspaceId}/plans/${planId}/execute`, {
      method: "POST",
      body: JSON.stringify({}),
    })
  },

  async listPlanRuns(workspaceId: string, planId: string): Promise<PlanRun[]> {
    return fetchJson<PlanRun[]>(`/api/v1/workspace/${workspaceId}/plans/${planId}/runs`)
  },

  // 5. Comparisons
  async compareRegions(
    workspaceId: string,
    regionAId: string,
    regionBId: string,
    period = "last_12_months",
    thresholds?: number[]
  ): Promise<RegionComparison> {
    return fetchJson<RegionComparison>(`/api/v1/workspace/${workspaceId}/compare/regions`, {
      method: "POST",
      body: JSON.stringify({
        region_a_id: regionAId,
        region_b_id: regionBId,
        period,
        thresholds,
      }),
    })
  },

  async listComparisons(workspaceId: string): Promise<RegionComparison[]> {
    return fetchJson<RegionComparison[]>(`/api/v1/workspace/${workspaceId}/compare/regions`)
  },

  // 6. Batch Processing
  async executeBatch(
    workspaceId: string,
    templateId: string,
    targets: any[],
    concurrency = 2
  ): Promise<BatchJob> {
    return fetchJson<BatchJob>(`/api/v1/workspace/${workspaceId}/batch`, {
      method: "POST",
      body: JSON.stringify({
        template_id: templateId,
        targets,
        concurrency,
      }),
    })
  },

  async listBatchJobs(workspaceId: string): Promise<BatchJob[]> {
    return fetchJson<BatchJob[]>(`/api/v1/workspace/${workspaceId}/batch`)
  },

  // 7. Synthesis
  async getSynthesis(workspaceId: string): Promise<any> {
    return fetchJson<any>(`/api/v1/workspace/${workspaceId}/synthesis`, {
      method: "POST",
    })
  },

  // 8. Annotations, Reviews & Follow-Ups
  async listAnnotations(workspaceId: string): Promise<Annotation[]> {
    return fetchJson<Annotation[]>(`/api/v1/workspace/${workspaceId}/annotations`)
  },

  async addAnnotation(workspaceId: string, annotation: Partial<Annotation>): Promise<Annotation> {
    return fetchJson<Annotation>(`/api/v1/workspace/${workspaceId}/annotations`, {
      method: "POST",
      body: JSON.stringify(annotation),
    })
  },

  async deleteAnnotation(workspaceId: string, annotationId: string): Promise<boolean> {
    const res = await fetchJson<{ deleted: boolean }>(`/api/v1/workspace/${workspaceId}/annotations/${annotationId}`, {
      method: "DELETE",
    })
    return res.deleted
  },

  async listReviews(workspaceId: string): Promise<ReviewRecord[]> {
    return fetchJson<ReviewRecord[]>(`/api/v1/workspace/${workspaceId}/reviews`)
  },

  async setReviewStatus(workspaceId: string, review: Partial<ReviewRecord>): Promise<ReviewRecord> {
    return fetchJson<ReviewRecord>(`/api/v1/workspace/${workspaceId}/reviews`, {
      method: "POST",
      body: JSON.stringify(review),
    })
  },

  async listFollowUps(workspaceId: string, status?: string): Promise<FollowUp[]> {
    const q = status ? `?status=${status}` : ""
    return fetchJson<FollowUp[]>(`/api/v1/workspace/${workspaceId}/follow-ups${q}`)
  },

  async createFollowUp(workspaceId: string, followUp: Partial<FollowUp>): Promise<FollowUp> {
    return fetchJson<FollowUp>(`/api/v1/workspace/${workspaceId}/follow-ups`, {
      method: "POST",
      body: JSON.stringify(followUp),
    })
  },

  // 9. Reports & Exports
  async listReports(workspaceId: string): Promise<ReportDocument[]> {
    return fetchJson<ReportDocument[]>(`/api/v1/workspace/${workspaceId}/reports`)
  },

  async createReport(workspaceId: string, report: Partial<ReportDocument>): Promise<ReportDocument> {
    return fetchJson<ReportDocument>(`/api/v1/workspace/${workspaceId}/reports`, {
      method: "POST",
      body: JSON.stringify(report),
    })
  },

  async getReport(workspaceId: string, reportId: string): Promise<ReportDocument> {
    return fetchJson<ReportDocument>(`/api/v1/workspace/${workspaceId}/reports/${reportId}`)
  },

  getReportRenderUrl(workspaceId: string, reportId: string): string {
    return `${API_BASE}/api/v1/workspace/${workspaceId}/reports/${reportId}/render`
  },

  async exportReportPackage(workspaceId: string, reportId: string): Promise<{ exported: boolean; package_path: string; filename: string }> {
    return fetchJson<{ exported: boolean; package_path: string; filename: string }>(
      `/api/v1/workspace/${workspaceId}/reports/${reportId}/export`,
      { method: "POST" }
    )
  },

  // 10. Tasks
  async submitTask(workspaceId: string, task: Partial<WorkspaceTask>): Promise<WorkspaceTask> {
    return fetchJson<WorkspaceTask>(`/api/v1/workspace/${workspaceId}/tasks`, {
      method: "POST",
      body: JSON.stringify(task),
    })
  },

  async listTasks(workspaceId: string, status?: string): Promise<WorkspaceTask[]> {
    const q = status ? `?status=${status}` : ""
    return fetchJson<WorkspaceTask[]>(`/api/v1/workspace/${workspaceId}/tasks${q}`)
  },

  async cancelTask(workspaceId: string, taskId: string): Promise<boolean> {
    const res = await fetchJson<{ cancelled: boolean }>(`/api/v1/workspace/${workspaceId}/tasks/${taskId}/cancel`, {
      method: "POST",
    })
    return res.cancelled
  },

  // 11. Snapshots
  async createSnapshot(workspaceId: string, state?: any): Promise<WorkspaceSnapshot> {
    return fetchJson<WorkspaceSnapshot>(`/api/v1/workspace/${workspaceId}/snapshots`, {
      method: "POST",
      body: JSON.stringify({ state }),
    })
  },

  async listSnapshots(workspaceId: string): Promise<WorkspaceSnapshot[]> {
    return fetchJson<WorkspaceSnapshot[]>(`/api/v1/workspace/${workspaceId}/snapshots`)
  },
}
