/**
 * TRINETRA Phase 6 — LangGraph Chain of Thought (CoT) Workstation View
 * Displays multi-specialist internal reasoning traces, sensor observations,
 * analytical deductions, and model predictions across the LangGraph pipeline.
 */

import React, { useState } from "react"
import {
  ChainOfThoughtStep,
  SpecialistModelType,
  InvestigationItem,
} from "@/lib/explore/investigation-types"
import {
  BrainCircuit,
  Cpu,
  Eye,
  Radio,
  Layers,
  Compass,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Activity,
  ShieldCheck,
  Workflow,
  MapPin,
  Bot,
  CheckCircle2,
  SlidersHorizontal,
} from "lucide-react"

interface Props {
  investigation?: InvestigationItem
  steps?: ChainOfThoughtStep[]
  isCompact?: boolean
  title?: string
  subtitle?: string
}

const MODEL_CONFIGS: Record<
  SpecialistModelType,
  { label: string; icon: React.FC<{ className?: string }>; color: string; badgeBg: string; border: string; text: string }
> = {
  router: {
    label: "Router",
    icon: Compass,
    color: "from-blue-500/20 to-indigo-500/20",
    badgeBg: "bg-blue-950/80",
    border: "border-blue-700/60",
    text: "text-blue-400",
  },
  vision: {
    label: "Vision",
    icon: Eye,
    color: "from-cyan-500/20 to-teal-500/20",
    badgeBg: "bg-cyan-950/80",
    border: "border-cyan-700/60",
    text: "text-cyan-400",
  },
  sar: {
    label: "SAR Radar",
    icon: Radio,
    color: "from-amber-500/20 to-orange-500/20",
    badgeBg: "bg-amber-950/80",
    border: "border-amber-700/60",
    text: "text-amber-400",
  },
  spectral: {
    label: "Spectral",
    icon: Layers,
    color: "from-emerald-500/20 to-green-500/20",
    badgeBg: "bg-emerald-950/80",
    border: "border-emerald-700/60",
    text: "text-emerald-400",
  },
  gis: {
    label: "GIS Topology",
    icon: MapPin,
    color: "from-purple-500/20 to-violet-500/20",
    badgeBg: "bg-purple-950/80",
    border: "border-purple-700/60",
    text: "text-purple-400",
  },
  fusion: {
    label: "Fusion",
    icon: Workflow,
    color: "from-rose-500/20 to-pink-500/20",
    badgeBg: "bg-rose-950/80",
    border: "border-rose-700/60",
    text: "text-rose-400",
  },
  classifier: {
    label: "Classifier",
    icon: Cpu,
    color: "from-yellow-500/20 to-amber-500/20",
    badgeBg: "bg-yellow-950/80",
    border: "border-yellow-700/60",
    text: "text-yellow-400",
  },
  reasoning: {
    label: "Executive Reasoner",
    icon: BrainCircuit,
    color: "from-orange-500/20 to-rose-500/20",
    badgeBg: "bg-orange-950/80",
    border: "border-orange-700/60",
    text: "text-orange-400",
  },
}

export const ChainOfThoughtView: React.FC<Props> = ({
  investigation,
  steps: explicitSteps,
  isCompact = false,
  title,
  subtitle,
}) => {
  const steps: ChainOfThoughtStep[] = explicitSteps || investigation?.chain_of_thought || []
  const [filterType, setFilterType] = useState<string>("ALL")
  const [expandedSteps, setExpandedSteps] = useState<Record<number, boolean>>(() => {
    // By default expand first two and last step
    const map: Record<number, boolean> = {}
    steps.forEach((s, idx) => {
      map[s.step_number] = idx < 2 || idx === steps.length - 1
    })
    return map
  })

  const toggleStep = (stepNumber: number) => {
    setExpandedSteps((prev) => ({
      ...prev,
      [stepNumber]: !prev[stepNumber],
    }))
  }

  const expandAll = () => {
    const map: Record<number, boolean> = {}
    steps.forEach((s) => {
      map[s.step_number] = true
    })
    setExpandedSteps(map)
  }

  const collapseAll = () => {
    setExpandedSteps({})
  }

  const filteredSteps = steps.filter((step) => {
    if (filterType === "ALL") return true
    return step.model_type.toUpperCase() === filterType.toUpperCase()
  })

  // If no steps exist yet, synthesize preview steps based on plan and findings
  if (steps.length === 0) {
    return (
      <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-4 space-y-3 font-sans">
        <div className="flex items-center gap-2">
          <BrainCircuit className="w-4 h-4 text-orange-400 animate-pulse" />
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wide font-mono">
            {title || "Chain of Thought Reasoning Trace"}
          </h3>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed font-mono">
          {subtitle || "LangGraph reasoning trace is pending or executing. Run an analysis or enquiry to view real-time specialist deductions."}
        </p>
      </div>
    )
  }

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-4 space-y-3 font-sans">
      {/* View Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
        <div className="flex items-center gap-2">
          <div className="p-1 rounded bg-orange-950/60 border border-orange-700/60">
            <BrainCircuit className="w-4 h-4 text-orange-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-bold text-slate-100 uppercase tracking-wide font-mono">
                {title || "Chain of Thought Reasoning Trace"}
              </h3>
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 font-mono">
                {steps.length} Steps
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-sans">
              {subtitle || "Chronological LangGraph telemetry across specialized vision, radar, and biophysical models."}
            </p>
          </div>
        </div>

        {/* Global Controls */}
        <div className="flex items-center gap-1.5 text-[11px] font-mono">
          <button
            onClick={expandAll}
            className="px-2 py-0.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
          >
            Expand All
          </button>
          <button
            onClick={collapseAll}
            className="px-2 py-0.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-400 border border-slate-700 transition-colors"
          >
            Collapse All
          </button>
        </div>
      </div>

      {/* Model Filter Bar (Full view only) */}
      {!isCompact && (
        <div className="flex items-center gap-1 overflow-x-auto pb-1 text-[10px] font-mono">
          <span className="text-slate-500 flex items-center gap-1 mr-1">
            <SlidersHorizontal className="w-3 h-3" /> Filter:
          </span>
          {["ALL", "ROUTER", "VISION", "SAR", "SPECTRAL", "GIS", "FUSION", "CLASSIFIER", "REASONING"].map((type) => {
            const active = filterType === type
            return (
              <button
                key={type}
                onClick={() => setFilterType(type)}
                className={`px-2 py-0.5 rounded transition-all whitespace-nowrap ${
                  active
                    ? "bg-orange-950 text-orange-300 border border-orange-700/70 font-bold"
                    : "bg-slate-800/50 hover:bg-slate-800 text-slate-400 hover:text-slate-200"
                }`}
              >
                {type}
              </button>
            )
          })}
        </div>
      )}

      {/* Stepper Timeline Container */}
      <div className="relative pl-6 space-y-3 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-gradient-to-b before:from-orange-500/80 before:via-cyan-500/60 before:to-emerald-500/80">
        {filteredSteps.map((step) => {
          const config = MODEL_CONFIGS[step.model_type] || MODEL_CONFIGS.reasoning
          const Icon = config.icon
          const isExpanded = !!expandedSteps[step.step_number]
          const confPercent = Math.round((step.confidence || 0.9) * 100)

          return (
            <div
              key={step.step_number}
              className="relative bg-slate-950/70 hover:bg-slate-950/90 border border-slate-800 rounded-lg transition-all shadow-sm group"
            >
              {/* Stepper Pin */}
              <div
                className={`absolute -left-[27px] top-3.5 w-5 h-5 rounded-full flex items-center justify-center font-mono text-[10px] font-bold border ${config.badgeBg} ${config.border} ${config.text} shadow-md`}
              >
                {step.step_number}
              </div>

              {/* Step Header (Click to toggle) */}
              <div
                onClick={() => toggleStep(step.step_number)}
                className="p-3 cursor-pointer flex items-center justify-between select-none"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold border ${config.badgeBg} ${config.border} ${config.text}`}>
                    <Icon className="w-3 h-3" />
                    <span>{step.agent_role}</span>
                  </span>

                  <span className="text-xs font-semibold text-slate-200 truncate">
                    {step.stage}
                  </span>
                </div>

                <div className="flex items-center gap-2 shrink-0 ml-2">
                  {/* Model Name Badge */}
                  <span className="text-[10px] font-mono text-slate-400 px-1.5 py-0.5 rounded bg-slate-800/80 border border-slate-700/60 hidden sm:inline-block">
                    {step.model_name}
                  </span>

                  {/* Confidence Pill */}
                  <span
                    className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${
                      confPercent >= 90
                        ? "bg-emerald-950/60 text-emerald-300 border-emerald-800"
                        : confPercent >= 75
                        ? "bg-amber-950/60 text-amber-300 border-amber-800"
                        : "bg-slate-800 text-slate-300 border-slate-700"
                    }`}
                  >
                    {confPercent}%
                  </span>

                  {isExpanded ? (
                    <ChevronUp className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-200" />
                  ) : (
                    <ChevronDown className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-200" />
                  )}
                </div>
              </div>

              {/* Expandable Body */}
              {isExpanded && (
                <div className="px-3 pb-3 pt-0 space-y-2.5 border-t border-slate-800/60 mt-1">
                  {/* Input Context Pill */}
                  {step.input_summary && (
                    <div className="pt-2 flex items-center gap-1.5 text-[11px] font-mono text-slate-400">
                      <span className="text-[10px] uppercase font-bold text-slate-500">Input:</span>
                      <span className="text-slate-300 truncate">{step.input_summary}</span>
                    </div>
                  )}

                  {/* Raw Observation */}
                  <div className="space-y-1">
                    <span className="text-[10px] uppercase font-mono font-bold text-slate-400 flex items-center gap-1">
                      <Eye className="w-3 h-3 text-cyan-400" /> Raw Telemetry Observation
                    </span>
                    <p className="text-xs text-slate-300 bg-slate-900/80 p-2 rounded border border-slate-800 leading-relaxed font-sans">
                      {step.observation}
                    </p>
                  </div>

                  {/* Internal Reasoning (CoT) Callout */}
                  <div className="space-y-1">
                    <span className="text-[10px] uppercase font-mono font-bold text-orange-400 flex items-center gap-1">
                      <BrainCircuit className="w-3 h-3 text-orange-400" /> Model Thought Process (CoT)
                    </span>
                    <div className="bg-orange-950/20 border-l-2 border-orange-500 p-2.5 rounded-r text-xs text-orange-200/90 leading-relaxed font-sans">
                      {step.thought_process}
                    </div>
                  </div>

                  {/* Output Prediction / Deduction */}
                  <div className="space-y-1">
                    <span className="text-[10px] uppercase font-mono font-bold text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Model Prediction & Deduction
                    </span>
                    <div className="bg-emerald-950/20 border border-emerald-800/40 p-2 rounded text-xs text-emerald-200/95 font-medium leading-relaxed">
                      {step.prediction}
                    </div>
                  </div>

                  {/* Metrics Badges */}
                  {step.metrics && Object.keys(step.metrics).length > 0 && (
                    <div className="pt-1 flex flex-wrap items-center gap-1.5">
                      <span className="text-[10px] font-mono uppercase text-slate-500 mr-1">
                        Metrics:
                      </span>
                      {Object.entries(step.metrics).map(([k, v]) => {
                        const valStr = typeof v === "object" ? JSON.stringify(v) : String(v)
                        return (
                          <div
                            key={k}
                            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-slate-800/90 border border-slate-700 text-[10px] font-mono text-slate-300"
                          >
                            <span className="text-slate-400">{k}:</span>
                            <span className="font-semibold text-slate-100">{valStr}</span>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
