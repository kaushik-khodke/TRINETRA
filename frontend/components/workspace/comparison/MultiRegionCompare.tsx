"use client"

import React, { useState } from "react"
import {
  GitCompare,
  AlertTriangle,
  Activity,
  ArrowRight,
  TrendingUp,
  Sparkles,
  BarChart3,
} from "lucide-react"
import { RegionComparison } from "@/lib/explore/workspace-types"

interface MultiRegionCompareProps {
  comparisons: RegionComparison[]
  activeComparison: RegionComparison | null
  onCompareRegions: (regA: string, regB: string, period?: string) => Promise<any>
}

export function MultiRegionCompare({
  comparisons,
  activeComparison,
  onCompareRegions,
}: MultiRegionCompareProps) {
  const [regionA, setRegionA] = useState("reg-sikkim")
  const [regionB, setRegionB] = useState("reg-ladakh")
  const [period, setPeriod] = useState("last_12_months")
  const [loading, setLoading] = useState(false)
  const [selectedComp, setSelectedComp] = useState<RegionComparison | null>(
    activeComparison || comparisons[0] || null
  )

  const handleCompare = async () => {
    setLoading(true)
    try {
      const res = await onCompareRegions(regionA, regionB, period)
      setSelectedComp(res)
    } finally {
      setLoading(false)
    }
  }

  const renderSparkline = (curve: any[]) => {
    if (!curve || curve.length === 0) return null
    const maxVal = Math.max(...curve.map((p) => p.detected_area_km2), 1.0)
    const points = curve.map((p, i) => {
      const x = (i / (curve.length - 1)) * 120
      const y = 40 - (p.detected_area_km2 / maxVal) * 35
      return `${x},${y}`
    }).join(" ")

    return (
      <svg className="w-28 h-10 overflow-visible">
        <polyline fill="none" stroke="#38bdf8" strokeWidth="2" points={points} />
      </svg>
    )
  }

  return (
    <div className="p-4 space-y-4 text-slate-200">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
            <GitCompare size={15} className="text-sky-400" /> Multi-Region Normalized Comparison
          </h3>
          <p className="text-[11px] text-slate-400">Area-normalized metrics, coverage warnings & stability analysis</p>
        </div>
      </div>

      {/* Comparison Input Bar */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5 space-y-3">
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <label className="text-[10px] text-slate-400 uppercase font-mono block mb-1">Region A</label>
            <input
              type="text"
              value={regionA}
              onChange={(e) => setRegionA(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
            />
          </div>
          <div>
            <label className="text-[10px] text-slate-400 uppercase font-mono block mb-1">Region B</label>
            <input
              type="text"
              value={regionB}
              onChange={(e) => setRegionB(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
            />
          </div>
        </div>

        <div className="flex items-center justify-between pt-1">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded px-2.5 py-1.5 outline-none"
          >
            <option value="last_3_months">Last 3 Months</option>
            <option value="last_6_months">Last 6 Months</option>
            <option value="last_12_months">Last 12 Months</option>
            <option value="last_5_years">Last 5 Years</option>
          </select>

          <button
            onClick={handleCompare}
            disabled={loading}
            className="bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold px-4 py-1.5 rounded transition disabled:opacity-50 flex items-center gap-1.5"
          >
            <GitCompare size={13} className={loading ? "animate-spin" : ""} />
            {loading ? "Comparing..." : "Execute Comparison"}
          </button>
        </div>
      </div>

      {/* Comparison Results Card */}
      {selectedComp && (
        <div className="space-y-4">
          {/* Warnings Callout */}
          {selectedComp.warnings && selectedComp.warnings.length > 0 && (
            <div className="bg-amber-950/40 border border-amber-800/60 rounded-xl p-3 space-y-1.5">
              <div className="flex items-center gap-1.5 text-amber-400 text-xs font-semibold uppercase font-mono">
                <AlertTriangle size={13} /> Coverage Disparity Warnings ({selectedComp.warnings.length})
              </div>
              <ul className="text-xs text-amber-200/80 space-y-1 list-disc list-inside">
                {selectedComp.warnings.map((w, idx) => (
                  <li key={idx} className="leading-snug">{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Area Normalized Metrics Matrix */}
          <div className="grid grid-cols-2 gap-3">
            {/* Region A */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 space-y-2">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-xs font-bold text-sky-400">{selectedComp.metrics.region_a.name}</span>
                <span className="text-[10px] font-mono text-slate-500">{selectedComp.metrics.region_a.area_km2} km²</span>
              </div>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">Events / 100km²:</span>
                  <span className="font-mono text-slate-200">{selectedComp.metrics.region_a.events_per_100km2}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Findings / 100km²:</span>
                  <span className="font-mono text-slate-200">{selectedComp.metrics.region_a.findings_per_100km2}</span>
                </div>
              </div>
              <div className="pt-2 border-t border-slate-800/60">
                <span className="text-[10px] text-slate-500 uppercase font-mono block mb-1">Sensitivity Curve</span>
                {renderSparkline(selectedComp.metrics.region_a.sensitivity_curve)}
              </div>
            </div>

            {/* Region B */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 space-y-2">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-xs font-bold text-emerald-400">{selectedComp.metrics.region_b.name}</span>
                <span className="text-[10px] font-mono text-slate-500">{selectedComp.metrics.region_b.area_km2} km²</span>
              </div>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">Events / 100km²:</span>
                  <span className="font-mono text-slate-200">{selectedComp.metrics.region_b.events_per_100km2}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Findings / 100km²:</span>
                  <span className="font-mono text-slate-200">{selectedComp.metrics.region_b.findings_per_100km2}</span>
                </div>
              </div>
              <div className="pt-2 border-t border-slate-800/60">
                <span className="text-[10px] text-slate-500 uppercase font-mono block mb-1">Sensitivity Curve</span>
                {renderSparkline(selectedComp.metrics.region_b.sensitivity_curve)}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
