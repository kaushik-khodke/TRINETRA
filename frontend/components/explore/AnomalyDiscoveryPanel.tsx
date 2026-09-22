"use client"

/**
 * TRINETRA Phase 7 — Anomaly Discovery Panel
 * Displays statistical anomalies, Z-score deviations, baseline distributions,
 * and non-causal contextual explanations.
 */

import React from "react"
import { AnomalyRecord } from "@/lib/explore/intelligence-types"
import {
  AlertTriangle,
  RefreshCw,
  MapPin,
  TrendingUp,
  ShieldAlert,
  Info,
} from "lucide-react"

interface Props {
  anomalies: AnomalyRecord[]
  selectedAnomaly: AnomalyRecord | null
  isLoading: boolean
  onSelectAnomaly: (anomaly: AnomalyRecord) => void
  onRefresh: () => void
  onFocusOnMap?: (bbox: number[]) => void
}

export const AnomalyDiscoveryPanel: React.FC<Props> = ({
  anomalies,
  selectedAnomaly,
  isLoading,
  onSelectAnomaly,
  onRefresh,
  onFocusOnMap,
}) => {
  return (
    <div className="flex flex-col gap-2.5 font-mono text-xs">
      {/* Header bar */}
      <div className="flex items-center justify-between pb-1 border-b border-slate-800">
        <div className="flex items-center gap-1.5 text-amber-400">
          <AlertTriangle className="w-3.5 h-3.5" />
          <span className="font-semibold text-slate-200">
            Statistical Anomalies ({anomalies.length})
          </span>
        </div>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          title="Reload Anomalies"
          className="p-1 rounded text-slate-400 hover:text-amber-300 hover:bg-slate-800 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin text-amber-400" : ""}`} />
        </button>
      </div>

      {/* Anomalies List */}
      <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-amber-500/20">
        {anomalies.length === 0 && !isLoading && (
          <div className="text-center py-8 text-slate-500 text-xs">
            <ShieldAlert className="w-8 h-8 mx-auto mb-2 text-slate-600" />
            <p>No statistical anomalies currently flagged.</p>
            <p className="text-[10px] mt-1 text-slate-600">
              Anomalies trigger when metrics deviate beyond $\pm 2.0\sigma$ from local baseline.
            </p>
          </div>
        )}

        {anomalies.map((anom) => {
          const isSelected = selectedAnomaly?.anomaly_id === anom.anomaly_id
          const zScore = anom.anomaly_score

          return (
            <div
              key={anom.anomaly_id}
              onClick={() => onSelectAnomaly(anom)}
              className={`p-2.5 rounded-lg border transition-all cursor-pointer flex flex-col gap-2 ${
                isSelected
                  ? "bg-slate-900 border-amber-500/70 shadow-md shadow-amber-950/30"
                  : "bg-slate-950/60 border-slate-800/80 hover:bg-slate-900/80 hover:border-slate-700"
              }`}
            >
              {/* Top Row: Metric & Score Badge */}
              <div className="flex items-start justify-between gap-1.5">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded bg-amber-950/70 border border-amber-700/60 text-amber-400">
                      Z: {zScore > 0 ? `+${zScore.toFixed(2)}σ` : `${zScore.toFixed(2)}σ`}
                    </span>
                    <span className="text-[10px] font-semibold text-slate-200">
                      {anom.metric_name.replace("_", " ")}
                    </span>
                  </div>
                  <div className="text-[9px] text-slate-400 font-mono">
                    Baseline: {anom.baseline_id}
                  </div>
                </div>

                <span
                  className={`text-[9px] px-1.5 py-0.5 rounded border uppercase font-semibold ${
                    anom.status === "NEW"
                      ? "bg-rose-950/60 border-rose-800 text-rose-400"
                      : "bg-slate-800 border-slate-700 text-slate-400"
                  }`}
                >
                  {anom.status}
                </span>
              </div>

              {/* Observed vs Baseline Stats */}
              <div className="grid grid-cols-2 gap-1.5 bg-slate-950/80 p-1.5 rounded border border-slate-800 text-[10px]">
                <div>
                  <span className="text-slate-500 block">Observed:</span>
                  <span className="font-bold text-amber-300">{anom.observed_value.toFixed(3)}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Baseline Mean:</span>
                  <span className="font-bold text-slate-300">{anom.baseline_mean.toFixed(3)}</span>
                </div>
              </div>

              {/* Non-Causal Explanation */}
              <div className="p-1.5 rounded bg-slate-900/60 border border-slate-800/60 text-[10px] text-slate-300 flex items-start gap-1.5">
                <Info className="w-3 h-3 text-amber-400 shrink-0 mt-0.5" />
                <p className="line-clamp-2 italic">{anom.explanation}</p>
              </div>

              {/* Confidence & Timestamp Footer */}
              <div className="flex items-center justify-between text-[9px] text-slate-500 pt-1 border-t border-slate-900">
                <span>Confidence: {(anom.confidence * 100).toFixed(0)}%</span>
                <span>{new Date(anom.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
