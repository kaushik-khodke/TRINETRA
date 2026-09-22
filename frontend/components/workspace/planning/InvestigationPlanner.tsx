"use client"

import React, { useState } from "react"
import {
  Layers,
  Play,
  Plus,
  ArrowRight,
  CheckCircle2,
  Clock,
  AlertCircle,
  ChevronRight,
  ShieldCheck,
} from "lucide-react"
import { InvestigationPlan, InvestigationStep, PlanRun, PlanStatus } from "@/lib/explore/workspace-types"

interface InvestigationPlannerProps {
  plans: InvestigationPlan[]
  onCreatePlan: (plan: Partial<InvestigationPlan>) => Promise<any>
  onExecutePlan: (planId: string) => Promise<any>
}

export function InvestigationPlanner({ plans, onCreatePlan, onExecutePlan }: InvestigationPlannerProps) {
  const [selectedPlan, setSelectedPlan] = useState<InvestigationPlan | null>(plans[0] || null)
  const [executing, setExecuting] = useState(false)
  const [newModalOpen, setNewModalOpen] = useState(false)
  const [title, setTitle] = useState("")
  const [question, setQuestion] = useState("")

  const handleExecute = async (planId: string) => {
    setExecuting(true)
    try {
      await onExecutePlan(planId)
    } finally {
      setExecuting(false)
    }
  }

  const handleCreatePlan = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || !question.trim()) return

    const defaultSteps: InvestigationStep[] = [
      {
        step_id: "s-fetch",
        type: "OBSERVATION_SEARCH",
        depends_on: [],
        parameters: { query: "Sentinel-2 L2A optical scenes" },
        status: "PENDING",
      },
      {
        step_id: "s-change",
        type: "ANALYZE_BITEMPORAL",
        depends_on: ["s-fetch"],
        parameters: { method: "NDVI_DIFFERENCE", threshold: 0.15 },
        status: "PENDING",
      },
      {
        step_id: "s-synth",
        type: "BUILD_SYNTHESIS",
        depends_on: ["s-change"],
        parameters: {},
        status: "PENDING",
      },
    ]

    const created = await onCreatePlan({
      title: title.trim(),
      question: question.trim(),
      steps: defaultSteps,
    })
    setSelectedPlan(created)
    setTitle("")
    setQuestion("")
    setNewModalOpen(false)
  }

  return (
    <div className="p-4 space-y-4 text-slate-200">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
            <Layers size={15} className="text-sky-400" /> Directed Acyclic Graph (DAG) Plans
          </h3>
          <p className="text-[11px] text-slate-400">Multi-step analytical workflows with topological dependencies</p>
        </div>
        <button
          onClick={() => setNewModalOpen(true)}
          className="flex items-center gap-1 text-xs bg-sky-600 hover:bg-sky-500 text-white px-2.5 py-1 rounded transition"
        >
          <Plus size={13} /> New Plan
        </button>
      </div>

      {plans.length === 0 ? (
        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-6 text-center text-xs text-slate-500 space-y-2">
          <p>No investigation plans configured yet.</p>
          <button
            onClick={() => setNewModalOpen(true)}
            className="text-sky-400 hover:underline inline-block"
          >
            Create your first workflow plan &rarr;
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {/* Plan Selector */}
          <div className="flex gap-2 overflow-x-auto pb-1">
            {plans.map((p) => (
              <button
                key={p.plan_id}
                onClick={() => setSelectedPlan(p)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap border transition ${
                  selectedPlan?.plan_id === p.plan_id
                    ? "bg-slate-800 border-sky-500 text-sky-300"
                    : "bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200"
                }`}
              >
                {p.title}
              </button>
            ))}
          </div>

          {selectedPlan && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="text-sm font-bold text-slate-100">{selectedPlan.title}</h4>
                  <p className="text-xs text-slate-400 mt-0.5">{selectedPlan.question}</p>
                </div>
                <button
                  onClick={() => handleExecute(selectedPlan.plan_id)}
                  disabled={executing}
                  className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold px-3 py-1.5 rounded transition disabled:opacity-50"
                >
                  <Play size={12} className={executing ? "animate-spin" : ""} />
                  {executing ? "Executing..." : "Run Plan"}
                </button>
              </div>

              {/* Steps Visual DAG */}
              <div className="space-y-2 pt-2 border-t border-slate-800">
                <span className="text-[11px] font-mono uppercase text-slate-500">
                  Execution Steps ({selectedPlan.steps.length})
                </span>
                <div className="space-y-2">
                  {selectedPlan.steps.map((step, idx) => (
                    <div
                      key={step.step_id}
                      className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-5 h-5 rounded-full bg-slate-800 text-slate-400 text-[10px] font-mono flex items-center justify-center">
                          {idx + 1}
                        </div>
                        <div>
                          <div className="text-xs font-semibold text-slate-200">{step.type}</div>
                          <div className="text-[10px] text-slate-500 font-mono">
                            ID: {step.step_id} {step.depends_on.length > 0 && `(Depends on: ${step.depends_on.join(", ")})`}
                          </div>
                        </div>
                      </div>

                      <div className="text-right">
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded font-mono uppercase ${
                            step.status === "COMPLETED"
                              ? "bg-emerald-950/60 text-emerald-400 border border-emerald-800/60"
                              : step.status === "RUNNING"
                              ? "bg-sky-950/60 text-sky-400 border border-sky-800/60"
                              : "bg-slate-800/60 text-slate-400"
                          }`}
                        >
                          {step.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* New Plan Dialog */}
      {newModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <form
            onSubmit={handleCreatePlan}
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 max-w-sm w-full space-y-4 shadow-2xl"
          >
            <h4 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
              <Plus size={15} className="text-sky-400" /> Create Investigation Plan
            </h4>

            <div className="space-y-1">
              <label className="text-xs text-slate-400">Plan Title</label>
              <input
                type="text"
                required
                placeholder="e.g. Glacier Retreat Verification"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-xs text-slate-100 outline-none focus:border-sky-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs text-slate-400">Core Analytical Question</label>
              <textarea
                rows={2}
                required
                placeholder="What specific physical phenomena are we verifying?"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-xs text-slate-100 outline-none focus:border-sky-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setNewModalOpen(false)}
                className="px-3 py-1.5 text-xs text-slate-400"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-3 py-1.5 text-xs bg-sky-600 hover:bg-sky-500 text-white font-medium rounded"
              >
                Create Plan
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
