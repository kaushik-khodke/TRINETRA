"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * ExploreHeader Component
 * Phase 1 Foundation
 */

import React from "react"
import Link from "next/link"
import { ArrowLeft, RotateCcw, Search, Sparkles } from "lucide-react"
import { globeCommandBus } from "@/lib/explore/globe-command-bus"
import { ViewModeSwitcher } from "./ViewModeSwitcher"
import { QueryBar } from "./QueryBar"
import { AIStatus } from "./AIStatus"

export function ExploreHeader() {
  const handleReset = () => {
    globeCommandBus.dispatch({ type: "RESET_VIEW" })
  }

  return (
    <header className="explore-header" role="banner">
      {/* Brand / Title */}
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

      {/* Natural Language Query Bar & Command Activity */}
      <div className="explore-header-center">
        <QueryBar />
      </div>

      {/* Header Actions: AI Status, 2D/3D switcher & Reset */}
      <div className="explore-header-actions">
        <AIStatus />
        <ViewModeSwitcher />

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
