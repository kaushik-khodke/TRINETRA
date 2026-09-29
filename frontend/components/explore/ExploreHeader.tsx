"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * ExploreHeader Component
 * Phase 1 Foundation
 */

import React from "react"
import Link from "next/link"
import { ArrowLeft, Globe, RotateCcw, Search, Sparkles } from "lucide-react"
import { globeCommandBus } from "@/lib/explore/globe-command-bus"
import { useGlobeState } from "@/lib/explore/globe-state"
import { QueryBar } from "./QueryBar"
import { AIStatus } from "./AIStatus"

export function ExploreHeader() {
  const { sidebarOpen, sidebarWidth } = useGlobeState()
  const handleReset = () => {
    globeCommandBus.dispatch({ type: "RESET_VIEW" })
  }

  return (
    <header
      className="explore-header"
      role="banner"
      style={{
        left: sidebarOpen ? `${sidebarWidth}px` : "0px",
        transition: "left 0.15s ease-out",
      }}
    >
      {/* Brand / Title (shown when sidebar is collapsed) */}
      {!sidebarOpen && (
        <div className="explore-brand-group">
          <Link
            href="/analysis"
            className="btn-tactical-icon"
            title="Return to Tactical Analysis Workspace"
            aria-label="Return to Tactical Analysis Workspace"
          >
            <ArrowLeft size={13} />
            <span>Workspace</span>
          </Link>

          <div className="explore-brand-title">
            <span>TRI•NETRA</span>
            <span className="explore-badge">SHANETRA EXPLORE</span>
          </div>
        </div>
      )}

      {/* Natural Language Query Bar & Command Activity */}
      <div className="explore-header-center">
        <QueryBar />
      </div>

      {/* Header Actions: AI Status, 2D/3D switcher & Reset */}
      <div className="explore-header-actions">
        <Link
          href="/workstation"
          className="btn-tactical-icon"
          title="Open Scientific Research Workstation"
          style={{ borderColor: "rgba(6, 182, 212, 0.4)", color: "#22d3ee" }}
        >
          <Sparkles size={13} />
          <span>Workstation</span>
        </Link>
        <AIStatus />
        <div
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#0a0e18]/80 border border-cyan-500/30 text-[11px] font-mono text-cyan-300 select-none shadow-sm"
          title="Cesium 3D Earth Globe Engine Active"
        >
          <Globe size={13} className="text-cyan-400" />
          <span>3D GLOBE</span>
        </div>

        <button
          type="button"
          className="btn-tactical-icon"
          onClick={handleReset}
          title="Reset Camera View to Default"
          aria-label="Reset Camera View"
        >
          <RotateCcw size={13} />
          <span>Reset</span>
        </button>
      </div>
    </header>
  )
}
