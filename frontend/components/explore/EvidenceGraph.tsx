/**
 * TRINETRA Phase 6 — Interactive Evidence Graph Viewer
 * Visualizes multi-sensor evidence nodes and relationship edges (SUPPORTS, CONTRADICTS, CORROBORATES).
 */

import React, { useState } from "react"
import { EvidenceCardData } from "@/lib/explore/investigation-types"
import { Share2, Filter, AlertCircle, CheckCircle, ArrowRight } from "lucide-react"

interface Props {
  evidenceCards: EvidenceCardData[]
  relationships: any[]
  selectedEvidenceId: string | null
  onSelectEvidence: (id: string) => void
}

export const EvidenceGraph: React.FC<Props> = ({
  evidenceCards,
  relationships,
  selectedEvidenceId,
  onSelectEvidence,
}) => {
  const [filterType, setFilterType] = useState<string>("ALL")

  const filteredRelationships = relationships.filter((rel) => {
    if (filterType === "ALL") return true
    return rel.relationship_type === filterType
  })

  const getEdgeColor = (type: string) => {
    switch (type) {
      case "SUPPORTS":
        return "text-emerald-400 border-emerald-500/30 bg-emerald-950/40"
      case "CONTRADICTS":
        return "text-rose-400 border-rose-500/30 bg-rose-950/40"
      case "CORROBORATES":
        return "text-orange-400 border-orange-500/30 bg-orange-950/40"
      default:
        return "text-slate-400 border-slate-700 bg-slate-900"
    }
  }

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Share2 className="w-4 h-4 text-orange-400" />
          <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
            Evidence Link Graph ({evidenceCards.length} nodes, {relationships.length} edges)
          </h4>
        </div>

        {/* Filter controls */}
        <div className="flex items-center gap-1 text-[10px] font-mono">
          <Filter className="w-3 h-3 text-slate-500" />
          {["ALL", "SUPPORTS", "CONTRADICTS", "CORROBORATES"].map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`px-1.5 py-0.5 rounded transition-colors ${
                filterType === t
                  ? "bg-orange-900 text-orange-200 font-bold border border-orange-700"
                  : "bg-slate-800 text-slate-400 hover:text-slate-200"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Nodes pill grid */}
      <div className="flex flex-wrap gap-1.5 p-2 bg-slate-950/60 rounded border border-slate-800/80 max-h-32 overflow-y-auto">
        {evidenceCards.map((ev) => {
          const isSelected = ev.id === selectedEvidenceId
          return (
            <button
              key={ev.id}
              onClick={() => onSelectEvidence(ev.id)}
              className={`px-2 py-1 rounded text-[11px] font-mono transition-all flex items-center gap-1 ${
                isSelected
                  ? "bg-orange-500 text-slate-950 font-bold shadow-sm shadow-orange-500/50 scale-105"
                  : "bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
              }`}
            >
              <span>{ev.type}</span>
              <span className="text-[9px] opacity-70">({ev.id.slice(0, 6)})</span>
            </button>
          )
        })}
      </div>

      {/* Relationship Edges List */}
      <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
        {filteredRelationships.length === 0 ? (
          <div className="text-xs text-slate-500 text-center py-4">No matching relationships found.</div>
        ) : (
          filteredRelationships.map((rel, idx) => {
            const isConnected =
              selectedEvidenceId &&
              (rel.source_id === selectedEvidenceId || rel.target_id === selectedEvidenceId)

            return (
              <div
                key={idx}
                className={`flex items-center justify-between p-2 rounded border text-xs font-mono transition-all ${
                  isConnected
                    ? "ring-1 ring-orange-500/60 bg-orange-950/20"
                    : "bg-slate-950/40 border-slate-800/60"
                }`}
              >
                <div className="flex items-center gap-1.5 truncate">
                  <span
                    onClick={() => onSelectEvidence(rel.source_id)}
                    className="cursor-pointer text-orange-400 hover:underline truncate max-w-[80px]"
                  >
                    {rel.source_id}
                  </span>
                  <ArrowRight className="w-3 h-3 text-slate-600 shrink-0" />
                  <span
                    onClick={() => onSelectEvidence(rel.target_id)}
                    className="cursor-pointer text-orange-400 hover:underline truncate max-w-[80px]"
                  >
                    {rel.target_id}
                  </span>
                </div>

                <div className="flex items-center gap-1.5 shrink-0">
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${getEdgeColor(
                      rel.relationship_type
                    )}`}
                  >
                    {rel.relationship_type}
                  </span>
                  <span className="text-[10px] text-slate-500">
                    {Math.round(rel.confidence * 100)}%
                  </span>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
