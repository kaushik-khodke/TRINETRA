/**
 * TRINETRA / Shanetra Explore Architecture
 * Performance Monitoring & Metrics Instrumentation
 * Phase 1 Foundation
 */

import { ExploreViewMode, PerformanceMetrics } from "./types"

export class PerformanceMonitor {
  private metrics: PerformanceMetrics = {
    initTimeMs: 0,
    modeSwitchTimeMs: 0,
    lastFrameTimestamp: performance.now(),
    estimatedFps: 60,
    activeRenderer: "2d",
  }

  private startTime: number = 0
  private frameCount: number = 0
  private lastFpsCalculation: number = performance.now()
  private listeners: Set<(metrics: PerformanceMetrics) => void> = new Set()

  startInitTimer(): void {
    this.startTime = performance.now()
  }

  recordInitComplete(renderer: ExploreViewMode): number {
    const elapsed = performance.now() - (this.startTime || performance.now())
    this.metrics.initTimeMs = Math.round(elapsed)
    this.metrics.activeRenderer = renderer
    this.notify()
    return this.metrics.initTimeMs
  }

  recordModeSwitch(from: ExploreViewMode, to: ExploreViewMode, durationMs: number): void {
    this.metrics.modeSwitchTimeMs = Math.round(durationMs)
    this.metrics.activeRenderer = to
    this.notify()
  }

  recordFrame(): void {
    const now = performance.now()
    this.frameCount++
    this.metrics.lastFrameTimestamp = now

    if (now - this.lastFpsCalculation >= 1000) {
      this.metrics.estimatedFps = Math.min(60, Math.round((this.frameCount * 1000) / (now - this.lastFpsCalculation)))
      this.frameCount = 0
      this.lastFpsCalculation = now
      this.notify()
    }
  }

  getMetrics(): PerformanceMetrics {
    return { ...this.metrics }
  }

  subscribe(listener: (metrics: PerformanceMetrics) => void): () => void {
    this.listeners.add(listener)
    listener(this.getMetrics())
    return () => this.listeners.delete(listener)
  }

  private notify(): void {
    const snapshot = this.getMetrics()
    this.listeners.forEach((fn) => fn(snapshot))
  }
}

export const performanceMonitor = new PerformanceMonitor()
