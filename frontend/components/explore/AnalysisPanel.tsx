/**
 * TRINETRA — Phase 5: Analytical Intelligence Workstation Panel
 * Main interactive analysis console for the Explore sidebar.
 */

import React, { useState, useEffect } from "react"
import { useAnalysisState } from "@/lib/explore/analysis-state"
import { AnalysisMode, ObservationSummary } from "@/lib/explore/types"
import { AnalysisModeBadge } from "./AnalysisModeBadge"
import { AnalysisProgress } from "./AnalysisProgress"
import { FindingsPanel } from "./FindingsPanel"
import { EvidencePanel } from "./EvidencePanel"
import { LimitationPanel } from "./LimitationPanel"
import { AnalysisArtifacts } from "./AnalysisArtifacts"
import { ChangeStatistics } from "./ChangeStatistics"
import { ChangeLegend } from "./ChangeLegend"
import {
  BrainCircuit,
  Play,
  XCircle,
  FileText,
  Binary,
  Layers,
  AlertTriangle,
  FolderDown,
  RotateCcw,
  Clock,
  Sparkles,
  HelpCircle,
} from "lucide-react"

interface Props {
  selectedObservation?: ObservationSummary | null
  comparisonObservationA?: ObservationSummary | null
  comparisonObservationB?: ObservationSummary | null
  aoiGeometry?: Record<string, any> | null
}

const EXAMPLE_PROMPTS = [
  { label: "Urban Expansion", query: "Detect built-up change and new construction between observations", mode: "BI_TEMPORAL" as AnalysisMode },
  { label: "Flood Inundation", query: "Evaluate flood water extent using radar penetration and optical reflectance", mode: "SAR_OPTICAL" as AnalysisMode },
  { label: "Airfield Inspection", query: "Detect and count all aircraft and vehicles on the runway", mode: "SINGLE_IMAGE" as AnalysisMode },
]

export const AnalysisPanel: React.FC<Props> = ({
  selectedObservation,
  comparisonObservationA,
  comparisonObservationB,
  aoiGeometry,
}) => {
  const {
    activeRun,
    activeResult,
    selectedFindingId,
    isAnalyzing,
    validation,
    isValidating,
    error,
    startAnalysis,
    cancelCurrentRun,
    validateRequest,
    selectFinding,
    reset,
  } = useAnalysisState()

  const [query, setQuery] = useState<string>("")
  const [mode, setMode] = useState<AnalysisMode>("BI_TEMPORAL")
  const [activeTab, setActiveTab] = useState<"findings" | "narrative" | "evidence" | "artifacts" | "limitations">("findings")

  // Derive observation IDs
  const obsAId = comparisonObservationA?.id || selectedObservation?.id || ""
  const obsBId = comparisonObservationB?.id || ""

  // Automatically update mode based on available observations
  useEffect(() => {
    if (comparisonObservationA && comparisonObservationB) {
      const isSarA = comparisonObservationA.sensor_type?.toLowerCase() === "sar" || comparisonObservationA.collection?.toLowerCase().includes("sentinel-1")
      const isSarB = comparisonObservationB.sensor_type?.toLowerCase() === "sar" || comparisonObservationB.collection?.toLowerCase().includes("sentinel-1")
      if ((isSarA && !isSarB) || (!isSarA && isSarB)) {
        setMode("SAR_OPTICAL")
      } else {
        setMode("BI_TEMPORAL")
      }
    } else if (selectedObservation && !comparisonObservationB) {
      setMode("SINGLE_IMAGE")
    }
  }, [selectedObservation, comparisonObservationA, comparisonObservationB])

  const handleRun = async () => {
    if (!query.trim()) return

    await startAnalysis({
      query: query.trim(),
      mode,
      observation_a_id: obsAId || undefined,
      observation_b_id: obsBId || undefined,
      aoi: aoiGeometry || undefined,
    })
  }

  const handleValidate = async () => {
    if (!query.trim()) return
    await validateRequest({
      query: query.trim(),
      mode,
      observation_a_id: obsAId || undefined,
      observation_b_id: obsBId || undefined,
      aoi: aoiGeometry || undefined,
    })
  }

  return (
    <div className="flex flex-col h-full space-y-3 p-3 overflow-y-auto bg-slate-950/60 font-sans">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <BrainCircuit className="w-5 h-5 text-cyan-400" />
          <h3 className="font-semibold text-sm text-slate-100 uppercase tracking-wider font-mono">
            EO Analytical Engine
          </h3>
        </div>
        {activeResult && (
          <button
            onClick={reset}
            className="flex items-center gap-1 text-[11px] font-mono text-slate-400 hover:text-slate-200 px-2 py-0.5 rounded bg-slate-800/80 hover:bg-slate-800 border border-slate-700 transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            New
          </button>
        )}
      </div>

      {/* Input Section (When not actively showing results) */}
      {!activeResult && (
        <div className="space-y-3">
          {/* Query input */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center justify-between font-mono">
              <span>Analytical Objective / Query</span>
              <span className="text-[10px] text-slate-500 font-normal">Natural language</span>
            </label>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. Detect urban growth, calculate flood extent, or ground runways..."
              className="w-full h-20 p-2.5 bg-slate-900/90 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500/50 resize-none font-sans"
            />
          </div>

          {/* Quick prompt suggestions */}
          <div className="flex flex-wrap gap-1.5">
            {EXAMPLE_PROMPTS.map((p) => (
              <button
                key={p.label}
                onClick={() => {
                  setQuery(p.query)
                  setMode(p.mode)
                }}
                className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900 border border-slate-800 text-slate-400 hover:text-cyan-300 hover:border-cyan-500/30 transition-all flex items-center gap-1"
              >
                <Sparkles className="w-2.5 h-2.5 text-cyan-400" />
                {p.label}
              </button>
            ))}
          </div>

          {/* Mode Selector */}
          <div className="space-y-1.5 pt-1">
            <label className="text-xs font-semibold text-slate-300 font-mono">Analytical Pipeline Mode</label>
            <div className="grid grid-cols-3 gap-1.5">
              {(["BI_TEMPORAL", "SAR_OPTICAL", "SINGLE_IMAGE"] as AnalysisMode[]).map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={`py-1.5 px-2 rounded text-[10px] font-mono font-medium border transition-all text-center ${
                    mode === m
                      ? "bg-cyan-950/60 border-cyan-500 text-cyan-300 shadow-[0_0_10px_rgba(6,182,212,0.2)]"
                      : "bg-slate-900/50 border-slate-800 text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                  }`}
                >
                  {m === "BI_TEMPORAL" ? "Bi-Temporal" : m === "SAR_OPTICAL" ? "SAR+Optical" : "Single Image"}
                </button>
              ))}
            </div>
          </div>

          {/* Context Observations Summary */}
          <div className="p-2 bg-slate-900/40 border border-slate-800/80 rounded-lg text-[11px] font-mono space-y-1">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-slate-500">Observation A:</span>
              <span className="text-slate-300 font-semibold truncate max-w-[160px]">
                {obsAId || "None selected"}
              </span>
            </div>
            {mode !== "SINGLE_IMAGE" && (
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-slate-500">Observation B:</span>
                <span className="text-slate-300 font-semibold truncate max-w-[160px]">
                  {obsBId || "None selected"}
                </span>
              </div>
            )}
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-slate-500">Spatial AOI:</span>
              <span className="text-emerald-400">
                {aoiGeometry ? "User Defined AOI" : "Full Scene Bounds"}
              </span>
            </div>
          </div>

          {/* Validation info */}
          {validation && (
            <div
              className={`p-2 rounded text-[11px] font-mono border ${
                validation.valid
                  ? "bg-emerald-950/20 border-emerald-500/30 text-emerald-300"
                  : "bg-rose-950/20 border-rose-500/30 text-rose-300"
              }`}
            >
              <div className="flex items-center justify-between">
                <span>{validation.valid ? "Feasibility Check Passed" : "Check Failed"}</span>
                <span>~{validation.estimated_runtime_seconds}s</span>
              </div>
              {validation.warnings.length > 0 && (
                <p className="text-[10px] text-amber-400 mt-1">{validation.warnings[0]}</p>
              )}
            </div>
          )}

          {/* Error display */}
          {error && (
            <div className="p-2.5 bg-rose-950/30 border border-rose-500/40 rounded-lg text-xs font-mono text-rose-300 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div className="space-y-0.5">
                <p className="font-semibold">Analysis Failed</p>
                <p className="text-[11px] leading-snug text-rose-200/90">{error}</p>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="pt-2 flex items-center gap-2">
            <button
              onClick={handleRun}
              disabled={isAnalyzing || !query.trim()}
              className="flex-1 py-2 px-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:from-slate-800 disabled:to-slate-800 disabled:text-slate-600 text-white font-mono text-xs font-semibold rounded-lg shadow-lg shadow-cyan-950/50 flex items-center justify-center gap-2 transition-all"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              Execute Analytical Engine
            </button>
            <button
              onClick={handleValidate}
              disabled={isValidating || !query.trim()}
              title="Pre-flight validation check"
              className="p-2 bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200 rounded-lg text-xs font-mono transition-colors"
            >
              <HelpCircle className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Progress View */}
      {activeRun && isAnalyzing && (
        <AnalysisProgress
          progress={activeRun.progress}
          status={activeRun.status}
          onCancel={cancelCurrentRun}
        />
      )}

      {/* Completed Results View */}
      {activeResult && (
        <div className="space-y-3">
          {/* Result Metadata Header */}
          <div className="p-2.5 bg-slate-900/80 border border-slate-800 rounded-lg space-y-1.5">
            <div className="flex items-center justify-between">
              <AnalysisModeBadge mode={activeResult.mode} />
              <span className="flex items-center gap-1 text-[11px] font-mono text-slate-400">
                <Clock className="w-3 h-3 text-cyan-400" />
                {activeResult.execution_time_seconds.toFixed(2)}s
              </span>
            </div>
            <p className="text-xs text-slate-200 font-semibold leading-snug">
              {activeResult.query}
            </p>
          </div>

          {/* Tab Switcher */}
          <div className="flex items-center border-b border-slate-800 text-xs font-mono">
            <button
              onClick={() => setActiveTab("findings")}
              className={`pb-1.5 px-2.5 font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === "findings"
                  ? "border-b-2 border-cyan-400 text-cyan-300"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              Findings ({activeResult.findings?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab("evidence")}
              className={`pb-1.5 px-2.5 font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === "evidence"
                  ? "border-b-2 border-cyan-400 text-cyan-300"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Binary className="w-3.5 h-3.5" />
              Evidence
            </button>
            <button
              onClick={() => setActiveTab("narrative")}
              className={`pb-1.5 px-2.5 font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === "narrative"
                  ? "border-b-2 border-cyan-400 text-cyan-300"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              Report
            </button>
            <button
              onClick={() => setActiveTab("artifacts")}
              className={`pb-1.5 px-2.5 font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === "artifacts"
                  ? "border-b-2 border-cyan-400 text-cyan-300"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <FolderDown className="w-3.5 h-3.5" />
              Files
            </button>
            <button
              onClick={() => setActiveTab("limitations")}
              className={`pb-1.5 px-2.5 font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === "limitations"
                  ? "border-b-2 border-cyan-400 text-cyan-300"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              Limits
            </button>
          </div>

          {/* Tab Contents */}
          {activeTab === "findings" && (
            <div className="space-y-3">
              {activeResult.mode === "BI_TEMPORAL" && (
                <>
                  <ChangeStatistics statistics={activeResult.evidence?.statistics || {}} />
                  <ChangeLegend />
                </>
              )}
              <FindingsPanel
                findings={activeResult.findings}
                selectedFindingId={selectedFindingId}
                onSelectFinding={selectFinding}
              />
            </div>
          )}

          {activeTab === "evidence" && (
            <EvidencePanel evidence={activeResult.evidence} query={activeResult.query} />
          )}

          {activeTab === "narrative" && (
            <div className="space-y-3 text-xs leading-relaxed text-slate-300 bg-slate-900/50 p-3 rounded-lg border border-slate-800">
              <div className="space-y-1">
                <h4 className="text-[11px] font-mono font-semibold uppercase tracking-wider text-cyan-400">
                  Executive Summary
                </h4>
                <p className="text-slate-200">
                  {activeResult.narrative?.executive_summary ||
                    "Analysis completed with verifiable evidence extraction."}
                </p>
              </div>

              {activeResult.narrative?.methodology && (
                <div className="space-y-1 pt-2 border-t border-slate-800">
                  <h4 className="text-[11px] font-mono font-semibold uppercase tracking-wider text-slate-400">
                    Analytical Methodology
                  </h4>
                  <p className="text-slate-300 text-[11px]">
                    {activeResult.narrative.methodology}
                  </p>
                </div>
              )}

              {activeResult.narrative?.confidence_explanation && (
                <div className="space-y-1 pt-2 border-t border-slate-800">
                  <h4 className="text-[11px] font-mono font-semibold uppercase tracking-wider text-slate-400">
                    Confidence Calibration
                  </h4>
                  <p className="text-slate-300 text-[11px]">
                    {activeResult.narrative.confidence_explanation}
                  </p>
                </div>
              )}
            </div>
          )}

          {activeTab === "artifacts" && (
            <AnalysisArtifacts
              artifacts={activeResult.artifacts}
              runId={activeResult.run_id}
            />
          )}

          {activeTab === "limitations" && (
            <LimitationPanel limitations={activeResult.limitations} />
          )}
        </div>
      )}
    </div>
  )
}
