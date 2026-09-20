/**
 * TRINETRA — Phase 5: Findings Panel
 * Displays structured analytical findings with filtering and selection.
 */

import React, { useState } from "react"
import { AnalysisFinding } from "@/lib/explore/types"
import { FindingCard } from "./FindingCard"
import { ListFilter } from "lucide-react"

interface Props {
  findings: AnalysisFinding[]
  selectedFindingId: string | null
  onSelectFinding: (findingId: string) => void
}

export const FindingsPanel: React.FC<Props> = ({
  findings,
  selectedFindingId,
  onSelectFinding,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL")

  const categories = ["ALL", ...Array.from(new Set(findings.map((f) => f.category || "GENERAL")))]

  const filteredFindings =
    selectedCategory === "ALL"
      ? findings
      : findings.filter((f) => (f.category || "GENERAL") === selectedCategory)

  if (!findings || findings.length === 0) {
    return (
      <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-lg text-center text-xs text-slate-400">
        No findings generated for this analysis run.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Category filter */}
      {categories.length > 2 && (
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
          <ListFilter className="w-3.5 h-3.5 text-slate-500 shrink-0" />
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2 py-0.5 rounded text-[10px] font-mono whitespace-nowrap transition-colors ${
                selectedCategory === cat
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                  : "bg-slate-800/60 text-slate-400 hover:text-slate-200 border border-slate-700/50"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      )}

      {/* Findings list */}
      <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
        {filteredFindings.map((finding) => (
          <FindingCard
            key={finding.finding_id}
            finding={finding}
            isSelected={selectedFindingId === finding.finding_id}
            onSelect={onSelectFinding}
          />
        ))}
      </div>
    </div>
  )
}
