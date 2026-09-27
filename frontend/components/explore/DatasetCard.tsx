"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * DatasetCard Component
 * Phase 2: Renders individual satellite observation card with preview and layer addition.
 */

import React, { useState } from "react"
import { ExploreDataset } from "@/lib/explore/types"
import { LayerAdapter } from "@/lib/explore/layer-adapter"
import { globeCommandBus } from "@/lib/explore/globe-command-bus"
import { globeState } from "@/lib/explore/globe-state"
import { exploreApi } from "@/lib/explore/api"

interface DatasetCardProps {
  dataset: ExploreDataset
}

export default function DatasetCard({ dataset }: DatasetCardProps) {
  const [isAdding, setIsAdding] = useState(false)
  const isAdded = globeState.getState().selectedLayerIds.some((id) => id.includes(dataset.id))

  const handlePreview = () => {
    if (dataset.bbox && dataset.bbox.length === 4) {
      const [minLon, minLat, maxLon, maxLat] = dataset.bbox
      const centerLon = (minLon + maxLon) / 2
      const centerLat = (minLat + maxLat) / 2
      globeCommandBus.dispatch({
        type: "FLY_TO",
        latitude: centerLat,
        longitude: centerLon,
        zoom: 7.5,
        duration: 1.5,
      })
    }
  }

  const handleAddLayer = async () => {
    setIsAdding(true)
    try {
      const assetKey = Object.keys(dataset.assets)[0]
      const assetId = assetKey ? dataset.assets[assetKey].id : dataset.id

      // Register with backend to obtain authoritative tile URL template
      const reg = await exploreApi.registerDatasetLayer(assetId, dataset.title)
      const layerDef = reg || LayerAdapter.fromDataset(dataset)

      globeCommandBus.dispatch({
        type: "ADD_LAYER",
        layer: layerDef,
      })
    } finally {
      setIsAdding(false)
    }
  }

  return (
    <div className="dataset-card">
      <div className="dataset-card-header">
        <div className="dataset-title-row">
          <span className="dataset-title">{dataset.title || dataset.id}</span>
          <span className={`provider-badge ${dataset.provider}`}>{dataset.provider.toUpperCase()}</span>
        </div>
        <span className="dataset-date">
          {dataset.datetime ? new Date(dataset.datetime).toLocaleDateString() : "Live Archive"}
        </span>
      </div>

      <div className="dataset-meta-row">
        {dataset.cloudCover !== undefined && dataset.cloudCover !== null && (
          <span className="meta-badge">Cloud: {dataset.cloudCover.toFixed(1)}%</span>
        )}
        <span className="meta-badge">Bands: {Object.keys(dataset.assets).length || 4}</span>
      </div>

      <div className="dataset-card-actions">
        <button className="preview-btn" onClick={handlePreview} title="Center camera on observation">
          Fly To
        </button>
        <button
          className={`add-layer-btn ${isAdded ? "added" : ""}`}
          onClick={handleAddLayer}
          disabled={isAdding || isAdded}
        >
          {isAdding ? "Adding..." : isAdded ? "✓ On Map" : "+ Add Layer"}
        </button>
      </div>
    </div>
  )
}
