"use client"

import React from "react"
import {
  Activity,
  Layers,
  FileText,
  Network,
  GitCompare,
  CheckCircle2,
  Clock,
  Sparkles,
  MapPin,
  ExternalLink,
} from "lucide-react"
import {
  Workspace,
  WorkspaceContext,
  WorkspaceActivity,
  EvidenceBoardItem,
  InvestigationPlan,
  ReportDocument,
  ReviewRecord,
} from "@/lib/explore/workspace-types"

interface WorkspaceOverviewProps {
  workspace: Workspace
  context: WorkspaceContext | null
  activities: WorkspaceActivity[]
  boardItems: EvidenceBoardItem[]
  plans: InvestigationPlan[]
  reports: ReportDocument[]
  reviews: ReviewRecord[]
  onTabChange: (tab: any) => void
  onGenerateSynthesis: () => void
}

export function WorkspaceOverview({
  workspace,
  context,
  activities,
  boardItems,
  plans,
  reports,
  reviews,
  onTabChange,
  onGenerateSynthesis,
}: WorkspaceOverviewProps) {
  const pendingReviews = reviews.filter((r) => r.status === "UNREVIEWED").length

  return (
    <div className="p-4 space-y-5 text-slate-200">
      {/* 1. Quick Stats Grid */}
      <div className="grid grid-cols-4 gap-2">
        <div
          onClick={() => onTabChange("board")}
          className="bg-slate-900/60 border border-slate-800 rounded-lg p-3 hover:border-sky-500/50 cursor-pointer transition"
        >
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase">Evidence</span>
            <Network size={13} className="text-sky-400" />
          </div>
          <div className="text-xl font-bold text-slate-100">{boardItems.length}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Pinned items</div>
        </div>

        <div
          onClick={() => onTabChange("plans")}
          className="bg-slate-900/60 border border-slate-800 rounded-lg p-3 hover:border-emerald-500/50 cursor-pointer transition"
        >
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase">Plans</span>
            <Layers size={13} className="text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-slate-100">{plans.length}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Workflows</div>
        </div>

        <div
          onClick={() => onTabChange("reviews")}
          className="bg-slate-900/60 border border-slate-800 rounded-lg p-3 hover:border-amber-500/50 cursor-pointer transition"
        >
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase">Review</span>
            <CheckCircle2 size={13} className="text-amber-400" />
          </div>
          <div className="text-xl font-bold text-slate-100">{pendingReviews}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Pending audit</div>
        </div>

        <div
          onClick={() => onTabChange("reports")}
          className="bg-slate-900/60 border border-slate-800 rounded-lg p-3 hover:border-purple-500/50 cursor-pointer transition"
        >
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase">Reports</span>
            <FileText size={13} className="text-purple-400" />
          </div>
          <div className="text-xl font-bold text-slate-100">{reports.length}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Dossiers</div>
        </div>
      </div>

      {/* 2. Active Operational Context */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3.5 space-y-2.5">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-1.5">
            <MapPin size={13} className="text-sky-400" /> Active Operational Context
          </span>
          <button
            onClick={onGenerateSynthesis}
            className="flex items-center gap-1 text-[11px] text-sky-400 hover:text-sky-300 bg-sky-950/60 border border-sky-800/60 px-2 py-0.5 rounded transition"
          >
            <Sparkles size={11} /> Synthesize
          </button>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-mono">Active Regions</span>
            <span className="text-slate-200 font-medium">
              {context?.active_regions.length ? context.active_regions.join(", ") : "None assigned"}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-mono">Selected Findings</span>
            <span className="text-slate-200 font-medium">
              {context?.selected_findings.length ? `${context.selected_findings.length} findings` : "None"}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-mono">Selected Observations</span>
            <span className="text-slate-200 font-medium">
              {context?.selected_observations.length ? `${context.selected_observations.length} scenes` : "None"}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-mono">Active Investigation</span>
            <span className="text-slate-200 font-medium truncate block">
              {context?.open_investigation_id || "None"}
            </span>
          </div>
        </div>
      </div>

      {/* 3. Recent Auditable Activities */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-slate-400 font-mono uppercase tracking-wider">
          <span className="flex items-center gap-1.5">
            <Activity size={13} className="text-slate-400" /> Audit Activity Log
          </span>
          <span>{activities.length} entries</span>
        </div>

        <div className="bg-slate-900/40 border border-slate-800 rounded-lg divide-y divide-slate-800/60 max-h-56 overflow-y-auto">
          {activities.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-500">No activity recorded yet in this workspace.</div>
          ) : (
            activities.map((act) => (
              <div key={act.activity_id} className="p-2.5 flex items-start justify-between text-xs">
                <div>
                  <div className="font-medium text-slate-300 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
                    {act.activity_type.replace(/_/g, " ")}
                  </div>
                  {act.entity_type && (
                    <span className="text-[10px] text-slate-500 font-mono">
                      {act.entity_type}: {act.entity_id || "N/A"}
                    </span>
                  )}
                </div>
                <span className="text-[10px] text-slate-500 font-mono whitespace-nowrap">
                  {new Date(act.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
