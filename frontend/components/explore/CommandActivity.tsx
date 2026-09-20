"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * Command Activity HUD Component
 * Phase 3: Natural-Language Earth Exploration + Controlled AI Map Commands
 * Live step-by-step telemetry displaying accepted, executed, and completed actions.
 */

import React from "react"
import { CheckCircle2, AlertTriangle, XCircle, Clock, Zap } from "lucide-react"
import { AICommandItem } from "@/lib/explore/command-types"

interface CommandActivityProps {
  summary: string
  items: AICommandItem[]
  status: "idle" | "loading" | "completed" | "partial_failure" | "rejected" | "error"
  fastPath: boolean
  latencyMs: number
  onClose?: () => void
}

export function CommandActivity({
  summary,
  items,
  status,
  fastPath,
  latencyMs,
  onClose,
}: CommandActivityProps) {
  if (status === "idle") return null

  return (
    <div className="command-activity-hud" role="region" aria-label="AI Command Activity">
      <div className="activity-hud-header">
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          {fastPath ? (
            <span className="fast-path-badge">
              <Zap size={10} />
              <span>FAST PATH ({latencyMs.toFixed(1)}ms)</span>
            </span>
          ) : (
            <span className="ai-path-badge">
              <Clock size={10} />
              <span>AI GATEWAY ({latencyMs.toFixed(0)}ms)</span>
            </span>
          )}
        </div>
        {onClose && (
          <button type="button" className="activity-close-btn" onClick={onClose} aria-label="Dismiss">
            ×
          </button>
        )}
      </div>

      <div className="activity-summary-text">{summary}</div>

      {items.length > 0 && (
        <div className="activity-items-list">
          {items.map((item) => (
            <div key={item.command_id} className={`activity-step-item status-${item.status}`}>
              {item.status === "executed" && <CheckCircle2 size={13} className="step-icon success" />}
              {item.status === "no_op" && <CheckCircle2 size={13} className="step-icon no-op" />}
              {item.status === "failed" && <XCircle size={13} className="step-icon error" />}
              {item.status === "cancelled" && <AlertTriangle size={13} className="step-icon cancelled" />}
              <span className="step-message">{item.message}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
