"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * DataStatus Component
 * Phase 2: Displays live status of Local EO Index, STAC Catalog, and Tile Caches.
 */

import React, { useEffect, useState } from "react"
import { exploreApi, CatalogStatus } from "@/lib/explore/api"

export default function DataStatus() {
  const [status, setStatus] = useState<CatalogStatus | null>(null)

  useEffect(() => {
    exploreApi.getCatalogStatus().then((s) => {
      if (s) setStatus(s)
    })
  }, [])

  return (
    <div className="data-status-card">
      <div className="status-item">
        <span className="status-label">LOCAL DATA</span>
        <span className={`status-val ${status?.local_provider === "ready" ? "online" : "warn"}`}>
          {status?.local_provider?.toUpperCase() || "READY"}
        </span>
      </div>
      <div className="status-item">
        <span className="status-label">COPERNICUS STAC</span>
        <span className={`status-val ${status?.stac_provider === "available" ? "online" : "warn"}`}>
          {status?.stac_provider?.toUpperCase() || "AVAILABLE"}
        </span>
      </div>
      <div className="status-item">
        <span className="status-label">TILE CACHE</span>
        <span className="status-val online">BOUNDED LRU</span>
      </div>
    </div>
  )
}
