"use client"

import React, { useState } from "react"
import {
  Briefcase,
  Plus,
  Camera,
  ChevronDown,
  CheckCircle2,
  Clock,
  PauseCircle,
  Archive,
  FolderOpen,
} from "lucide-react"
import { Workspace, WorkspaceStatus } from "@/lib/explore/workspace-types"

interface WorkspaceHeaderProps {
  workspaces: Workspace[]
  activeWorkspace: Workspace | null
  onSelectWorkspace: (ws: Workspace) => void
  onCreateWorkspace: (name: string, description?: string) => Promise<any>
  onUpdateStatus: (status: WorkspaceStatus) => Promise<any>
  onSnapshot: () => Promise<any>
}

export function WorkspaceHeader({
  workspaces,
  activeWorkspace,
  onSelectWorkspace,
  onCreateWorkspace,
  onUpdateStatus,
  onSnapshot,
}: WorkspaceHeaderProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [newName, setNewName] = useState("")
  const [newDesc, setNewDesc] = useState("")
  const [snapshotLoading, setSnapshotLoading] = useState(false)

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newName.trim()) return
    await onCreateWorkspace(newName.trim(), newDesc.trim())
    setNewName("")
    setNewDesc("")
    setCreateModalOpen(false)
  }

  const handleTakeSnapshot = async () => {
    setSnapshotLoading(true)
    try {
      await onSnapshot()
    } finally {
      setSnapshotLoading(false)
    }
  }

  const getStatusBadge = (status: WorkspaceStatus) => {
    switch (status) {
      case "ACTIVE":
        return <span className="flex items-center gap-1 text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-2 py-0.5 rounded text-xs"><CheckCircle2 size={11} /> ACTIVE</span>
      case "PAUSED":
        return <span className="flex items-center gap-1 text-amber-400 bg-amber-950/60 border border-amber-800/60 px-2 py-0.5 rounded text-xs"><PauseCircle size={11} /> PAUSED</span>
      case "COMPLETED":
        return <span className="flex items-center gap-1 text-sky-400 bg-sky-950/60 border border-sky-800/60 px-2 py-0.5 rounded text-xs"><CheckCircle2 size={11} /> COMPLETED</span>
      case "ARCHIVED":
        return <span className="flex items-center gap-1 text-slate-400 bg-slate-800/60 border border-slate-700/60 px-2 py-0.5 rounded text-xs"><Archive size={11} /> ARCHIVED</span>
      default:
        return <span className="flex items-center gap-1 text-blue-400 bg-blue-950/60 border border-blue-800/60 px-2 py-0.5 rounded text-xs"><Clock size={11} /> CREATED</span>
    }
  }

  return (
    <div className="border-b border-slate-800 bg-slate-900/90 backdrop-blur p-3.5 space-y-2">
      <div className="flex items-center justify-between">
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 text-sm font-semibold text-slate-100 hover:text-sky-400 transition"
          >
            <Briefcase size={16} className="text-sky-400" />
            <span className="truncate max-w-[220px]">
              {activeWorkspace ? activeWorkspace.name : "Select Workspace"}
            </span>
            <ChevronDown size={14} className="text-slate-400" />
          </button>

          {dropdownOpen && (
            <div className="absolute left-0 mt-2 w-64 bg-slate-900 border border-slate-800 rounded-lg shadow-2xl z-50 py-1">
              <div className="px-3 py-1.5 text-[10px] uppercase font-mono tracking-wider text-slate-400 border-b border-slate-800">
                Workspaces ({workspaces.length})
              </div>
              <div className="max-h-48 overflow-y-auto">
                {workspaces.map((ws) => (
                  <button
                    key={ws.workspace_id}
                    onClick={() => {
                      onSelectWorkspace(ws)
                      setDropdownOpen(false)
                    }}
                    className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-800 transition ${
                      activeWorkspace?.workspace_id === ws.workspace_id ? "text-sky-400 font-medium bg-slate-800/50" : "text-slate-300"
                    }`}
                  >
                    <span className="truncate pr-2">{ws.name}</span>
                    <span className="text-[10px] text-slate-500 font-mono">{ws.status}</span>
                  </button>
                ))}
              </div>
              <div className="border-t border-slate-800 p-1.5">
                <button
                  onClick={() => {
                    setDropdownOpen(false)
                    setCreateModalOpen(true)
                  }}
                  className="w-full flex items-center justify-center gap-1.5 text-xs text-sky-400 hover:bg-sky-950/40 py-1 rounded transition"
                >
                  <Plus size={13} /> New Workspace
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {activeWorkspace && getStatusBadge(activeWorkspace.status)}
          <button
            onClick={handleTakeSnapshot}
            disabled={snapshotLoading || !activeWorkspace}
            title="Save Workspace State Snapshot"
            className="p-1.5 text-slate-400 hover:text-sky-400 hover:bg-slate-800 rounded transition disabled:opacity-50"
          >
            <Camera size={14} className={snapshotLoading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {activeWorkspace?.description && (
        <p className="text-xs text-slate-400 line-clamp-1">{activeWorkspace.description}</p>
      )}

      {/* New Workspace Dialog */}
      {createModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <form
            onSubmit={handleCreateSubmit}
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 max-w-sm w-full space-y-4 shadow-2xl"
          >
            <div className="flex items-center gap-2 text-sky-400 font-medium">
              <FolderOpen size={18} />
              <span>Create Analytical Workspace</span>
            </div>

            <div className="space-y-1">
              <label className="text-xs text-slate-400">Workspace Title</label>
              <input
                type="text"
                required
                placeholder="e.g. Sikkim Lake 2026 Monitoring"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-xs text-slate-100 focus:border-sky-500 outline-none"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs text-slate-400">Analytical Objective / Description</label>
              <textarea
                rows={2}
                placeholder="Brief description of investigation question..."
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-xs text-slate-100 focus:border-sky-500 outline-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setCreateModalOpen(false)}
                className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-3 py-1.5 text-xs bg-sky-600 hover:bg-sky-500 text-white rounded font-medium transition"
              >
                Create Workspace
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
