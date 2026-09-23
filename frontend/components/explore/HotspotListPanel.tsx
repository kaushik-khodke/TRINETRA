"use client"

/**
 * TRINETRA Phase 7 — Regional Hotspots & Density Panel
 * Visualizes spatial change clusters, activity severity, and multi-temporal regional trajectories.
 */

import React from "react"
import { HotspotCluster, RegionalSummary } from "@/lib/explore/intelligence-types"
import {
  Flame,
  RefreshCw,
  MapPin,
  TrendingUp,
  Activity,
  Compass,
} from "lucide-react"

interface Props {
  hotspots: HotspotCluster[]
  selectedHotspot: HotspotCluster | null
  isLoading: boolean
  regionalSummary: RegionalSummary | null
  isSummaryLoading: boolean
  onSelectHotspot: (hotspot: HotspotCluster) => void
  onRefresh: () => void
  onFocusOnMap: (bbox: number[]) => void
}

export const HotspotListPanel: React.FC<Props> = ({
  hotspots,
  selectedHotspot,
  isLoading,
  regionalSummary,
  isSummaryLoading,
  onSelectHotspot,
  onRefresh,
  onFocusOnMap,
}) => {
  return (
    <div className="flex flex-col gap-2.5 font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between pb-1 border-b border-slate-800">
        <div className="flex items-center gap-1.5 text-rose-400">
          <Flame className="w-3.5 h-3.5" />
          <span className="font-semibold text-slate-200">
            High-Density Clusters ({hotspots.length})
          </span>
        </div>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          title="Reload Hotspots"
          className="p-1 rounded text-slate-400 hover:text-rose-300 hover:bg-slate-800 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin text-rose-400" : ""}`} />
        </button>
      </div>

      {/* Regional Summary Card (if present) */}
      {regionalSummary && (
        <div className="p-2.5 bg-slate-950 border border-slate-800 rounded-lg space-y-2">
          <div className="flex justify-between items-center text-[11px] font-bold text-slate-200">
            <span>{regionalSummary.name || regionalSummary.region_id}</span>
            <span className="text-orange-400 font-mono">{regionalSummary.total_events} events</span>
          </div>
          <div className="grid grid-cols-2 gap-1 text-[10px] text-slate-400">
            <div>
              <span>Density: </span>
              <strong className="text-slate-200">
                {regionalSummary.density_events_per_sqkm?.toFixed(2) || "0.00"} /km²
              </strong>
            </div>
            <div>
              <span>Hotspots: </span>
              <strong className="text-rose-400">{regionalSummary.hotspot_count || 0}</strong>
            </div>
          </div>
        </div>
      )}

      {/* Hotspots List */}
      <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-rose-500/20">
        {hotspots.length === 0 && !isLoading && (
          <div className="text-center py-8 text-slate-500 text-xs">
            <Flame className="w-8 h-8 mx-auto mb-2 text-slate-600" />
            <p>No high-density change clusters detected.</p>
            <p className="text-[10px] mt-1 text-slate-600">
              Clusters form when $\ge 2$ events concentrate within 5 km.
            </p>
          </div>
        )}

        {hotspots.map((spot) => {
          const isSelected = selectedHotspot?.cluster_id === spot.cluster_id
          const severityPct = Math.min(100, (spot.severity_score || 0.5) * 100)

          return (
            <div
              key={spot.cluster_id}
              onClick={() => onSelectHotspot(spot)}
              className={`p-2.5 rounded-lg border transition-all cursor-pointer flex flex-col gap-2 ${
                isSelected
                  ? "bg-slate-900 border-rose-500/70 shadow-md shadow-rose-950/30"
                  : "bg-slate-950/60 border-slate-800/80 hover:bg-slate-900/80 hover:border-slate-700"
              }`}
            >
              {/* Cluster Title & Centroid */}
              <div className="flex items-start justify-between gap-1.5">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded bg-rose-950/70 border border-rose-700/60 text-rose-400">
                      {spot.event_count} Events
                    </span>
                    <span className="text-[10px] font-semibold text-slate-200">
                      {spot.dominant_class || "Multi-class"}
                    </span>
                  </div>
                  <div className="text-[9px] text-slate-400 flex items-center gap-1">
                    <MapPin className="w-2.5 h-2.5 text-slate-500" />
                    <span>
                      {spot.centroid_lat.toFixed(3)}°N, {spot.centroid_lon.toFixed(3)}°E
                    </span>
                  </div>
                </div>

                {spot.bounding_box && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onFocusOnMap(spot.bounding_box)
                    }}
                    title="Center on cluster"
                    className="p-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-700 text-rose-300 transition-colors"
                  >
                    <Compass className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>

              {/* Severity Bar */}
              <div className="space-y-1">
                <div className="flex justify-between text-[9px] text-slate-400">
                  <span>Cluster Severity</span>
                  <span className="font-bold text-rose-300">{severityPct.toFixed(0)}%</span>
                </div>
                <div className="w-full bg-slate-900 h-1.5 rounded overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-amber-500 to-rose-500 h-full rounded transition-all"
                    style={{ width: `${severityPct}%` }}
                  />
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
