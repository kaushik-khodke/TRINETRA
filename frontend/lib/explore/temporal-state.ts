/**
 * TRINETRA / Shanetra Explore Architecture
 * Temporal Exploration State Manager
 * Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
 */

import { useEffect, useState } from "react"
import { ObservationDetails, ObservationSummary } from "./types"
import { TemporalApiClient } from "./temporal-api"
import { aoiStateManager } from "./aoi-state"
import { globeCommandBus } from "./globe-command-bus"

export interface TemporalState {
  startDate: string
  endDate: string
  cloudCoverMax: number
  collections: string[]
  sort: "datetime_desc" | "datetime_asc" | "cloud_asc"
  observations: ObservationSummary[]
  selectedObservation: ObservationSummary | null
  selectedObservationDetails: ObservationDetails | null
  loading: boolean
  detailsLoading: boolean
  error: string | null
  isPlaying: boolean
  playIndex: number
}

class TemporalStateManager {
  private state: TemporalState = {
    startDate: "2026-01-01",
    endDate: "2026-09-20",
    cloudCoverMax: 30,
    collections: ["sentinel-2-l2a"],
    sort: "datetime_desc",
    observations: [],
    selectedObservation: null,
    selectedObservationDetails: null,
    loading: false,
    detailsLoading: false,
    error: null,
    isPlaying: false,
    playIndex: 0,
  }

  private listeners: Set<(state: TemporalState) => void> = new Set()
  private abortController: AbortController | null = null
  private playTimer: any = null

  getState(): TemporalState {
    return { ...this.state }
  }

  setState(partial: Partial<TemporalState>): void {
    this.state = { ...this.state, ...partial }
    this.notify()
  }

  setDateRange(startDate: string, endDate: string): void {
    this.setState({ startDate, endDate })
  }

  setCloudCoverMax(cloudCoverMax: number): void {
    this.setState({ cloudCoverMax })
  }

  setCollections(collections: string[]): void {
    this.setState({ collections })
  }

  setSort(sort: "datetime_desc" | "datetime_asc" | "cloud_asc"): void {
    this.setState({ sort })
  }

  async search(): Promise<ObservationSummary[]> {
    if (this.abortController) {
      this.abortController.abort()
    }
    this.abortController = new AbortController()

    this.setState({ loading: true, error: null })

    const aoi = aoiStateManager.getState().activeAOI

    try {
      const res = await TemporalApiClient.searchObservations(
        {
          aoi: aoi || undefined,
          start_datetime: `${this.state.startDate}T00:00:00Z`,
          end_datetime: `${this.state.endDate}T23:59:59Z`,
          collections: this.state.collections,
          cloud_cover_max: this.state.cloudCoverMax,
          sort: this.state.sort,
          limit: 50,
        },
        this.abortController.signal
      )

      const obs = res.observations || []
      this.setState({
        observations: obs,
        loading: false,
        playIndex: 0,
        selectedObservation: obs.length > 0 ? obs[0] : null,
      })

      if (obs.length > 0) {
        this.selectObservation(obs[0])
      }

      return obs
    } catch (e: any) {
      if (e.name === "AbortError") return []
      this.setState({
        loading: false,
        error: e.message || "Failed to search satellite observations.",
      })
      return []
    }
  }

  async selectObservation(
    obs: ObservationSummary | null
  ): Promise<ObservationDetails | null> {
    if (!obs) {
      this.setState({
        selectedObservation: null,
        selectedObservationDetails: null,
      })
      return null
    }

    const idx = this.state.observations.findIndex((o) => o.id === obs.id)
    this.setState({
      selectedObservation: obs,
      playIndex: idx >= 0 ? idx : 0,
      detailsLoading: true,
    })

    // Broadcast to renderers
    globeCommandBus.dispatch({
      type: "SELECT_OBSERVATION",
      observation: obs,
      targetSlot: "primary",
    })

    try {
      const details = await TemporalApiClient.getObservationDetails(obs.id)
      this.setState({
        selectedObservationDetails: details,
        detailsLoading: false,
      })
      return details
    } catch (e) {
      this.setState({ detailsLoading: false })
      return null
    }
  }

  // --- Timeline Playback Controls ---

  play(): void {
    if (this.state.observations.length <= 1) return
    this.setState({ isPlaying: true })

    if (this.playTimer) clearInterval(this.playTimer)
    this.playTimer = setInterval(() => {
      const { observations, playIndex } = this.state
      if (observations.length === 0) return

      const nextIndex = (playIndex + 1) % observations.length
      this.setState({ playIndex: nextIndex })
      this.selectObservation(observations[nextIndex])
    }, 2000)
  }

  pause(): void {
    if (this.playTimer) {
      clearInterval(this.playTimer)
      this.playTimer = null
    }
    this.setState({ isPlaying: false })
  }

  stepNext(): void {
    const { observations, playIndex } = this.state
    if (observations.length <= 1) return
    const nextIdx = (playIndex + 1) % observations.length
    this.selectObservation(observations[nextIdx])
  }

  stepPrev(): void {
    const { observations, playIndex } = this.state
    if (observations.length <= 1) return
    const prevIdx = (playIndex - 1 + observations.length) % observations.length
    this.selectObservation(observations[prevIdx])
  }

  subscribe(listener: (state: TemporalState) => void): () => void {
    this.listeners.add(listener)
    listener(this.getState())
    return () => {
      this.listeners.delete(listener)
    }
  }

  private notify(): void {
    const s = this.getState()
    this.listeners.forEach((l) => l(s))
  }
}

export const temporalStateManager = new TemporalStateManager()

export function useTemporalState(): TemporalState {
  const [state, setState] = useState<TemporalState>(
    temporalStateManager.getState()
  )

  useEffect(() => {
    return temporalStateManager.subscribe(setState)
  }, [])

  return state
}
