"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * CatalogResults Component
 * Phase 2: Lists discovered Earth Observation satellite products.
 */

import React from "react"
import { useGlobeState } from "@/lib/explore/globe-state"
import DatasetCard from "./DatasetCard"

export default function CatalogResults() {
  const { catalogItems, catalogLoading } = useGlobeState()

  if (catalogLoading) {
    return (
      <div className="catalog-loading">
        <div className="spinner" />
        <span>Searching Earth-Observation Catalogs...</span>
      </div>
    )
  }

  if (catalogItems.length === 0) {
    return (
      <div className="catalog-empty">
        <span>No satellite observations loaded yet. Click Search to query observations for current region.</span>
      </div>
    )
  }

  return (
    <div className="catalog-results-list">
      <div className="catalog-count-header">
        <span>{catalogItems.length} OBSERVATIONS DISCOVERED</span>
      </div>
      {catalogItems.map((item) => (
        <DatasetCard key={item.id} dataset={item} />
      ))}
    </div>
  )
}
