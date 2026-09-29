"use client"

/**
 * TRINETRA Workstation — Minimalist Glassmorphic Header Bar
 * Mission switcher, Active AOI telemetry, 2D/3D mode, and Export package CTA.
 */

import React, { useState } from "react"
import Link from "next/link"
import { Mission, AreaOfInterest } from "@/lib/workstation/types"
import {
  Layers,
  Sparkles,
  Download,
  Plus,
  Compass,
  Globe2,
  ShieldCheck,
  Cpu,
  ChevronDown,
  ArrowLeft,
  X,
} from "lucide-react"

interface Props {
  missions: Mission[]
  activeMission: Mission | null
  onSelectMission: (mission: Mission) => void
  onCreateMission: (name: string, description: string) => Promise<void>
  activeAOI: AreaOfInterest | null
  onClearAOI?: () => void
  viewMode?: "2d" | "3d"
  onToggleViewMode?: (mode: "2d" | "3d") => void
  onExportClick: () => void
}

export const WorkstationHeader: React.FC<Props> = ({
  missions,
  activeMission,
  onSelectMission,
  onCreateMission,
  activeAOI,
  onClearAOI,
  viewMode,
  onToggleViewMode,
  onExportClick,
}) => {
  const [showMissionModal, setShowMissionModal] = useState(false)
  const [newMissionName, setNewMissionName] = useState("")
  const [newMissionDesc, setNewMissionDesc] = useState("")
  const [showDropdown, setShowDropdown] = useState(false)
  const [isCreating, setIsCreating] = useState(false)

  const navLinks = [
    { href: "/workstation", label: "Workstation", active: true },
    { href: "/explore", label: "Explore", active: false },
    { href: "/analysis", label: "Workspace", active: false },
    { href: "/dashboard", label: "History", active: false },
    { href: "/evaluation", label: "Evaluation", active: false },
  ]

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMissionName.trim()) return
    setIsCreating(true)
    try {
      await onCreateMission(newMissionName, newMissionDesc)
      setNewMissionName("")
      setNewMissionDesc("")
      setShowMissionModal(false)
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <>
      <header className="h-14 border-b border-white/[0.08] bg-slate-950/80 backdrop-blur-2xl px-4 flex items-center justify-between select-none z-30 relative shadow-sm gap-2">
        {/* Left: Back Button, Brand & Main Navigation */}
        <div className="flex items-center gap-3">
          {/* Quick Exit / Back Button */}
          <Link
            href="/analysis"
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.08] hover:border-white/[0.15] text-xs text-slate-300 hover:text-white transition-all cursor-pointer group"
            title="Return to Tactical Workspace"
          >
            <ArrowLeft className="w-3.5 h-3.5 text-slate-400 group-hover:text-cyan-400 transition-colors" />
            <span className="text-[11px] font-medium hidden sm:inline">Back</span>
          </Link>

          {/* Clickable Brand Logo */}
          <Link href="/" className="flex items-center gap-2 group cursor-pointer" title="Return to Home Portal">
            <img
              src="/trinetra-logo1.webp"
              alt="TRINETRA Logo"
              className="w-6 h-6 rounded object-contain group-hover:opacity-90 transition-opacity"
            />
            <div className="flex flex-col">
              <span className="font-bold tracking-wider text-xs bg-gradient-to-r from-slate-100 via-slate-200 to-slate-400 bg-clip-text text-transparent group-hover:to-cyan-300 transition-colors">
                TRI·NETRA
              </span>
              <span className="text-[8px] font-mono text-slate-500 uppercase leading-none hidden md:inline">
                RESEARCH / 001
              </span>
            </div>
          </Link>

          <div className="h-4 w-px bg-white/10 hidden sm:block" />

          {/* Main Global Navigation Links */}
          <nav className="flex items-center gap-1 bg-white/[0.02] border border-white/[0.06] p-0.5 rounded-lg">
            {navLinks.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`px-2.5 py-1 text-xs rounded-md transition-all font-medium ${
                  item.active
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="h-4 w-px bg-white/10 hidden md:block" />

          {/* Mission Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="flex items-center gap-2 bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] hover:border-white/[0.15] rounded-lg px-2.5 py-1 text-xs text-slate-200 transition-all cursor-pointer backdrop-blur-md"
            >
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <div className="flex flex-col text-left">
                <span className="text-[8px] text-slate-400 uppercase font-mono leading-none">
                  Mission
                </span>
                <span className="font-medium text-slate-100 truncate max-w-[130px] sm:max-w-[160px] text-xs leading-tight">
                  {activeMission?.name || "Initialize Mission"}
                </span>
              </div>
              <ChevronDown className="w-3 h-3 text-slate-400 ml-0.5" />
            </button>

            {showDropdown && (
              <div className="absolute top-full left-0 mt-1.5 w-72 bg-slate-950/95 border border-white/10 rounded-xl shadow-2xl p-2 z-50 backdrop-blur-3xl">
                <div className="text-[10px] font-mono uppercase text-slate-400 px-2 py-1 flex items-center justify-between border-b border-white/[0.08]">
                  <span>Missions</span>
                  <span>{missions.length}</span>
                </div>
                <div className="max-h-56 overflow-y-auto py-1 space-y-1">
                  {missions.length > 0 ? (
                    missions.map((m) => (
                      <button
                        key={m.id}
                        onClick={() => {
                          onSelectMission(m)
                          setShowDropdown(false)
                        }}
                        className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs transition-colors flex flex-col ${
                          activeMission?.id === m.id
                            ? "bg-cyan-950/60 border border-cyan-800/80 text-cyan-200"
                            : "hover:bg-white/5 text-slate-300"
                        }`}
                      >
                        <span className="font-medium truncate">{m.name}</span>
                        <span className="text-[10px] text-slate-400 truncate">{m.description || "No description"}</span>
                      </button>
                    ))
                  ) : (
                    <div className="py-4 text-center text-slate-400 text-xs font-mono">
                      No missions registered.
                    </div>
                  )}
                </div>
                <div className="border-t border-white/[0.08] pt-1.5 mt-1">
                  <button
                    onClick={() => {
                      setShowDropdown(false)
                      setShowMissionModal(true)
                    }}
                    className="w-full flex items-center justify-center gap-1.5 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Create New Mission</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Center: Active AOI & Telemetry */}
        <div className="hidden xl:flex items-center gap-2.5">
          {activeAOI ? (
            <div className="flex items-center gap-2 bg-white/[0.03] border border-cyan-500/30 rounded-full pl-3 pr-2 py-1 backdrop-blur-md">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
              <span className="text-[10px] font-mono text-cyan-400 uppercase font-semibold">AOI:</span>
              <span className="text-xs font-medium text-slate-200">{activeAOI.name}</span>
              {onClearAOI && (
                <button
                  onClick={onClearAOI}
                  className="p-0.5 rounded-full hover:bg-white/10 text-slate-400 hover:text-rose-300 transition-colors cursor-pointer ml-0.5"
                  title="Deselect Active AOI (Show Global Extent)"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          ) : (
            <div className="text-[10px] font-mono text-slate-400 bg-white/[0.02] border border-white/[0.06] rounded-full px-3 py-1">
              Global Extent (No AOI Selected)
            </div>
          )}

          <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-400 bg-white/[0.02] border border-white/[0.06] rounded-full px-2.5 py-1">
            <Cpu className="w-3 h-3 text-emerald-400" />
            <span>COPILOT READY</span>
          </div>

          <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-400 bg-white/[0.02] border border-white/[0.06] rounded-full px-2.5 py-1">
            <ShieldCheck className="w-3 h-3 text-cyan-400" />
            <span>APPROVAL GATE</span>
          </div>
        </div>

        {/* Right: View Mode Toggle & Export CTA */}
        <div className="flex items-center gap-2">
          {/* 3D Cesium Globe Indicator */}
          <div
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-cyan-950/40 border border-cyan-500/30 text-xs font-mono text-cyan-300 shadow-sm select-none"
            title="Cesium 3D Earth Globe Engine Active"
          >
            <Globe2 className="w-3.5 h-3.5 text-cyan-400" />
            <span>3D GLOBE</span>
          </div>

          {/* Export Manifest */}
          <button
            onClick={onExportClick}
            className="flex items-center gap-1.5 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 px-3 py-1.5 rounded-lg text-xs font-medium shadow-sm transition-all cursor-pointer backdrop-blur-md"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Export Manifest</span>
          </button>
        </div>
      </header>

      {/* New Mission Modal */}
      {showMissionModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-2xl flex items-center justify-center p-4">
          <div className="bg-slate-950/90 border border-white/10 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4 backdrop-blur-3xl">
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
              <h2 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                Initialize Research Mission
              </h2>
              <button
                onClick={() => setShowMissionModal(false)}
                className="text-slate-400 hover:text-slate-200 text-sm font-medium w-7 h-7 rounded-lg hover:bg-white/5 flex items-center justify-center transition-colors"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">
                  Mission Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Mahanadi Catchment Forest Study"
                  value={newMissionName}
                  onChange={(e) => setNewMissionName(e.target.value)}
                  className="w-full bg-black/40 border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-cyan-500/60 transition-colors"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">
                  Scientific Objectives & Scope
                </label>
                <textarea
                  rows={3}
                  placeholder="Describe sensor hypotheses, target dates, and investigation criteria..."
                  value={newMissionDesc}
                  onChange={(e) => setNewMissionDesc(e.target.value)}
                  className="w-full bg-black/40 border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-cyan-500/60 transition-colors"
                />
              </div>
              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowMissionModal(false)}
                  className="px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreating}
                  className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold px-4 py-1.5 rounded-lg text-xs shadow-lg shadow-cyan-950/40 transition-all cursor-pointer"
                >
                  {isCreating ? "Initializing..." : "Create Mission"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}
