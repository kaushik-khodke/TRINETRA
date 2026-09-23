"use client"

/**
 * TRINETRA Phase 7 — Intelligence Top Dashboard Bar
 * Displays high-level intelligence KPIs and subtab switcher.
 */

import React from "react"
import { IntelSubTab } from "@/lib/explore/intelligence-state"
import {
  Database,
  Search,
  AlertTriangle,
  Flame,
  Radio,
  FileCheck2,
  RefreshCw,
} from "lucide-react"

interface Props {
  activeSubTab: IntelSubTab
  onSelectSubTab: (tab: IntelSubTab) => void
  eventsCount: number
  anomaliesCount: number
  hotspotsCount: number
  monitorsCount: number
  onRefreshAll?: () => void
}

export const IntelligenceDashboard: React.FC<Props> = ({
  activeSubTab,
  onSelectSubTab,
  eventsCount,
  anomaliesCount,
  hotspotsCount,
  monitorsCount,
  onRefreshAll,
}) => {
  const tabs: Array<{ id: IntelSubTab; label: string; icon: React.FC<any>; count?: number }> = [
    { id: "events", label: "Events", icon: Database, count: eventsCount },
    { id: "search", label: "Search & Sim", icon: Search },
    { id: "anomalies", label: "Anomalies", icon: AlertTriangle, count: anomaliesCount },
    { id: "hotspots", label: "Hotspots", icon: Flame, count: hotspotsCount },
    { id: "monitoring", label: "Monitors", icon: Radio, count: monitorsCount },
    { id: "templates", label: "Templates", icon: FileCheck2 },
  ]

  return (
    <div className="flex flex-col gap-2 p-2 bg-slate-900/90 border-b border-slate-800 backdrop-blur-md">
      {/* Top Banner with KPIs */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[11px] font-mono uppercase tracking-wider font-semibold text-orange-300">
            Persistent EO Intelligence
          </span>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-orange-950/80 border border-orange-800/60 text-orange-400">
            Phase 7
          </span>
        </div>

        {onRefreshAll && (
          <button
            onClick={onRefreshAll}
            title="Refresh Intelligence Index"
            className="p-1 rounded text-slate-400 hover:text-orange-300 hover:bg-slate-800 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Quick KPI Strip */}
      <div className="grid grid-cols-4 gap-1 text-center font-mono">
        <div className="bg-slate-950/60 border border-slate-800/80 rounded py-1 px-1">
          <div className="text-[9px] text-slate-400 uppercase">Events</div>
          <div className="text-xs font-bold text-sky-400">{eventsCount}</div>
        </div>
        <div className="bg-slate-950/60 border border-slate-800/80 rounded py-1 px-1">
          <div className="text-[9px] text-slate-400 uppercase">Anomalies</div>
          <div className="text-xs font-bold text-amber-400">{anomaliesCount}</div>
        </div>
        <div className="bg-slate-950/60 border border-slate-800/80 rounded py-1 px-1">
          <div className="text-[9px] text-slate-400 uppercase">Hotspots</div>
          <div className="text-xs font-bold text-rose-400">{hotspotsCount}</div>
        </div>
        <div className="bg-slate-950/60 border border-slate-800/80 rounded py-1 px-1">
          <div className="text-[9px] text-slate-400 uppercase">Monitors</div>
          <div className="text-xs font-bold text-emerald-400">{monitorsCount}</div>
        </div>
      </div>

      {/* Subtab Button Switcher */}
      <div className="flex items-center gap-1 overflow-x-auto pb-1 text-xs font-mono scrollbar-none">
        {tabs.map((tab) => {
          const Icon = tab.icon
          const isActive = activeSubTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => onSelectSubTab(tab.id)}
              className={`flex items-center gap-1.5 px-2 py-1 rounded text-[11px] whitespace-nowrap transition-all ${
                isActive
                  ? "bg-orange-500/20 text-orange-300 border border-orange-500/40 shadow-sm shadow-orange-950"
                  : "bg-slate-950/40 text-slate-400 border border-slate-800/60 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? "text-orange-400" : "text-slate-500"}`} />
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span
                  className={`text-[9px] px-1 rounded-full ${
                    isActive ? "bg-orange-500/30 text-orange-200" : "bg-slate-800 text-slate-400"
                  }`}
                >
                  {tab.count}
                </span>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
