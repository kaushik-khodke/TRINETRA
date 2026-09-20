"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * Globe Error Boundary — 3D CesiumJS Failure Isolation
 * Phase 1 Foundation
 */

import React, { Component, ErrorInfo, ReactNode } from "react"
import { AlertTriangle, RefreshCw, Map } from "lucide-react"
import { globeCommandBus } from "@/lib/explore/globe-command-bus"

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class GlobeErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("[GlobeErrorBoundary] 3D Cesium failure captured:", error, errorInfo)
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null })
  }

  handleSwitchTo2D = () => {
    this.setState({ hasError: false, error: null })
    globeCommandBus.dispatch({ type: "SET_VIEW_MODE", mode: "2d" })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="renderer-fallback" role="alert">
          <AlertTriangle size={36} color="#f87171" style={{ marginBottom: 12 }} />
          <h3>3D GLOBE UNAVAILABLE</h3>
          <p>
            The Cesium 3D graphics context could not be initialized or encountered a shader error.
            You can continue using the 2D MapLibre view seamlessly.
          </p>
          <div className="fallback-actions">
            <button type="button" className="btn-tactical-icon" onClick={this.handleRetry}>
              <RefreshCw size={13} />
              <span>Retry 3D Globe</span>
            </button>
            <button type="button" className="btn-tactical-icon" onClick={this.handleSwitchTo2D}>
              <Map size={13} />
              <span>Switch to 2D Map</span>
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
