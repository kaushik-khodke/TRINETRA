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
  const [provider, setProvider] = useState<"all" | "copernicus">(
    catalogProvider === "local" ? "copernicus" : (catalogProvider as "all" | "copernicus")
  )

  // Initial load of satellite discovery on component mount
  useEffect(() => {
    handleSearch("copernicus")
  }, [])

  const handleSearch = async (selectedProvider: "all" | "copernicus" = provider) => {
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
        bbox,
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
      <div className="section-label">EO SATELLITE CATALOG</div>
      <div className="provider-toggle-group">
        <button
          className={`provider-btn ${provider === "copernicus" ? "active" : ""}`}
          onClick={() => {
            setProvider("copernicus")
            handleSearch("copernicus")
          }}
        >
          COPERNICUS STAC
        </button>
        <button
          className={`provider-btn ${provider === "all" ? "active" : ""}`}
          onClick={() => {
            setProvider("all")
            handleSearch("all")
          }}
        >
          GLOBAL SENSORS
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
