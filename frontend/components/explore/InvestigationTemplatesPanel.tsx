"use client"

/**
 * TRINETRA Phase 7 — Standard Investigation Templates Panel
 * Catalogs reusable analytical patterns for repeatable multi-temporal EO audits.
 */

import React, { useState } from "react"
import { InvestigationTemplate } from "@/lib/explore/intelligence-types"
import {
  FileCheck2,
  RefreshCw,
  Play,
  Layers,
  HelpCircle,
  Tag,
  Clock,
} from "lucide-react"

interface Props {
  templates: InvestigationTemplate[]
  isLoading: boolean
  availableObservationIds?: string[]
  onRunTemplate: (templateId: string, observationIds: string[]) => Promise<any>
  onRefresh: () => void
}

export const InvestigationTemplatesPanel: React.FC<Props> = ({
  templates,
  isLoading,
  availableObservationIds = [],
  onRunTemplate,
  onRefresh,
}) => {
  const [runningTemplateId, setRunningTemplateId] = useState<string | null>(null)

  const handleRun = async (templateId: string) => {
    setRunningTemplateId(templateId)
    try {
      // Default to available observation IDs or a fallback dummy observation if in demo mode
      const obsToUse =
        availableObservationIds.length > 0
          ? availableObservationIds
          : ["obs_s2_demo_01", "obs_s2_demo_02"]
      await onRunTemplate(templateId, obsToUse)
    } finally {
      setRunningTemplateId(null)
    }
  }

  return (
    <div className="flex flex-col gap-2.5 font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between pb-1 border-b border-slate-800">
        <div className="flex items-center gap-1.5 text-cyan-400">
          <FileCheck2 className="w-3.5 h-3.5" />
          <span className="font-semibold text-slate-200">
            Audit Templates ({templates.length})
          </span>
        </div>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          title="Reload Templates"
          className="p-1 rounded text-slate-400 hover:text-cyan-300 hover:bg-slate-800 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin text-cyan-400" : ""}`} />
        </button>
      </div>

      {/* Templates List */}
      <div className="space-y-2.5 max-h-[500px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-cyan-500/20">
        {templates.length === 0 && !isLoading && (
          <div className="text-center py-8 text-slate-500 text-xs">
            <FileCheck2 className="w-8 h-8 mx-auto mb-2 text-slate-600" />
            <p>No investigation templates configured.</p>
          </div>
        )}

        {templates.map((tmpl) => {
          const isExecuting = runningTemplateId === tmpl.template_id

          return (
            <div
              key={tmpl.template_id}
              className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-lg hover:border-slate-700 transition-all space-y-2"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded bg-cyan-950/70 border border-cyan-700/60 text-cyan-300">
                      {tmpl.analysis_mode}
                    </span>
                    <span className="text-xs font-semibold text-slate-200">{tmpl.name}</span>
                  </div>
                </div>

                <button
                  onClick={() => handleRun(tmpl.template_id)}
                  disabled={isExecuting}
                  className="px-2 py-1 rounded bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-slate-950 font-bold text-[10px] flex items-center gap-1 transition-colors shrink-0"
                >
                  <Play className="w-3 h-3 fill-current" />
                  <span>{isExecuting ? "Launching..." : "Execute"}</span>
                </button>
              </div>

              {/* Standardized Enquiry Question */}
              <div className="p-2 rounded bg-slate-900/60 border border-slate-800 text-[10px] text-slate-300 flex items-start gap-1.5">
                <HelpCircle className="w-3 h-3 text-cyan-400 shrink-0 mt-0.5" />
                <p className="italic">{tmpl.question}</p>
              </div>

              {/* Semantic Targets & Required Evidence */}
              <div className="flex items-center justify-between text-[9px] text-slate-400 pt-1 border-t border-slate-900">
                <div className="flex items-center gap-1">
                  <Layers className="w-2.5 h-2.5 text-indigo-400" />
                  <span>{tmpl.required_evidence.join(", ") || "Standard Evidence"}</span>
                </div>

                {tmpl.semantic_targets && tmpl.semantic_targets.length > 0 && (
                  <div className="flex items-center gap-1 text-cyan-400">
                    <Tag className="w-2.5 h-2.5" />
                    <span>{tmpl.semantic_targets.join(", ")}</span>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
