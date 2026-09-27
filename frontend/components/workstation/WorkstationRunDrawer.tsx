/**
 * TRINETRA Workstation — Run Drawer & Research Notebook
 * Bottom expandable tray for execution monitoring, zonal statistics, provenance manifest,
 * and scientific research notebook with minimalist glassmorphism styling.
 */

import React, { useState } from "react"
import { AnalysisRun, NotebookEntry } from "@/lib/workstation/types"
import {
  Activity,
  BookOpen,
  FileCheck,
  ChevronUp,
  ChevronDown,
  BarChart3,
  Plus,
  FileText,
  Copy,
  Check,
  Cpu,
  Layers,
  Sparkles,
} from "lucide-react"

interface Props {
  runs: AnalysisRun[]
  activeRun: AnalysisRun | null
  onSelectRun: (run: AnalysisRun) => void
  notebookEntries: NotebookEntry[]
  onAddNote: (title: string, body: string) => Promise<void>
  onMountChangeLayer?: (run: AnalysisRun) => void
}

type DrawerTab = "runs" | "outputs" | "notebook" | "provenance"

export const WorkstationRunDrawer: React.FC<Props> = ({
  runs,
  activeRun,
  onSelectRun,
  notebookEntries,
  onAddNote,
  onMountChangeLayer,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<DrawerTab>("runs")
  const [noteTitle, setNoteTitle] = useState("")
  const [noteBody, setNoteBody] = useState("")
  const [isSubmittingNote, setIsSubmittingNote] = useState(false)
  const [copiedProvenance, setCopiedProvenance] = useState(false)

  const handleCreateNote = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!noteTitle.trim()) return
    setIsSubmittingNote(true)
    try {
      await onAddNote(noteTitle, noteBody)
      setNoteTitle("")
      setNoteBody("")
    } finally {
      setIsSubmittingNote(false)
    }
  }

  const selectedRun = activeRun || (runs.length > 0 ? runs[0] : null)

  const handleAutoLogRunSummary = () => {
    if (!selectedRun) return
    const stats = selectedRun.outputs.find((o) => o.statistics)?.statistics || {}
    const pKey = (selectedRun.pipeline_key || "ANALYSIS").toUpperCase()
    const title = `EXP-${selectedRun.run_number}: ${pKey} Surface Analysis`
    const body = `Run #${selectedRun.run_number} (${pKey}) executed across ${stats.total_area_analyzed_km2 || 0} km² AOI.\n` +
      `Detected Alteration: ${stats.changed_surface_km2 || 0} km² (${stats.change_percentage || 0}% of area) with Mean Delta: ${stats.mean_delta ?? 0}.\n` +
      `Measurement Confidence: ${stats.confidence_score || 95}% (Cloud Contamination: ${stats.cloud_contamination_pct || 0}%).\n` +
      (stats.ai_interpretation ? `AI Scientific Evidence: "${stats.ai_interpretation}"` : "")
    setNoteTitle(title)
    setNoteBody(body)
  }

  const handleCopyProvenance = () => {
    const text = selectedRun?.provenance
      ? JSON.stringify(selectedRun.provenance, null, 2)
      : JSON.stringify(
          {
            engine: "TRINETRA Earth Observation Engine v2.4.0",
            digest_standard: "SHA256_STRICT_CONTAINER",
            status: "No active run provenance payload",
          },
          null,
          2
        )
    navigator.clipboard.writeText(text)
    setCopiedProvenance(true)
    setTimeout(() => setCopiedProvenance(false), 2000)
  }

  return (
    <div
      className={`border-t border-white/[0.08] bg-slate-950/75 backdrop-blur-2xl transition-all duration-300 z-30 flex flex-col select-none ${
        isOpen ? "h-80 shadow-2xl shadow-cyan-950/20" : "h-11"
      }`}
    >
      {/* Drawer Handle & Tab Bar */}
      <div className="h-11 px-4 flex items-center justify-between border-b border-white/[0.05] bg-white/[0.015] shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="flex items-center gap-2 text-xs font-semibold text-slate-200 hover:text-cyan-400 transition-colors cursor-pointer group"
          >
            <div className="w-5 h-5 rounded-md bg-white/[0.04] border border-white/[0.08] flex items-center justify-center group-hover:border-cyan-500/40">
              {isOpen ? (
                <ChevronDown className="w-3.5 h-3.5 text-cyan-400" />
              ) : (
                <ChevronUp className="w-3.5 h-3.5 text-cyan-400" />
              )}
            </div>
            <span className="uppercase tracking-widest font-mono text-[11px] text-slate-300 group-hover:text-cyan-300">
              Execution & Analytics Tray
            </span>
          </button>

          {/* Quick status pill */}
          {selectedRun ? (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-[10px] font-mono text-slate-400">Run #{selectedRun.run_number}</span>
              <span
                className={`px-2 py-0.5 rounded-full text-[9px] font-mono font-semibold uppercase tracking-wider ${
                  selectedRun.status.includes("succeeded")
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                    : selectedRun.status === "running"
                    ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 animate-pulse"
                    : "bg-white/[0.04] text-slate-400 border border-white/[0.08]"
                }`}
              >
                {selectedRun.status}
              </span>
              {selectedRun.status === "running" && (
                <div className="w-20 bg-white/[0.06] h-1 rounded-full overflow-hidden">
                  <div
                    className="bg-cyan-400 h-full transition-all duration-500 shadow-[0_0_8px_rgba(6,182,212,0.8)]"
                    style={{ width: `${selectedRun.progress_percent}%` }}
                  />
                </div>
              )}
            </div>
          ) : (
            <span className="text-[10px] font-mono text-slate-500 hidden sm:inline">
              [Idle · Standby for Run Dispatch]
            </span>
          )}
        </div>

        {/* Tab selection */}
        {isOpen && (
          <div className="flex items-center gap-1.5 bg-slate-900/60 p-1 rounded-lg border border-white/[0.06]">
            <button
              onClick={() => setActiveTab("runs")}
              className={`flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-md transition-all ${
                activeTab === "runs"
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              <span>Runs ({runs.length})</span>
            </button>
            <button
              onClick={() => setActiveTab("outputs")}
              className={`flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-md transition-all ${
                activeTab === "outputs"
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Outputs & Stats</span>
            </button>
            <button
              onClick={() => setActiveTab("notebook")}
              className={`flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-md transition-all ${
                activeTab === "notebook"
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Notebook ({notebookEntries.length})</span>
            </button>
            <button
              onClick={() => setActiveTab("provenance")}
              className={`flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-md transition-all ${
                activeTab === "provenance"
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <FileCheck className="w-3.5 h-3.5" />
              <span>Provenance</span>
            </button>
          </div>
        )}
      </div>

      {/* Expanded Tray Content */}
      {isOpen && (
        <div className="flex-1 overflow-hidden p-4">
          {/* TAB 1: RUNS & EVENT LOG */}
          {activeTab === "runs" && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 h-full">
              {/* Runs List */}
              <div className="border border-white/[0.06] rounded-xl p-3 overflow-y-auto space-y-2 bg-slate-900/30 backdrop-blur-md">
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block font-semibold">
                  Execution History ({runs.length})
                </span>
                {runs.length === 0 ? (
                  <div className="text-center py-10 px-2">
                    <Cpu className="w-6 h-6 text-slate-600 mx-auto mb-2 opacity-50" />
                    <p className="text-xs text-slate-400 font-medium">No Runs Executed</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">
                      Configure a plan in the right panel and click Execute Plan to start real computation.
                    </p>
                  </div>
                ) : (
                  runs.map((r) => (
                    <div
                      key={r.id}
                      onClick={() => onSelectRun(r)}
                      className={`p-2.5 rounded-lg border text-xs cursor-pointer transition-all ${
                        selectedRun?.id === r.id
                          ? "bg-cyan-500/15 border-cyan-500/50 shadow-sm"
                          : "bg-white/[0.02] border-white/[0.06] hover:border-white/[0.12]"
                      }`}
                    >
                      <div className="flex items-center justify-between font-bold text-slate-200">
                        <span>Run #{r.run_number}</span>
                        <span className="text-[9px] font-mono text-cyan-400 uppercase tracking-wider">
                          {r.pipeline_key}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400 flex items-center justify-between mt-1 font-mono">
                        <span className="capitalize">{r.status}</span>
                        <span>{r.created_at.split("T")[1]?.slice(0, 8) || ""}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Event Log Stream */}
              <div className="md:col-span-2 border border-white/[0.06] rounded-xl p-3.5 overflow-y-auto space-y-2 bg-slate-950/60 font-mono text-xs backdrop-blur-md">
                <div className="flex items-center justify-between pb-1 border-b border-white/[0.05]">
                  <span className="text-[10px] uppercase tracking-wider text-slate-400 font-sans font-bold">
                    Telemetry Stream — {selectedRun ? `Run #${selectedRun.run_number} (${selectedRun.id})` : "Standby"}
                  </span>
                  {selectedRun && (
                    <span className="text-[9px] px-2 py-0.5 rounded bg-white/[0.04] text-cyan-400 border border-white/[0.08]">
                      {selectedRun.events.length} events logged
                    </span>
                  )}
                </div>

                {selectedRun && selectedRun.events.length > 0 ? (
                  <div className="space-y-1.5 pt-1">
                    {selectedRun.events.map((evt, idx) => (
                      <div key={idx} className="flex items-start gap-2.5 text-[11px] text-slate-300">
                        <span className="text-cyan-400/90 shrink-0 font-mono">
                          [{evt.occurred_at.split("T")[1]?.slice(0, 8)}]
                        </span>
                        <span className="px-1.5 py-0.2 rounded text-[9px] uppercase tracking-wider bg-white/[0.05] text-slate-400 shrink-0 border border-white/[0.05]">
                          {evt.stage}
                        </span>
                        <span className="leading-snug text-slate-200">{evt.message}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-500 py-12 text-center font-sans text-xs">
                    No execution events recorded yet. Run a plan to view live telemetry.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: OUTPUTS & ZONAL STATS */}
          {activeTab === "outputs" && (
            <div className="h-full overflow-y-auto space-y-4">
              {selectedRun && selectedRun.outputs.find((o) => o.statistics && Object.keys(o.statistics).length > 0) ? (
                <>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {(() => {
                      const stats = selectedRun.outputs.find((o) => o.statistics)?.statistics || {}
                      return (
                        <>
                          <div className="p-4 bg-slate-900/40 border border-white/[0.08] rounded-xl flex flex-col justify-between backdrop-blur-md">
                            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                              Total Area Analyzed
                            </span>
                            <div className="text-2xl font-bold font-mono text-slate-100 my-2">
                              {stats.total_area_analyzed_km2 || 0}{" "}
                              <span className="text-xs font-normal text-slate-400">km²</span>
                            </div>
                            <span className="text-[10px] text-slate-500">Bounding AOI Extent (Calculated)</span>
                          </div>

                          <div className="p-4 bg-slate-900/40 border border-white/[0.08] rounded-xl flex flex-col justify-between backdrop-blur-md">
                            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                              Surface Alteration
                            </span>
                            <div className="text-2xl font-bold font-mono text-amber-400 my-2">
                              {stats.changed_surface_km2 || 0}{" "}
                              <span className="text-xs font-normal text-slate-400">km²</span>
                            </div>
                            <span className="text-[10px] text-amber-400/90 font-mono">
                              {stats.change_percentage || 0}% of AOI Affected
                            </span>
                          </div>

                          <div className="p-4 bg-slate-900/40 border border-white/[0.08] rounded-xl flex flex-col justify-between backdrop-blur-md">
                            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                              Mean Index Delta
                            </span>
                            <div className="text-2xl font-bold font-mono text-cyan-300 my-2">
                              {stats.mean_delta ?? 0}
                            </div>
                            <span className="text-[10px] text-slate-400 font-mono">
                              Metric: {stats.metric_name || "NDVI"}
                            </span>
                          </div>

                          <div className="p-4 bg-slate-900/40 border border-white/[0.08] rounded-xl flex flex-col justify-between backdrop-blur-md">
                            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                              Measurement Confidence
                            </span>
                            <div className="text-2xl font-bold font-mono text-emerald-400 my-2">
                              {stats.confidence_score ? `${stats.confidence_score}%` : `${(100 - (stats.cloud_contamination_pct || 0)).toFixed(1)}%`}
                            </div>
                            <span className="text-[10px] text-emerald-400/90 font-mono">
                              Cloud Contam: {stats.cloud_contamination_pct || 0}%
                            </span>
                          </div>
                        </>
                      )
                    })()}
                  </div>

                  {/* Multi-Class Pixel Distribution & Boundary Uncertainty Explorer */}
                  {(() => {
                    const stats = selectedRun.outputs.find((o) => o.statistics)?.statistics || {}
                    const dist = stats.pixel_distribution || {
                      positive_delta_pct: stats.change_percentage || 0,
                      negative_delta_pct: 0,
                      stable_pct: Math.max(0, 100 - (stats.change_percentage || 0)),
                      boundary_uncertainty_pct: 3.5,
                      positive_km2: stats.changed_surface_km2 || 0,
                      negative_km2: 0,
                      stable_km2: Math.max(0, (stats.total_area_analyzed_km2 || 0) - (stats.changed_surface_km2 || 0)),
                    }

                    const posPct = dist.positive_delta_pct || 0
                    const negPct = dist.negative_delta_pct || 0
                    const stablePct = dist.stable_pct || 0
                    const uncertPct = dist.boundary_uncertainty_pct || 0

                    return (
                      <div className="p-4 bg-slate-900/40 border border-white/[0.08] rounded-xl space-y-3 backdrop-blur-md">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Activity className="w-4 h-4 text-cyan-400" />
                            <span className="text-xs font-semibold text-slate-100 uppercase tracking-wider font-mono">
                              Pixel Class Allocation & Boundary Uncertainty Band
                            </span>
                          </div>
                          <span className="text-[10px] font-mono text-slate-400 bg-white/[0.03] px-2 py-0.5 rounded border border-white/[0.06]">
                            Δ Threshold Sensitivity: ±0.05
                          </span>
                        </div>

                        {/* Segmented Horizontal Distribution Bar */}
                        <div className="h-4 w-full bg-slate-950 rounded-lg overflow-hidden flex border border-white/[0.08] shadow-inner">
                          {/* Positive Alteration */}
                          <div
                            style={{ width: `${posPct}%` }}
                            className="bg-amber-400 h-full transition-all relative group"
                            title={`Positive Delta (Alteration / Inundation): ${posPct}%`}
                          />
                          {/* Negative Alteration */}
                          {negPct > 0 && (
                            <div
                              style={{ width: `${negPct}%` }}
                              className="bg-rose-500 h-full transition-all relative group"
                              title={`Negative Delta (Canopy Loss): ${negPct}%`}
                            />
                          )}
                          {/* Boundary Uncertainty Band (Hashed strip) */}
                          {uncertPct > 0 && (
                            <div
                              style={{ width: `${uncertPct}%` }}
                              className="bg-yellow-500/70 h-full relative group [background-image:repeating-linear-gradient(45deg,transparent,transparent_4px,rgba(0,0,0,0.5)_4px,rgba(0,0,0,0.5)_8px)]"
                              title={`Boundary Uncertainty Band (±0.05 around threshold): ${uncertPct}%`}
                            />
                          )}
                          {/* Stable Surface */}
                          <div
                            style={{ width: `${stablePct}%` }}
                            className="bg-slate-700/60 h-full transition-all relative group"
                            title={`Stable Surface: ${stablePct}%`}
                          />
                        </div>

                        {/* Detailed Breakdown Legend & Metrics Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 pt-1 text-[11px] font-mono">
                          {/* Pos Alteration */}
                          <div className="p-2 rounded-lg bg-black/30 border border-amber-500/20 space-y-0.5">
                            <div className="flex items-center gap-1.5 text-amber-400 text-[10px] font-semibold">
                              <span className="w-2 h-2 rounded-full bg-amber-400 shrink-0" />
                              <span>Positive Alteration</span>
                            </div>
                            <div className="text-slate-100 font-bold text-xs">{posPct}%</div>
                            <div className="text-[10px] text-slate-400">
                              {dist.positive_km2 ?? ((stats.total_area_analyzed_km2 || 0) * (posPct / 100)).toFixed(2)} km²
                            </div>
                          </div>

                          {/* Neg Alteration */}
                          <div className="p-2 rounded-lg bg-black/30 border border-rose-500/20 space-y-0.5">
                            <div className="flex items-center gap-1.5 text-rose-400 text-[10px] font-semibold">
                              <span className="w-2 h-2 rounded-full bg-rose-500 shrink-0" />
                              <span>Negative Loss</span>
                            </div>
                            <div className="text-slate-100 font-bold text-xs">{negPct}%</div>
                            <div className="text-[10px] text-slate-400">
                              {dist.negative_km2 ?? ((stats.total_area_analyzed_km2 || 0) * (negPct / 100)).toFixed(2)} km²
                            </div>
                          </div>

                          {/* Stable Surface */}
                          <div className="p-2 rounded-lg bg-black/30 border border-slate-700/40 space-y-0.5">
                            <div className="flex items-center gap-1.5 text-slate-300 text-[10px] font-semibold">
                              <span className="w-2 h-2 rounded-full bg-slate-500 shrink-0" />
                              <span>Stable Surface</span>
                            </div>
                            <div className="text-slate-100 font-bold text-xs">{stablePct}%</div>
                            <div className="text-[10px] text-slate-400">
                              {dist.stable_km2 ?? ((stats.total_area_analyzed_km2 || 0) * (stablePct / 100)).toFixed(2)} km²
                            </div>
                          </div>

                          {/* Boundary Uncertainty Band */}
                          <div className="p-2 rounded-lg bg-black/30 border border-yellow-500/30 space-y-0.5">
                            <div className="flex items-center gap-1.5 text-yellow-300 text-[10px] font-semibold">
                              <span className="w-2 h-2 rounded-sm bg-yellow-400 [background-image:repeating-linear-gradient(45deg,transparent,transparent_2px,black_2px,black_4px)] shrink-0" />
                              <span>Boundary Margin</span>
                            </div>
                            <div className="text-yellow-200 font-bold text-xs">{uncertPct}%</div>
                            <div className="text-[9px] text-yellow-400/80 leading-tight">
                              Within ±0.05 cutoff margin
                            </div>
                          </div>
                        </div>

                        <div className="text-[10px] text-slate-400/90 font-sans italic border-t border-white/[0.05] pt-1.5">
                          * Boundary margin accounts for sub-pixel spectral mixing and atmospheric variance near classification thresholds.
                        </div>
                      </div>
                    )
                  })()}

                  {/* AI Evidence Assessment Card */}
                  {(() => {
                    const stats = selectedRun.outputs.find((o) => o.statistics)?.statistics || {}
                    const debrief = stats.ai_interpretation
                    if (!debrief) return null
                    return (
                      <div className="p-3.5 rounded-xl bg-gradient-to-r from-cyan-950/40 to-slate-900/40 border border-cyan-500/20 backdrop-blur-md space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5 text-cyan-300 text-xs font-semibold">
                            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                            <span>AI Scientific Evidence Brief</span>
                          </div>
                          <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-800/40 text-cyan-300">
                            GEMINI EO SYNTHESIS
                          </span>
                        </div>
                        <p className="text-xs text-slate-200 leading-relaxed font-sans">{debrief}</p>
                        <div className="pt-1 flex items-center justify-end">
                          <button
                            onClick={() => onAddNote(`Debrief: Run #${selectedRun.run_number}`, debrief)}
                            className="text-[10px] font-mono text-cyan-400 hover:text-cyan-200 flex items-center gap-1 px-2.5 py-1 rounded bg-white/[0.03] hover:bg-white/[0.08] transition-colors border border-white/[0.05] cursor-pointer"
                          >
                            <Plus className="w-3 h-3" />
                            <span>Save to Research Notebook</span>
                          </button>
                        </div>
                      </div>
                    )
                  })()}

                  {/* ARD GeoTIFF Change Raster Download & Mount */}
                  {selectedRun.outputs.find((o) => o.output_type === "raster") && (
                    <div className="flex items-center justify-between p-3 rounded-xl bg-amber-950/20 border border-amber-500/30 text-xs">
                      <div className="flex items-center gap-2.5">
                        <Layers className="w-4 h-4 text-amber-400 shrink-0" />
                        <div>
                          <div className="font-semibold text-amber-200 text-xs">
                            Analysis-Ready GeoTIFF Change Map
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono">
                            Co-registered single-band radiometric difference raster with georeferenced spatial bounds
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <a
                          href={`/api/v1/workstation/runs/${selectedRun.id}/outputs/raster`}
                          download={`trinetra_change_${selectedRun.id}.tif`}
                          className="px-2.5 py-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-slate-200 text-[11px] font-mono border border-white/[0.1] transition-colors"
                        >
                          Download .TIF
                        </a>
                        {onMountChangeLayer && (
                          <button
                            onClick={() => onMountChangeLayer(selectedRun)}
                            className="px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-[11px] font-semibold transition-all shadow-sm cursor-pointer flex items-center gap-1.5"
                          >
                            <Layers className="w-3.5 h-3.5" />
                            <span>Mount on Map</span>
                          </button>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Quality & Preflight Flags */}
                  {(() => {
                    const statsOut = selectedRun.outputs.find((o) => o.statistics)
                    const flags = statsOut?.quality_flags || []
                    if (flags.length === 0) return null
                    return (
                      <div className="flex flex-wrap items-center gap-1.5 pt-1">
                        <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
                          Preprocessing & ARD Flags:
                        </span>
                        {flags.map((flag, idx) => (
                          <span
                            key={idx}
                            className="text-[9px] font-mono px-2 py-0.5 rounded-md bg-emerald-950/40 border border-emerald-800/40 text-emerald-300"
                          >
                            ✓ {flag.replace(/_/g, " ")}
                          </span>
                        ))}
                      </div>
                    )
                  })()}
                </>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 border border-white/[0.06] rounded-xl bg-slate-900/20 backdrop-blur-md">
                  <BarChart3 className="w-8 h-8 text-slate-600 mb-2 opacity-50" />
                  <p className="text-xs text-slate-300 font-medium">No Analysis Outputs or Zonal Statistics</p>
                  <p className="text-[11px] text-slate-500 max-w-sm mt-1">
                    Upload satellite rasters, define an AOI, and execute an analysis pipeline to view genuine zonal statistics, alteration metrics, and raster differencing data.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: NOTEBOOK */}
          {activeTab === "notebook" && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 h-full">
              {/* Form */}
              <form
                onSubmit={handleCreateNote}
                className="space-y-2.5 border-b md:border-b-0 md:border-r border-white/[0.08] pr-0 md:pr-4 flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
                      Researcher Log & Annotation
                    </span>
                    {selectedRun && (
                      <button
                        type="button"
                        onClick={handleAutoLogRunSummary}
                        className="text-[9px] font-mono text-cyan-400 hover:text-cyan-200 bg-cyan-950/40 hover:bg-cyan-900/40 px-2 py-0.5 rounded border border-cyan-800/40 cursor-pointer transition-colors"
                        title="Fill form with current run zonal statistics and evidence brief"
                      >
                        + Summarize Run #{selectedRun.run_number}
                      </button>
                    )}
                  </div>
                  <input
                    type="text"
                    required
                    placeholder="Observation title..."
                    value={noteTitle}
                    onChange={(e) => setNoteTitle(e.target.value)}
                    className="w-full bg-slate-900/50 border border-white/[0.08] rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/60"
                  />
                  <textarea
                    rows={3}
                    required
                    placeholder="Document scientific findings, anomalous pixel patterns, or field notes..."
                    value={noteBody}
                    onChange={(e) => setNoteBody(e.target.value)}
                    className="w-full bg-slate-900/50 border border-white/[0.08] rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/60 resize-none"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isSubmittingNote}
                  className="w-full py-1.5 px-3 bg-cyan-600/30 hover:bg-cyan-500/40 border border-cyan-500/50 text-cyan-200 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all cursor-pointer disabled:opacity-50"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>{isSubmittingNote ? "Logging..." : "Append to Research Journal"}</span>
                </button>
              </form>

              {/* Entries Timeline */}
              <div className="md:col-span-2 overflow-y-auto space-y-2.5 pl-0 md:pl-2">
                {notebookEntries.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center p-6 border border-white/[0.06] rounded-xl bg-slate-900/20 backdrop-blur-md">
                    <BookOpen className="w-7 h-7 text-slate-600 mb-2 opacity-50" />
                    <p className="text-xs text-slate-300 font-medium">Research Journal is Empty</p>
                    <p className="text-[11px] text-slate-500 max-w-sm mt-0.5">
                      Log field notes, hypothesis validations, or analytical anomalies to maintain an audit trail for your mission.
                    </p>
                  </div>
                ) : (
                  notebookEntries.map((nb) => {
                    const isExperiment =
                      nb.title.startsWith("Debrief:") ||
                      nb.title.startsWith("EXP-") ||
                      nb.title.startsWith("Run #")
                    return (
                      <div
                        key={nb.id}
                        className={`p-3.5 rounded-xl space-y-2 backdrop-blur-md border transition-all ${
                          isExperiment
                            ? "bg-cyan-950/20 border-cyan-500/30 shadow-sm"
                            : "bg-slate-900/40 border-white/[0.08]"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {isExperiment ? (
                              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                            ) : (
                              <FileText className="w-3.5 h-3.5 text-slate-400" />
                            )}
                            <span className="text-xs font-bold text-slate-100">{nb.title}</span>
                            {isExperiment && (
                              <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-cyan-950/60 border border-cyan-800/40 text-cyan-300 uppercase">
                                Experiment Audit Record
                              </span>
                            )}
                          </div>
                          <span className="text-[9px] font-mono text-slate-400">
                            {nb.created_at.split("T")[0]} · {nb.created_at.split("T")[1]?.slice(0, 8)}
                          </span>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed font-sans whitespace-pre-line">
                          {nb.body}
                        </p>
                      </div>
                    )
                  })
                )}
              </div>
            </div>
          )}

          {/* TAB 4: PROVENANCE MANIFEST */}
          {activeTab === "provenance" && (
            <div className="h-full flex flex-col border border-white/[0.06] rounded-xl bg-slate-950/60 backdrop-blur-md overflow-hidden">
              <div className="px-4 py-2 border-b border-white/[0.06] flex items-center justify-between bg-white/[0.02]">
                <div className="flex items-center gap-2">
                  <FileCheck className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs font-mono font-semibold text-slate-200">
                    Immutable Provenance Manifest (SHA-256 Strict)
                  </span>
                </div>
                <button
                  onClick={handleCopyProvenance}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-[10px] font-mono text-slate-300 transition-colors cursor-pointer"
                >
                  {copiedProvenance ? (
                    <>
                      <Check className="w-3 h-3 text-emerald-400" />
                      <span className="text-emerald-400">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3 text-slate-400" />
                      <span>Copy JSON</span>
                    </>
                  )}
                </button>
              </div>
              <div className="flex-1 p-3 overflow-y-auto font-mono text-[11px] text-cyan-300/90 leading-relaxed bg-black/40">
                <pre>
                  {selectedRun?.provenance
                    ? JSON.stringify(selectedRun.provenance, null, 2)
                    : JSON.stringify(
                        {
                          message: "Select an executed run to inspect its strict container and input raster hashes.",
                          engine: "TRINETRA Earth Observation Engine v2.4.0",
                          standard: "OGC & ISO 19115 Provenance Spec",
                          status: "Awaiting execution trigger",
                        },
                        null,
                        2
                      )}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

