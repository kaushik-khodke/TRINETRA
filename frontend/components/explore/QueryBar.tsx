"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * QueryBar Component — Natural-Language Earth Command Interface
 * Phase 3: Natural-Language Earth Exploration + Controlled AI Map Commands
 * Enforces execution-on-submit, AbortController cancellation, and state patching.
 */

import React, { useState, useRef, useEffect } from "react"
import { Send, Loader2, X, Sparkles } from "lucide-react"
import { submitExploreQuery } from "@/lib/explore/ai-api"
import { CommandStateCoordinator } from "@/lib/explore/command-state"
import { useGlobeState } from "@/lib/explore/globe-state"
import { AICommandItem } from "@/lib/explore/command-types"
import { QuerySuggestions } from "./QuerySuggestions"
import { CommandActivity } from "./CommandActivity"

export function QueryBar() {
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(false)
  const [activityStatus, setActivityStatus] = useState<
    "idle" | "loading" | "completed" | "partial_failure" | "rejected" | "error"
  >("idle")
  const [summary, setSummary] = useState("")
  const [executionItems, setExecutionItems] = useState<AICommandItem[]>([])
  const [fastPath, setFastPath] = useState(false)
  const [latencyMs, setLatencyMs] = useState(0)

  const abortControllerRef = useRef<AbortController | null>(null)
  const { camera, selectedLayerIds } = useGlobeState()

  // Clean up in-flight requests on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  const handleSubmit = async (textToSubmit?: string) => {
    const raw = textToSubmit !== undefined ? textToSubmit : query
    const clean = raw.trim()
    if (!clean || loading) return

    // Cancel any previous in-flight AI request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    const controller = new AbortController()
    abortControllerRef.current = controller

    setLoading(true)
    setActivityStatus("loading")
    setSummary(`Interpreting "${clean}"...`)
    setExecutionItems([])

    try {
      const response = await submitExploreQuery(
        clean,
        camera,
        selectedLayerIds,
        controller.signal
      )

      setFastPath(response.fast_path)
      setLatencyMs(response.latency_ms)
      setActivityStatus(response.status)
      setSummary(response.summary)
      setExecutionItems(response.commands)

      // Apply state patch deterministically to map / globe
      if (response.status === "completed" || response.status === "partial_failure") {
        CommandStateCoordinator.applyPatch(response.request_id, response.state_patch)
      }
    } catch (err: any) {
      if (err.name === "AbortError") {
        setActivityStatus("rejected")
        setSummary("Previous request superseded by newer command.")
      } else {
        setActivityStatus("error")
        setSummary(err.message || "Failed to process exploration query.")
      }
    } finally {
      setLoading(false)
      abortControllerRef.current = null
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleSelectSuggestion = (s: string) => {
    setQuery(s)
    handleSubmit(s)
  }

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      setLoading(false)
      setActivityStatus("idle")
    }
  }

  return (
    <div className="query-bar-wrapper">
      <div className="query-bar-container" role="search">
        <Sparkles size={15} className="query-bar-ai-icon" />

        <input
          type="text"
          className="query-bar-input"
          placeholder="Ask TRINETRA... (e.g., 'Go to Nagpur', 'Show Sentinel-2', 'Reset')"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          aria-label="Natural language explore command"
          disabled={loading}
        />

        {query && !loading && (
          <button
            type="button"
            className="query-bar-clear-btn"
            onClick={() => setQuery("")}
            title="Clear query"
          >
            <X size={13} />
          </button>
        )}

        {loading ? (
          <button
            type="button"
            className="query-bar-action-btn cancel"
            onClick={handleCancel}
            title="Cancel execution"
          >
            <Loader2 size={14} className="spin" />
            <span>Cancel</span>
          </button>
        ) : (
          <button
            type="button"
            className="query-bar-action-btn submit"
            onClick={() => handleSubmit()}
            disabled={!query.trim()}
            title="Execute command (Enter)"
          >
            <Send size={13} />
            <span>Send</span>
          </button>
        )}
      </div>

      {/* Suggestion Chips */}
      <QuerySuggestions onSelectSuggestion={handleSelectSuggestion} />

      {/* Real-time Command Execution Telemetry HUD */}
      <CommandActivity
        summary={summary}
        items={executionItems}
        status={activityStatus}
        fastPath={fastPath}
        latencyMs={latencyMs}
        onClose={() => setActivityStatus("idle")}
      />
    </div>
  )
}
