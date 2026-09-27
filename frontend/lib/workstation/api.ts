/**
 * TRINETRA Workstation — API Client
 * Interfaces with /api/v1/workstation endpoints.
 */

import {
  Mission,
  AreaOfInterest,
  Asset,
  PipelineDefinition,
  AnalysisPlan,
  AnalysisRun,
  NotebookEntry,
  CatalogScene,
} from "./types"

const API_BASE = "/api/v1/workstation"

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  })
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(errorBody.detail || errorBody.message || `Request failed with status ${res.status}`)
  }
  return res.json()
}

export const workstationApi = {
  // Missions
  listMissions: () => fetchJSON<Mission[]>(`${API_BASE}/missions`),
  getMission: (id: string) => fetchJSON<Mission>(`${API_BASE}/missions/${id}`),
  createMission: (payload: { name: string; description?: string }) =>
    fetchJSON<Mission>(`${API_BASE}/missions`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // AOIs
  listAOIs: (missionId: string) => fetchJSON<AreaOfInterest[]>(`${API_BASE}/missions/${missionId}/aois`),
  createAOI: (missionId: string, payload: { name: string; geometry: any; start_at?: string; end_at?: string }) =>
    fetchJSON<AreaOfInterest>(`${API_BASE}/missions/${missionId}/aois`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  deleteAOI: (missionId: string, aoiId: string) =>
    fetchJSON<{ success: boolean; deleted_id: string }>(`${API_BASE}/missions/${missionId}/aois/${aoiId}`, {
      method: "DELETE",
    }),

  // Assets & Catalog
  listAssets: (missionId: string) => fetchJSON<Asset[]>(`${API_BASE}/missions/${missionId}/assets`),
  deleteAsset: (missionId: string, assetId: string) =>
    fetchJSON<{ success: boolean; deleted_id: string }>(`${API_BASE}/missions/${missionId}/assets/${assetId}`, {
      method: "DELETE",
    }),
  deleteCollection: (missionId: string, collectionId: string) =>
    fetchJSON<{ success: boolean; collection_id: string; deleted_count: number }>(
      `${API_BASE}/missions/${missionId}/collections/${collectionId}`,
      {
        method: "DELETE",
      }
    ),
  uploadAsset: (
    missionId: string,
    file: File,
    title?: string,
    onProgress?: (percent: number, loaded: number, total: number) => void,
    collectionId?: string,
  ): Promise<Asset> => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      const formData = new FormData()
      formData.append("file", file)
      if (title) formData.append("title", title)
      if (collectionId) formData.append("collection_id", collectionId)

      xhr.open("POST", `${API_BASE}/missions/${missionId}/upload`)

      if (onProgress && xhr.upload) {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percent = Math.round((event.loaded / event.total) * 100)
            onProgress(percent, event.loaded, event.total)
          }
        }
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText))
          } catch {
            reject(new Error("Invalid server JSON response"))
          }
        } else {
          try {
            const err = JSON.parse(xhr.responseText)
            reject(new Error(err.detail || err.message || `Upload failed with status ${xhr.status}`))
          } catch {
            reject(new Error(`Upload failed with status ${xhr.status}`))
          }
        }
      }

      xhr.onerror = () => reject(new Error("Network connection error during file upload"))
      xhr.send(formData)
    })
  },
  searchCatalog: (missionId: string, payload: { collection?: string; cloudCoverMax?: number }) =>
    fetchJSON<{ scenes: CatalogScene[]; total_found: number }>(`${API_BASE}/missions/${missionId}/catalog/search`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Pipelines
  listPipelines: () => fetchJSON<PipelineDefinition[]>(`${API_BASE}/pipelines`),

  // Copilot & Planning
  draftPlan: (missionId: string, payload: { question: string; aoi_id?: string; pipeline_key?: string; context_options?: any }) =>
    fetchJSON<AnalysisPlan>(`${API_BASE}/missions/${missionId}/plan`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  validatePlan: (plan: AnalysisPlan) =>
    fetchJSON<AnalysisPlan>(`${API_BASE}/plans/${plan.planId}/validate`, {
      method: "POST",
      body: JSON.stringify({ plan }),
    }),
  approvePlan: (planId: string) =>
    fetchJSON<AnalysisPlan>(`${API_BASE}/plans/${planId}/approve`, {
      method: "POST",
      body: JSON.stringify({ approved_by: "analyst_principal" }),
    }),

  // Execution Runs
  listRuns: (missionId: string) => fetchJSON<AnalysisRun[]>(`${API_BASE}/missions/${missionId}/runs`),
  getRun: (runId: string) => fetchJSON<AnalysisRun>(`${API_BASE}/runs/${runId}`),
  submitRun: (missionId: string, planId: string) =>
    fetchJSON<AnalysisRun>(`${API_BASE}/missions/${missionId}/runs`, {
      method: "POST",
      body: JSON.stringify({ plan_id: planId }),
    }),

  // Notebook & Export
  listNotebook: (missionId: string) => fetchJSON<NotebookEntry[]>(`${API_BASE}/missions/${missionId}/notebook`),
  addNotebookEntry: (missionId: string, payload: { title: string; body: string; entry_type?: string; run_id?: string; findings_data?: any }) =>
    fetchJSON<NotebookEntry>(`${API_BASE}/missions/${missionId}/notebook`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getExportManifest: (missionId: string) => fetchJSON<any>(`${API_BASE}/missions/${missionId}/export`),
}
