"use client"

import React, { useState } from "react"
import {
  Clock,
  Play,
  XCircle,
  CheckCircle2,
  AlertCircle,
  Plus,
  Cpu,
} from "lucide-react"
import { WorkspaceTask, TaskPriority } from "@/lib/explore/workspace-types"

interface TaskQueuePanelProps {
  tasks: WorkspaceTask[]
  onSubmitTask: (type: string, priority: TaskPriority, params: any) => Promise<any>
  onCancelTask: (taskId: string) => Promise<any>
}

export function TaskQueuePanel({
  tasks,
  onSubmitTask,
  onCancelTask,
}: TaskQueuePanelProps) {
  const [modalOpen, setModalOpen] = useState(false)
  const [taskType, setTaskType] = useState("ANALYSIS")
  const [priority, setPriority] = useState<TaskPriority>("NORMAL")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await onSubmitTask(taskType, priority, {})
    setModalOpen(false)
  }

  const getPriorityBadge = (pri: TaskPriority) => {
    switch (pri) {
      case "INTERACTIVE":
        return "bg-red-950/60 text-red-400 border-red-800/60"
      case "NORMAL":
        return "bg-sky-950/60 text-sky-400 border-sky-800/60"
      default:
        return "bg-slate-800 text-slate-400 border-slate-700"
    }
  }

  return (
    <div className="p-4 space-y-4 text-slate-200">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
            <Cpu size={15} className="text-sky-400" /> Analytical Task Queue
          </h3>
          <p className="text-[11px] text-slate-400">Priority scheduling (Interactive &gt; Normal &gt; Background)</p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="flex items-center gap-1 text-xs bg-sky-600 hover:bg-sky-500 text-white px-2.5 py-1 rounded transition"
        >
          <Plus size={13} /> Enqueue Task
        </button>
      </div>

      <div className="space-y-2">
        {tasks.length === 0 ? (
          <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-6 text-center text-xs text-slate-500">
            No background analytical tasks in the queue.
          </div>
        ) : (
          tasks.map((t) => (
            <div
              key={t.task_id}
              className="bg-slate-900/80 border border-slate-800 rounded-xl p-3 space-y-2"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded font-mono border uppercase ${getPriorityBadge(t.priority)}`}>
                    {t.priority}
                  </span>
                  <span className="text-xs font-semibold text-slate-200">{t.type}</span>
                  <span className="text-[10px] text-slate-500 font-mono">({t.task_id.slice(0, 10)})</span>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded font-mono uppercase ${
                      t.status === "COMPLETED"
                        ? "text-emerald-400 bg-emerald-950/60 border border-emerald-800/60"
                        : t.status === "RUNNING"
                        ? "text-sky-400 bg-sky-950/60 border border-sky-800/60"
                        : t.status === "CANCELLED"
                        ? "text-slate-500 bg-slate-800"
                        : "text-amber-400 bg-amber-950/60 border border-amber-800/60"
                    }`}
                  >
                    {t.status}
                  </span>
                  {t.status === "RUNNING" || t.status === "QUEUED" ? (
                    <button
                      onClick={() => onCancelTask(t.task_id)}
                      title="Cancel Task"
                      className="text-slate-500 hover:text-red-400 transition p-1"
                    >
                      <XCircle size={14} />
                    </button>
                  ) : null}
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-1">
                <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                  <span>Stage: {t.progress?.stage || "QUEUED"}</span>
                  <span>{t.progress?.percentage || 0}%</span>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-300 ${
                      t.status === "COMPLETED" ? "bg-emerald-500" : "bg-sky-500"
                    }`}
                    style={{ width: `${t.progress?.percentage || 0}%` }}
                  />
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Enqueue Task Modal */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <form
            onSubmit={handleSubmit}
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 max-w-sm w-full space-y-4 shadow-2xl"
          >
            <h4 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
              <Plus size={15} className="text-sky-400" /> Enqueue Background Task
            </h4>

            <div className="space-y-1">
              <label className="text-xs text-slate-400">Task Type</label>
              <select
                value={taskType}
                onChange={(e) => setTaskType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
              >
                <option value="ANALYSIS">Bitemporal Change Analysis</option>
                <option value="BATCH">Batch Multi-Target Execution</option>
                <option value="SEARCH">Semantic Intelligence Search</option>
                <option value="REPORT">Dossier Assembly &amp; Packaging</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs text-slate-400">Scheduling Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as TaskPriority)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
              >
                <option value="INTERACTIVE">Interactive (Urgent Pre-emption)</option>
                <option value="NORMAL">Normal (Standard Processing)</option>
                <option value="BACKGROUND">Background (Batch / Resource Friendly)</option>
              </select>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="px-3 py-1.5 text-xs text-slate-400"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-3 py-1.5 text-xs bg-sky-600 hover:bg-sky-500 text-white font-medium rounded"
              >
                Enqueue
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
