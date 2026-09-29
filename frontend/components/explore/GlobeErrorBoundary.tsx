"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * Globe Error Boundary — 3D CesiumJS Failure Isolation
 * Phase 1 Foundation
 */

import React, { Component, ErrorInfo, ReactNode } from "react"
import { AlertTriangle, RefreshCw } from "lucide-react"

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

  render() {
    if (this.state.hasError) {
      return (
        <div className="renderer-fallback" role="alert">
          <AlertTriangle size={36} color="#f87171" style={{ marginBottom: 12 }} />
          <h3>3D GLOBE UNAVAILABLE</h3>
          <p>
            The Cesium 3D graphics context could not be initialized or encountered a WebGL context error.
            Please verify hardware acceleration in your browser settings.
          </p>
          <div className="fallback-actions">
            <button type="button" className="btn-tactical-icon" onClick={this.handleRetry}>
              <RefreshCw size={13} />
              <span>Retry 3D Globe</span>
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
