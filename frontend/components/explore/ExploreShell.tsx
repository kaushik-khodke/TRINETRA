"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * ExploreShell Component — Main Workstation Layout Coordinator
 * Phase 1 Foundation
 */

import React from "react"
import "@/app/explore/explore.css"
import { ExploreHeader } from "./ExploreHeader"
import { ExploreSidebar } from "./ExploreSidebar"
import { ExploreViewport } from "./ExploreViewport"
import { ExploreStatusBar } from "./ExploreStatusBar"

export function ExploreShell() {
  return (
    <div className="explore-root" id="shanetra-explore-root">
      {/* 1. Header with search & view switchers */}
      <ExploreHeader />

      {/* 2. Workstation body containing sidebar & viewport */}
      <div className="explore-body">
        <ExploreSidebar />
        <ExploreViewport />
      </div>

      {/* 3. Operational bottom telemetry status bar */}
      <ExploreStatusBar />
    </div>
  )
}
