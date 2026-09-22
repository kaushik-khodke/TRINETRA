/**
 * TRINETRA Phase 8 — Workspace State Hook & Reactive State Manager
 * Coordinates analyst workspaces, DAG investigation plans, multi-region comparisons,
 * batch processing, interactive evidence board, review queues, and report exports.
 */

import { useState, useEffect, useCallback, useRef } from "react"
import {
  Workspace,
  WorkspaceStatus,
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
  ReviewStatus,
  FollowUp,
  ReportDocument,
  WorkspaceTask,
  WorkspaceSnapshot,
} from "./workspace-types"
import { workspaceApi } from "./workspace-api"

export type WorkspaceTab =
  | "overview"
  | "plans"
  | "compare"
  | "batch"
  | "board"
  | "reviews"
  | "reports"
  | "tasks"

export function useWorkspaceState() {
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("overview")

  // Core Workspace
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(null)
  const [context, setContext] = useState<WorkspaceContext | null>(null)
  const [activities, setActivities] = useState<WorkspaceActivity[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  // Subsystem Entities
  const [plans, setPlans] = useState<InvestigationPlan[]>([])
  const [activePlan, setActivePlan] = useState<InvestigationPlan | null>(null)
  const [planRuns, setPlanRuns] = useState<PlanRun[]>([])

  const [comparisons, setComparisons] = useState<RegionComparison[]>([])
  const [activeComparison, setActiveComparison] = useState<RegionComparison | null>(null)

  const [batchJobs, setBatchJobs] = useState<BatchJob[]>([])
  const [activeBatchJob, setActiveBatchJob] = useState<BatchJob | null>(null)

  const [boardItems, setBoardItems] = useState<EvidenceBoardItem[]>([])
  const [boardRelations, setBoardRelations] = useState<EvidenceBoardRelation[]>([])
  const [selectedBoardItem, setSelectedBoardItem] = useState<EvidenceBoardItem | null>(null)

  const [annotations, setAnnotations] = useState<Annotation[]>([])
  const [reviews, setReviews] = useState<ReviewRecord[]>([])
  const [followUps, setFollowUps] = useState<FollowUp[]>([])

  const [reports, setReports] = useState<ReportDocument[]>([])
  const [activeReport, setActiveReport] = useState<ReportDocument | null>(null)

  const [tasks, setTasks] = useState<WorkspaceTask[]>([])
  const [snapshots, setSnapshots] = useState<WorkspaceSnapshot[]>([])
  const [synthesis, setSynthesis] = useState<any>(null)

  // Fetch workspaces on mount
  const refreshWorkspaces = useCallback(async () => {
    try {
      setIsLoading(true)
      const list = await workspaceApi.listWorkspaces()
      setWorkspaces(list)
      if (list.length > 0 && !activeWorkspace) {
        setActiveWorkspace(list[0])
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }, [activeWorkspace])

  useEffect(() => {
    refreshWorkspaces()
  }, [])

  // When active workspace changes, reload all its items
  const reloadWorkspaceData = useCallback(async (wsId: string) => {
    try {
      setIsLoading(true)
      setError(null)

      const [
        wsCtx,
        acts,
        pList,
        cList,
        bJobs,
        bItems,
        bRels,
        anns,
        revs,
        fUps,
        repList,
        tList,
        sList,
      ] = await Promise.all([
        workspaceApi.getContext(wsId).catch(() => null),
        workspaceApi.listActivities(wsId).catch(() => []),
        workspaceApi.listPlans(wsId).catch(() => []),
        workspaceApi.listComparisons(wsId).catch(() => []),
        workspaceApi.listBatchJobs(wsId).catch(() => []),
        workspaceApi.listBoardItems(wsId).catch(() => []),
        workspaceApi.listBoardRelations(wsId).catch(() => []),
        workspaceApi.listAnnotations(wsId).catch(() => []),
        workspaceApi.listReviews(wsId).catch(() => []),
        workspaceApi.listFollowUps(wsId).catch(() => []),
        workspaceApi.listReports(wsId).catch(() => []),
        workspaceApi.listTasks(wsId).catch(() => []),
        workspaceApi.listSnapshots(wsId).catch(() => []),
      ])

      setContext(wsCtx)
      setActivities(acts)
      setPlans(pList)
      setComparisons(cList)
      setBatchJobs(bJobs)
      setBoardItems(bItems)
      setBoardRelations(bRels)
      setAnnotations(anns)
      setReviews(revs)
      setFollowUps(fUps)
      setReports(repList)
      setTasks(tList)
      setSnapshots(sList)

      // Fetch initial synthesis if board has items
      if (bItems && bItems.length > 0) {
        workspaceApi.getSynthesis(wsId).then(setSynthesis).catch(() => {})
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (activeWorkspace) {
      reloadWorkspaceData(activeWorkspace.workspace_id)
    }
  }, [activeWorkspace?.workspace_id, reloadWorkspaceData])

  // Actions
  const createWorkspace = async (name: string, description?: string, aoi?: any) => {
    const ws = await workspaceApi.createWorkspace({ name, description, current_aoi: aoi })
    setWorkspaces((prev) => [ws, ...prev])
    setActiveWorkspace(ws)
    return ws
  }

  const updateWorkspaceStatus = async (status: WorkspaceStatus) => {
    if (!activeWorkspace) return
    const updated = await workspaceApi.updateWorkspace(activeWorkspace.workspace_id, { status })
    setActiveWorkspace(updated)
    setWorkspaces((prev) => prev.map((w) => (w.workspace_id === updated.workspace_id ? updated : w)))
  }

  const pinToBoard = async (item: Partial<EvidenceBoardItem>) => {
    if (!activeWorkspace) return
    const pinned = await workspaceApi.pinBoardItem(activeWorkspace.workspace_id, item)
    setBoardItems((prev) => [...prev.filter((i) => i.item_id !== pinned.item_id), pinned])
    return pinned
  }

  const deleteBoardItem = async (itemId: string) => {
    if (!activeWorkspace) return
    await workspaceApi.deleteBoardItem(activeWorkspace.workspace_id, itemId)
    setBoardItems((prev) => prev.filter((i) => i.item_id !== itemId))
    setBoardRelations((prev) => prev.filter((r) => r.source_item_id !== itemId && r.target_item_id !== itemId))
  }

  const linkBoardItems = async (sourceId: string, targetId: string, relationType: any = "supports") => {
    if (!activeWorkspace) return
    const rel = await workspaceApi.linkBoardItems(activeWorkspace.workspace_id, {
      source_item_id: sourceId,
      target_item_id: targetId,
      relation_type: relationType,
    })
    setBoardRelations((prev) => [...prev, rel])
    return rel
  }

  const createPlan = async (plan: Partial<InvestigationPlan>) => {
    if (!activeWorkspace) return
    const created = await workspaceApi.createPlan(activeWorkspace.workspace_id, plan)
    setPlans((prev) => [created, ...prev])
    return created
  }

  const executePlan = async (planId: string) => {
    if (!activeWorkspace) return
    const run = await workspaceApi.executePlan(activeWorkspace.workspace_id, planId)
    setPlanRuns((prev) => [run, ...prev])
    // Reload plan status
    const updatedPlan = await workspaceApi.getPlan(activeWorkspace.workspace_id, planId)
    setPlans((prev) => prev.map((p) => (p.plan_id === planId ? updatedPlan : p)))
    return run
  }

  const compareRegions = async (regionAId: string, regionBId: string, period = "last_12_months") => {
    if (!activeWorkspace) return
    const comp = await workspaceApi.compareRegions(activeWorkspace.workspace_id, regionAId, regionBId, period)
    setComparisons((prev) => [comp, ...prev])
    setActiveComparison(comp)
    return comp
  }

  const executeBatch = async (templateId: string, targets: any[], concurrency = 2) => {
    if (!activeWorkspace) return
    const job = await workspaceApi.executeBatch(activeWorkspace.workspace_id, templateId, targets, concurrency)
    setBatchJobs((prev) => [job, ...prev])
    setActiveBatchJob(job)
    return job
  }

  const setReviewStatus = async (entityType: string, entityId: string, status: ReviewStatus, reviewNote = "") => {
    if (!activeWorkspace) return
    const rev = await workspaceApi.setReviewStatus(activeWorkspace.workspace_id, {
      entity_type: entityType,
      entity_id: entityId,
      status,
      review_note: reviewNote,
    })
    setReviews((prev) => [...prev.filter((r) => !(r.entity_type === entityType && r.entity_id === entityId)), rev])
    return rev
  }

  const createFollowUp = async (entityType: string, entityId: string, note: string) => {
    if (!activeWorkspace) return
    const fu = await workspaceApi.createFollowUp(activeWorkspace.workspace_id, {
      linked_entity_type: entityType,
      linked_entity_id: entityId,
      note,
    })
    setFollowUps((prev) => [fu, ...prev])
    return fu
  }

  const createReport = async (title: string, sections: any[]) => {
    if (!activeWorkspace) return
    const rep = await workspaceApi.createReport(activeWorkspace.workspace_id, { title, sections })
    setReports((prev) => [rep, ...prev])
    setActiveReport(rep)
    return rep
  }

  const exportReport = async (reportId: string) => {
    if (!activeWorkspace) return
    return workspaceApi.exportReportPackage(activeWorkspace.workspace_id, reportId)
  }

  const submitTask = async (type: string, priority: any = "NORMAL", params: any = {}) => {
    if (!activeWorkspace) return
    const task = await workspaceApi.submitTask(activeWorkspace.workspace_id, {
      type,
      priority,
      parameters: params,
    })
    setTasks((prev) => [task, ...prev])
    return task
  }

  const cancelTask = async (taskId: string) => {
    if (!activeWorkspace) return
    await workspaceApi.cancelTask(activeWorkspace.workspace_id, taskId)
    setTasks((prev) =>
      prev.map((t) => (t.task_id === taskId ? { ...t, status: "CANCELLED" as any } : t))
    )
  }

  const createSnapshot = async () => {
    if (!activeWorkspace) return
    const snap = await workspaceApi.createSnapshot(activeWorkspace.workspace_id)
    setSnapshots((prev) => [snap, ...prev])
    return snap
  }

  return {
    activeTab,
    setActiveTab,
    workspaces,
    activeWorkspace,
    setActiveWorkspace,
    context,
    activities,
    isLoading,
    error,

    // Plans
    plans,
    activePlan,
    setActivePlan,
    planRuns,
    createPlan,
    executePlan,

    // Comparisons
    comparisons,
    activeComparison,
    setActiveComparison,
    compareRegions,

    // Batch
    batchJobs,
    activeBatchJob,
    setActiveBatchJob,
    executeBatch,

    // Board
    boardItems,
    boardRelations,
    selectedBoardItem,
    setSelectedBoardItem,
    pinToBoard,
    deleteBoardItem,
    linkBoardItems,

    // Annotations & Reviews
    annotations,
    reviews,
    followUps,
    setReviewStatus,
    createFollowUp,

    // Reports
    reports,
    activeReport,
    setActiveReport,
    createReport,
    exportReport,

    // Tasks & Snapshots
    tasks,
    snapshots,
    synthesis,
    submitTask,
    cancelTask,
    createSnapshot,
    refreshWorkspaces,
    reloadWorkspaceData: () => activeWorkspace && reloadWorkspaceData(activeWorkspace.workspace_id),
  }
}
