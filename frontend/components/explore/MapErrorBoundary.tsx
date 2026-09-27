"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * Map Error Boundary — 2D MapLibre Failure Isolation
 * Phase 1 Foundation
 */

import React, { Component, ErrorInfo, ReactNode } from "react"
import { AlertTriangle, RefreshCw, Globe } from "lucide-react"
import { globeCommandBus } from "@/lib/explore/globe-command-bus"

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class MapErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("[MapErrorBoundary] 2D MapLibre failure captured:", error, errorInfo)
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null })
  }

  handleSwitchTo3D = () => {
    this.setState({ hasError: false, error: null })
    globeCommandBus.dispatch({ type: "SET_VIEW_MODE", mode: "3d" })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="renderer-fallback" role="alert">
          <AlertTriangle size={36} color="#f87171" style={{ marginBottom: 12 }} />
          <h3>2D MAP UNAVAILABLE</h3>
          <p>
            The WebGL map renderer encountered an unexpected initialization or context loss error.
            The rest of TRINETRA remains functional.
          </p>
          <div className="fallback-actions">
            <button type="button" className="btn-tactical-icon" onClick={this.handleRetry}>
              <RefreshCw size={13} />
              <span>Retry 2D Map</span>
            </button>
            <button type="button" className="btn-tactical-icon" onClick={this.handleSwitchTo3D}>
              <Globe size={13} />
              <span>Switch to 3D Globe</span>
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
