"use client"

import React from "react"
import {
  LayoutDashboard,
  Layers,
  GitCompare,
  Network,
  CheckCircle2,
  FileText,
  Cpu,
  Loader2,
  AlertTriangle,
} from "lucide-react"
import { useWorkspaceState, WorkspaceTab } from "@/lib/explore/workspace-state"
import { WorkspaceHeader } from "./WorkspaceHeader"
import { WorkspaceOverview } from "./WorkspaceOverview"
import { InvestigationPlanner } from "./planning/InvestigationPlanner"
import { MultiRegionCompare } from "./comparison/MultiRegionCompare"
import { EvidenceBoard } from "./board/EvidenceBoard"
import { ReviewQueue } from "./annotations/ReviewQueue"
import { ReportBuilderView } from "./reporting/ReportBuilderView"
import { TaskQueuePanel } from "./tasks/TaskQueuePanel"

export function WorkspaceShell() {
  const {
    activeTab,
    setActiveTab,
    workspaces,
    activeWorkspace,
    setActiveWorkspace,
    context,
    activities,
    isLoading,
    error,

    plans,
    createPlan,
    executePlan,

    comparisons,
    activeComparison,
    compareRegions,

    boardItems,
    boardRelations,
    pinToBoard,
    deleteBoardItem,
    linkBoardItems,

    reviews,
    followUps,
    setReviewStatus,
    createFollowUp,

    reports,
    createReport,
    exportReport,

    tasks,
    submitTask,
    cancelTask,
    createSnapshot,
  } = useWorkspaceState()

  const tabs: { id: WorkspaceTab; label: string; icon: React.ComponentType<{ size?: number; className?: string }> }[] = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "plans", label: "Plans", icon: Layers },
    { id: "compare", label: "Compare", icon: GitCompare },
    { id: "board", label: "Evidence Board", icon: Network },
    { id: "reviews", label: "Reviews", icon: CheckCircle2 },
    { id: "reports", label: "Reports", icon: FileText },
    { id: "tasks", label: "Tasks", icon: Cpu },
  ]

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-100 overflow-hidden select-none">
      {/* 1. Header */}
      <WorkspaceHeader
        workspaces={workspaces}
        activeWorkspace={activeWorkspace}
        onSelectWorkspace={setActiveWorkspace}
        onCreateWorkspace={async (name, desc) => {
          // create workspace handler
        }}
        onUpdateStatus={async (status) => {
          // update status handler
        }}
        onSnapshot={createSnapshot}
      />

      {/* 2. Subtabs Navigation Bar */}
      <div className="flex items-center gap-1 px-3 py-1.5 border-b border-slate-800 bg-slate-900/50 overflow-x-auto no-scrollbar">
        {tabs.map((t) => {
          const Icon = t.icon
          const isActive = activeTab === t.id
          return (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium whitespace-nowrap transition ${
                isActive
                  ? "bg-sky-950 text-sky-400 border border-sky-800/80"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              }`}
            >
              <Icon size={13} className={isActive ? "text-sky-400" : "text-slate-500"} />
              <span>{t.label}</span>
            </button>
          )
        })}
      </div>

      {/* 3. Error or Loading State */}
      {error && (
        <div className="bg-red-950/40 border-b border-red-800/60 p-2 text-xs text-red-300 flex items-center gap-2">
          <AlertTriangle size={13} className="text-red-400 shrink-0" />
          <span className="truncate">{error}</span>
        </div>
      )}

      {/* 4. Active Sub-View Body */}
      <div className="flex-1 overflow-y-auto">
        {isLoading && !activeWorkspace ? (
          <div className="flex flex-col items-center justify-center h-48 text-slate-500 text-xs space-y-2">
            <Loader2 size={20} className="animate-spin text-sky-400" />
            <span>Loading workspace intelligence...</span>
          </div>
        ) : !activeWorkspace ? (
          <div className="p-8 text-center text-xs text-slate-500">
            No workspace selected. Create or select a workspace from the header.
          </div>
        ) : (
          <>
            {activeTab === "overview" && (
              <WorkspaceOverview
                workspace={activeWorkspace}
                context={context}
                activities={activities}
                boardItems={boardItems}
                plans={plans}
                reports={reports}
                reviews={reviews}
                onTabChange={setActiveTab}
                onGenerateSynthesis={() => setActiveTab("reports")}
              />
            )}

            {activeTab === "plans" && (
              <InvestigationPlanner
                plans={plans}
                onCreatePlan={createPlan}
                onExecutePlan={executePlan}
              />
            )}

            {activeTab === "compare" && (
              <MultiRegionCompare
                comparisons={comparisons}
                activeComparison={activeComparison}
                onCompareRegions={compareRegions}
              />
            )}

            {activeTab === "board" && (
              <EvidenceBoard
                items={boardItems}
                relations={boardRelations}
                onPinItem={pinToBoard}
                onDeleteItem={deleteBoardItem}
                onLinkItems={linkBoardItems}
              />
            )}

            {activeTab === "reviews" && (
              <ReviewQueue
                reviews={reviews}
                followUps={followUps}
                onSetReviewStatus={setReviewStatus}
                onCreateFollowUp={createFollowUp}
              />
            )}

            {activeTab === "reports" && (
              <ReportBuilderView
                workspaceId={activeWorkspace.workspace_id}
                reports={reports}
                onCreateReport={createReport}
                onExportReport={exportReport}
              />
            )}

            {activeTab === "tasks" && (
              <TaskQueuePanel
                tasks={tasks}
                onSubmitTask={submitTask}
                onCancelTask={cancelTask}
              />
            )}
          </>
        )}
      </div>
    </div>
  )
}
