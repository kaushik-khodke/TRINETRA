"use client"

/**
 * TRINETRA Phase 7 — Continuous Monitoring & Real-Time Alert Panel
 * Manages automated sentinel observation watchers, scheduled intelligence jobs,
 * and duplicate-suppressed alert feeds.
 */

import React, { useState } from "react"
import {
  MonitorDefinition,
  MonitorAlert,
} from "@/lib/explore/intelligence-types"
import {
  Radio,
  Bell,
  RefreshCw,
  Plus,
  Trash2,
  CheckCircle2,
  AlertOctagon,
  AlertTriangle,
  Info,
  Power,
} from "lucide-react"

interface Props {
  monitors: MonitorDefinition[]
  alerts: MonitorAlert[]
  isLoadingMonitors: boolean
  isLoadingAlerts: boolean
  onToggleMonitor: (monitorId: string) => void
  onDeleteMonitor: (monitorId: string) => void
  onAcknowledgeAlert: (alertId: string) => void
  onCreateMonitor: (data: any) => Promise<any>
  onRefresh: () => void
}

const SEVERITY_THEMES: Record<string, { bg: string; border: string; text: string; icon: React.FC<any> }> = {
  CRITICAL: { bg: "bg-rose-950/70", border: "border-rose-700/60", text: "text-rose-400", icon: AlertOctagon },
  WARNING: { bg: "bg-amber-950/70", border: "border-amber-700/60", text: "text-amber-400", icon: AlertTriangle },
  INFO: { bg: "bg-sky-950/70", border: "border-sky-700/60", text: "text-sky-400", icon: Info },
}

export const MonitoringPanel: React.FC<Props> = ({
  monitors,
  alerts,
  isLoadingMonitors,
  isLoadingAlerts,
  onToggleMonitor,
  onDeleteMonitor,
  onAcknowledgeAlert,
  onCreateMonitor,
  onRefresh,
}) => {
  const [activeTab, setActiveTab] = useState<"monitors" | "alerts">("monitors")
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false)

  // Form state
  const [monitorName, setMonitorName] = useState<string>("")
  const [collection, setCollection] = useState<string>("sentinel-2-l2a")
  const [cadence, setCadence] = useState<string>("daily")
  const [cooldown, setCooldown] = useState<number>(24)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!monitorName.trim()) return
    setIsSubmitting(true)
    try {
      await onCreateMonitor({
        name: monitorName.trim(),
        observation_collection: collection,
        schedule_cadence: cadence,
        cooldown_hours: cooldown,
        trigger_condition: {
          operator: "AND",
          conditions: [
            { field: "confidence", operator: ">=", value: 0.65 },
            { field: "change_area_ha", operator: ">", value: 1.0 },
          ],
        },
      })
      setMonitorName("")
      setShowCreateModal(false)
    } catch {
      // Handled in state hook
    } finally {
      setIsSubmitting(false)
    }
  }

  const unackAlertCount = alerts.filter((a) => !a.acknowledged).length

  return (
    <div className="flex flex-col gap-3 font-mono text-xs">
      {/* Sub-navigation bar */}
      <div className="flex items-center justify-between pb-1 border-b border-slate-800">
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setActiveTab("monitors")}
            className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-colors ${
              activeTab === "monitors"
                ? "bg-orange-500/20 text-orange-300 border border-orange-500/50"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Watchers ({monitors.length})
          </button>
          <button
            onClick={() => setActiveTab("alerts")}
            className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-colors flex items-center gap-1 ${
              activeTab === "alerts"
                ? "bg-amber-500/20 text-amber-300 border border-amber-500/50"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <span>Alerts</span>
            {unackAlertCount > 0 && (
              <span className="px-1 rounded-full bg-rose-600 text-slate-100 text-[9px]">
                {unackAlertCount}
              </span>
            )}
          </button>
        </div>

        <div className="flex items-center gap-1">
          {activeTab === "monitors" && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-orange-400 transition-colors"
              title="Add New Monitor"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            onClick={onRefresh}
            disabled={isLoadingMonitors || isLoadingAlerts}
            title="Refresh"
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <RefreshCw
              className={`w-3.5 h-3.5 ${
                isLoadingMonitors || isLoadingAlerts ? "animate-spin text-orange-400" : ""
              }`}
            />
          </button>
        </div>
      </div>

      {/* Create Monitor Modal */}
      {showCreateModal && (
        <form onSubmit={handleCreateSubmit} className="p-3 bg-slate-950 border border-orange-800/80 rounded-lg space-y-2.5">
          <div className="text-[11px] font-bold text-orange-300 flex items-center gap-1">
            <Radio className="w-3.5 h-3.5" />
            <span>Configure Continuous Monitor</span>
          </div>

          <div className="space-y-1">
            <label className="text-[10px] text-slate-400">Monitor Name</label>
            <input
              type="text"
              placeholder="e.g. Eastern Ghats Forest Watcher"
              value={monitorName}
              onChange={(e) => setMonitorName(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs focus:outline-none focus:border-orange-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <label className="text-[10px] text-slate-400">Collection</label>
              <select
                value={collection}
                onChange={(e) => setCollection(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-[11px]"
              >
                <option value="sentinel-2-l2a">Sentinel-2 (Optical)</option>
                <option value="sentinel-1-grd">Sentinel-1 (SAR)</option>
                <option value="landsat-8-c2-l2">Landsat-8 (Optical)</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] text-slate-400">Cadence</label>
              <select
                value={cadence}
                onChange={(e) => setCadence(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-[11px]"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="per_acquisition">Per Acquisition</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-1.5 pt-1">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="px-2 py-1 text-[10px] text-slate-400 hover:text-slate-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!monitorName.trim() || isSubmitting}
              className="px-2.5 py-1 text-[10px] bg-orange-600 hover:bg-orange-500 disabled:opacity-50 font-semibold text-slate-950 rounded"
            >
              {isSubmitting ? "Creating..." : "Save Monitor"}
            </button>
          </div>
        </form>
      )}

      {/* Monitors List Tab */}
      {activeTab === "monitors" && (
        <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-orange-500/20">
          {monitors.length === 0 && !isLoadingMonitors && (
            <div className="text-center py-8 text-slate-500 text-xs">
              <Radio className="w-8 h-8 mx-auto mb-2 text-slate-600" />
              <p>No continuous monitors active.</p>
              <p className="text-[10px] mt-1 text-slate-600">
                Click (+) to configure recurring checks against new satellite observations.
              </p>
            </div>
          )}

          {monitors.map((m) => (
            <div
              key={m.monitor_id}
              className="p-2.5 bg-slate-950/70 border border-slate-800/80 rounded-lg space-y-2"
            >
              <div className="flex items-start justify-between gap-1.5">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        m.enabled ? "bg-emerald-400 animate-pulse" : "bg-slate-600"
                      }`}
                    />
                    <span className="text-xs font-semibold text-slate-200">{m.name}</span>
                  </div>
                  <div className="text-[9px] text-slate-400">
                    {m.observation_collection} • {m.schedule_cadence}
                  </div>
                </div>

                <div className="flex items-center gap-1">
                  <button
                    onClick={() => onToggleMonitor(m.monitor_id)}
                    title={m.enabled ? "Disable monitor" : "Enable monitor"}
                    className={`p-1 rounded text-xs transition-colors ${
                      m.enabled
                        ? "bg-emerald-950 border border-emerald-700/60 text-emerald-300"
                        : "bg-slate-900 border border-slate-700 text-slate-500"
                    }`}
                  >
                    <Power className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => onDeleteMonitor(m.monitor_id)}
                    title="Delete monitor"
                    className="p-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-400 hover:text-rose-400 transition-colors"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>

              {/* Execution telemetry */}
              <div className="flex items-center justify-between text-[9px] text-slate-500 pt-1 border-t border-slate-900">
                <span>Runs: {m.total_runs || 0}</span>
                <span>Cooldown: {m.cooldown_hours}h</span>
                <span>{new Date(m.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Alerts Feed Tab */}
      {activeTab === "alerts" && (
        <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-amber-500/20">
          {alerts.length === 0 && !isLoadingAlerts && (
            <div className="text-center py-8 text-slate-500 text-xs">
              <Bell className="w-8 h-8 mx-auto mb-2 text-slate-600" />
              <p>No alerts triggered by active monitors.</p>
            </div>
          )}

          {alerts.map((al) => {
            const theme = SEVERITY_THEMES[al.severity] || SEVERITY_THEMES.INFO
            const Icon = theme.icon

            return (
              <div
                key={al.alert_id}
                className={`p-2.5 rounded-lg border flex flex-col gap-1.5 ${
                  al.acknowledged
                    ? "bg-slate-950/40 border-slate-900 text-slate-500"
                    : `${theme.bg} ${theme.border} text-slate-200`
                }`}
              >
                <div className="flex items-start justify-between gap-1.5">
                  <div className="flex items-center gap-1.5">
                    <Icon className={`w-3.5 h-3.5 ${theme.text}`} />
                    <span className={`text-[9px] font-bold uppercase ${theme.text}`}>
                      {al.severity}
                    </span>
                    <span className="text-[9px] text-slate-400 font-mono">
                      {al.alert_fingerprint.slice(0, 8)}
                    </span>
                  </div>

                  {!al.acknowledged && (
                    <button
                      onClick={() => onAcknowledgeAlert(al.alert_id)}
                      className="text-[9px] px-1.5 py-0.5 rounded bg-slate-900 hover:bg-slate-800 text-orange-300 border border-slate-700 flex items-center gap-1 transition-colors"
                    >
                      <CheckCircle2 className="w-3 h-3" />
                      <span>Ack</span>
                    </button>
                  )}
                </div>

                <p className="text-[10px] text-slate-300 font-mono">{al.trigger_reason}</p>

                <div className="text-[9px] text-slate-500 pt-0.5">
                  Triggered: {new Date(al.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
