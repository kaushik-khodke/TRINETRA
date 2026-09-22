/**
 * TRINETRA Phase 6 — Multi-Temporal Investigation Timeline
 * Visualizes chronological observations, baseline epochs, and physical surface transitions.
 */

import React from "react"
import { TimelineMilestone } from "@/lib/explore/investigation-types"
import { Calendar, CircleDot, Satellite, ArrowRight, Tag } from "lucide-react"

interface Props {
  milestones: TimelineMilestone[]
  onSelectEvidence?: (id: string) => void
}

export const InvestigationTimeline: React.FC<Props> = ({ milestones, onSelectEvidence }) => {
  if (!milestones || milestones.length === 0) {
    return (
      <div className="text-center py-6 text-xs text-slate-500 font-mono">
        No multi-temporal milestones recorded for this investigation.
      </div>
    )
  }

  return (
    <div className="space-y-4 relative pl-4 border-l-2 border-slate-800 ml-2 py-1">
      {milestones.map((m, idx) => (
        <div key={idx} className="relative group">
          {/* Node marker on vertical line */}
          <div className="absolute -left-[23px] top-1 w-3.5 h-3.5 rounded-full bg-slate-900 border-2 border-cyan-400 group-hover:scale-125 transition-transform" />

          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 space-y-1.5 hover:border-slate-700 transition-colors">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-1.5 font-mono text-cyan-400 font-bold">
                <Calendar className="w-3.5 h-3.5" />
                <span>{m.date}</span>
              </div>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase bg-slate-800 text-slate-300">
                {m.event_type}
              </span>
            </div>

            <h4 className="text-xs font-semibold text-slate-200">{m.title}</h4>
            <p className="text-xs text-slate-400 leading-relaxed">{m.description}</p>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-[10px] font-mono text-slate-500">
              <span className="flex items-center gap-1 text-slate-400">
                <Satellite className="w-3 h-3 text-cyan-500" />
                {m.platform}
              </span>

              {m.associated_evidence_ids && m.associated_evidence_ids.length > 0 && (
                <div className="flex items-center gap-1">
                  <Tag className="w-3 h-3 text-slate-600" />
                  {m.associated_evidence_ids.slice(0, 2).map((eid) => (
                    <button
                      key={eid}
                      onClick={() => onSelectEvidence?.(eid)}
                      className="text-cyan-400 hover:underline"
                    >
                      {eid}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
