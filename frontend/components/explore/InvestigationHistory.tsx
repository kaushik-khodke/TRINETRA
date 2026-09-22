/**
 * TRINETRA Phase 6 — Investigation History List
 * Enables analysts to review and replay past multi-modal investigations.
 */

import React from "react"
import { History, CheckCircle2, Clock, XCircle, AlertCircle, ChevronRight } from "lucide-react"

interface Props {
  history: any[]
  activeInvestigationId: string | null
  onSelectInvestigation: (id: string) => void
}

export const InvestigationHistory: React.FC<Props> = ({
  history,
  activeInvestigationId,
  onSelectInvestigation,
}) => {
  if (!history || history.length === 0) {
    return (
      <div className="text-center py-6 text-xs text-slate-500 font-mono">
        No previous investigations found.
      </div>
    )
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
      case "running":
        return <Clock className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
      case "cancelled":
        return <XCircle className="w-3.5 h-3.5 text-amber-400" />
      default:
        return <AlertCircle className="w-3.5 h-3.5 text-slate-500" />
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5 text-xs text-slate-300 font-semibold font-mono">
        <History className="w-3.5 h-3.5 text-cyan-400" />
        <span>Recent Investigations ({history.length})</span>
      </div>

      <div className="space-y-1.5 max-h-72 overflow-y-auto pr-1">
        {history.map((item) => {
          const isActive = item.investigation_id === activeInvestigationId
          return (
            <div
              key={item.investigation_id}
              onClick={() => onSelectInvestigation(item.investigation_id)}
              className={`p-2.5 rounded-lg border transition-all cursor-pointer flex items-center justify-between gap-2 ${
                isActive
                  ? "bg-cyan-950/40 border-cyan-500 ring-1 ring-cyan-500/50"
                  : "bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900/90"
              }`}
            >
              <div className="flex flex-col gap-1 truncate">
                <div className="flex items-center gap-1.5">
                  {getStatusIcon(item.status)}
                  <span className="font-mono text-[10px] text-cyan-400 font-bold truncate">
                    {item.investigation_id}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">
                    {(item.created_at || "").slice(0, 10)}
                  </span>
                </div>
                <span className="text-xs text-slate-200 truncate font-medium">
                  {item.question}
                </span>
              </div>

              <ChevronRight className="w-4 h-4 text-slate-600 shrink-0" />
            </div>
          )
        })}
      </div>
    </div>
  )
}
