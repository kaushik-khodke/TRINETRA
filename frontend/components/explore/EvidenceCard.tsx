/**
 * TRINETRA Phase 6 — Evidence Card
 * Displays individual multi-sensor evidence items with quality, sensor provenance,
 * localized spatial metadata, and conflict flags.
 */

import React from "react"
import { EvidenceCardData } from "@/lib/explore/investigation-types"
import {
  Satellite,
  Radio,
  Eye,
  Box,
  Binary,
  AlertCircle,
  MapPin,
  Share2,
  ChevronRight,
} from "lucide-react"

interface Props {
  evidence: EvidenceCardData
  isSelected: boolean
  onSelect: (id: string) => void
}

export const EvidenceCard: React.FC<Props> = ({ evidence, isSelected, onSelect }) => {
  const getTypeIcon = (type: string) => {
    switch (type) {
      case "SAR":
        return <Radio className="w-3.5 h-3.5 text-indigo-400" />
      case "OPTICAL":
      case "SPECTRAL":
        return <Eye className="w-3.5 h-3.5 text-emerald-400" />
      case "OBJECT":
        return <Box className="w-3.5 h-3.5 text-amber-400" />
      case "CHANGE":
        return <Binary className="w-3.5 h-3.5 text-rose-400" />
      default:
        return <Satellite className="w-3.5 h-3.5 text-orange-400" />
    }
  }

  const getTypeBadgeColor = (type: string) => {
    switch (type) {
      case "SAR":
        return "bg-indigo-950 text-indigo-300 border-indigo-800"
      case "OPTICAL":
      case "SPECTRAL":
        return "bg-emerald-950 text-emerald-300 border-emerald-800"
      case "OBJECT":
        return "bg-amber-950 text-amber-300 border-amber-800"
      case "CHANGE":
        return "bg-rose-950 text-rose-300 border-rose-800"
      default:
        return "bg-orange-950 text-orange-300 border-orange-800"
    }
  }

  return (
    <div
      onClick={() => onSelect(evidence.id)}
      className={`p-3 rounded-lg border transition-all cursor-pointer ${
        isSelected
          ? "bg-orange-950/40 border-orange-500 shadow-[0_0_15px_rgba(6,182,212,0.15)] ring-1 ring-orange-500/50"
          : "bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900/90"
      }`}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-1.5">
          {getTypeIcon(evidence.type)}
          <span
            className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold border ${getTypeBadgeColor(
              evidence.type
            )}`}
          >
            {evidence.type}
          </span>
          <span className="text-[10px] font-mono text-slate-500 truncate max-w-[90px]">
            {evidence.id}
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          {evidence.has_conflict && (
            <span
              title="Discrepancy detected with another evidence item"
              className="p-1 rounded bg-amber-950/80 border border-amber-700 text-amber-400 flex items-center"
            >
              <AlertCircle className="w-3 h-3" />
            </span>
          )}
          <span className="font-mono text-xs text-orange-400 font-semibold">
            {Math.round(evidence.confidence * 100)}%
          </span>
        </div>
      </div>

      <div className="text-[11px] text-slate-400 font-mono mb-2 truncate">
        Source: <span className="text-slate-300">{evidence.source}</span>
      </div>

      {/* Value preview */}
      {evidence.value && (
        <div className="bg-slate-950/80 border border-slate-800/80 rounded p-2 mb-2 text-[11px] font-mono text-slate-300 space-y-1">
          {typeof evidence.value === "object" ? (
            Object.entries(evidence.value)
              .slice(0, 3)
              .map(([k, v]) => (
                <div key={k} className="flex items-center justify-between gap-2">
                  <span className="text-slate-500 text-[10px] truncate">{k.replace(/_/g, " ")}:</span>
                  <span className="text-orange-300 font-bold truncate">{String(v)}</span>
                </div>
              ))
          ) : (
            <div className="truncate">{String(evidence.value)}</div>
          )}
        </div>
      )}

      {/* Card footer */}
      <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1.5 border-t border-slate-800/60 font-mono">
        <span className="flex items-center gap-1">
          <MapPin className="w-3 h-3 text-slate-400" />
          {evidence.bounding_box ? "Localized" : "Scene-wide"}
        </span>

        {evidence.relationship_count > 0 && (
          <span className="flex items-center gap-1 text-slate-400">
            <Share2 className="w-3 h-3 text-orange-500" />
            {evidence.relationship_count} link{evidence.relationship_count > 1 ? "s" : ""}
          </span>
        )}

        <span className="flex items-center gap-0.5 text-orange-400 font-semibold">
          Focus
          <ChevronRight className="w-3 h-3" />
        </span>
      </div>
    </div>
  )
}
