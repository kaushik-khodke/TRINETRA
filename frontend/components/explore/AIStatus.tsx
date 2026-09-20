"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * AI Status Component
 * Phase 3: Natural-Language Earth Exploration + Controlled AI Map Commands
 * Telemetry badge showing Ollama AI availability and active planner model.
 */

import React, { useEffect, useState } from "react"
import { Sparkles, Bot, AlertCircle } from "lucide-react"
import { getAIStatus } from "@/lib/explore/ai-api"
import { AIStatusInfo } from "@/lib/explore/command-types"

export function AIStatus() {
  const [status, setStatus] = useState<AIStatusInfo>({
    available: false,
    model: "checking...",
    router_model: "checking...",
    planner_model: "checking...",
    structured_output: true,
    offline_fallback_active: false,
  })

  useEffect(() => {
    let mounted = true
    const check = async () => {
      const s = await getAIStatus()
      if (mounted) setStatus(s)
    }
    check()
    const timer = setInterval(check, 30000)
    return () => {
      mounted = false
      clearInterval(timer)
    }
  }, [])

  return (
    <div
      className={`ai-status-badge ${status.available ? "online" : "offline"}`}
      title={
        status.available
          ? `AI Engine Ready: Planner (${status.planner_model}) & Router (${status.router_model})`
          : "Local Ollama Offline: Deterministic Fast-Path commands ('reset', 'zoom in', 'show boundaries') remain active."
      }
    >
      {status.available ? (
        <>
          <Sparkles size={12} className="ai-icon-pulse" />
          <span className="ai-status-text">AI READY</span>
          <span className="ai-model-tag">{status.planner_model.split(":")[0]}</span>
        </>
      ) : (
        <>
          <AlertCircle size={12} style={{ color: "#f59e0b" }} />
          <span className="ai-status-text" style={{ color: "#f59e0b" }}>AI OFFLINE</span>
          <span className="ai-model-tag" style={{ color: "#94a3b8" }}>FALLBACK</span>
        </>
      )}
    </div>
  )
}
