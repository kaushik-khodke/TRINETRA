"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * DataSourcePanel Component
 * Phase 2: Data provider selector and manual region discovery trigger.
 */

import React, { useEffect, useState } from "react"
import { useGlobeState, globeState } from "@/lib/explore/globe-state"
import { exploreApi } from "@/lib/explore/api"

export default function DataSourcePanel() {
  const { catalogProvider, camera, catalogLoading } = useGlobeState()
  const [provider, setProvider] = useState<"all" | "local" | "copernicus">(catalogProvider)

  // Initial load of local samples on component mount
  useEffect(() => {
    handleSearch("local")
  }, [])

  const handleSearch = async (selectedProvider = provider) => {
    globeState.setCatalogLoading(true)
    globeState.setCatalogProvider(selectedProvider)

    try {
      // Calculate current approximate viewport bbox from camera center and zoom
      const delta = 360 / Math.pow(2, Math.max(1, camera.zoom))
      const bbox = [
        Math.max(-180, camera.longitude - delta),
        Math.max(-90, camera.latitude - delta),
        Math.min(180, camera.longitude + delta),
        Math.min(90, camera.latitude + delta),
      ]

      const items = await exploreApi.searchDatasets({
        bbox: selectedProvider === "local" ? undefined : bbox,
        provider: selectedProvider,
        limit: 15,
      })

      globeState.setCatalogItems(items)
    } finally {
      globeState.setCatalogLoading(false)
    }
  }

  return (
    <div className="datasource-panel">
      <div className="section-label">DATA SOURCE</div>
      <div className="provider-toggle-group">
        <button
          className={`provider-btn ${provider === "all" ? "active" : ""}`}
          onClick={() => {
            setProvider("all")
            handleSearch("all")
          }}
        >
          ALL
        </button>
        <button
          className={`provider-btn ${provider === "local" ? "active" : ""}`}
          onClick={() => {
            setProvider("local")
            handleSearch("local")
          }}
        >
          LOCAL
        </button>
        <button
          className={`provider-btn ${provider === "copernicus" ? "active" : ""}`}
          onClick={() => {
            setProvider("copernicus")
            handleSearch("copernicus")
          }}
        >
          COPERNICUS
        </button>
      </div>

      <button
        className="search-region-btn"
        onClick={() => handleSearch(provider)}
        disabled={catalogLoading}
      >
        {catalogLoading ? "Searching Catalogs..." : "🔍 Search Viewport Region"}
      </button>
    </div>
  )
}
