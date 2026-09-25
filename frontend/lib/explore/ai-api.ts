/**
 * TRINETRA / Shanetra Explore Architecture
 * AI Exploration API Client
 * Phase 3: Natural-Language Earth Exploration + Controlled AI Map Commands
 */

import { AIQueryResponse, AIStatusInfo } from "./command-types"
import { GlobeCameraState } from "./types"

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  (typeof window !== "undefined" ? "" : "http://127.0.0.1:8000")

export async function submitExploreQuery(
  query: string,
  viewState?: GlobeCameraState,
  activeLayerIds: string[] = [],
  signal?: AbortSignal
): Promise<AIQueryResponse> {
  const payload = {
    query: query.trim(),
    view_state: viewState
      ? {
          latitude: viewState.latitude,
          longitude: viewState.longitude,
          zoom: viewState.zoom,
          mode: "2d",
        }
      : undefined,
    active_layer_ids: activeLayerIds,
    explore_state_version: 1,
  }

  const res = await fetch(`${BASE_URL}/api/v1/explore/ai/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    signal,
  })

  if (!res.ok) {
    const errorText = await res.text()
    throw new Error(`AI Gateway error (${res.status}): ${errorText}`)
  }

  return (await res.json()) as AIQueryResponse
}

export async function getAIStatus(signal?: AbortSignal): Promise<AIStatusInfo> {
  try {
    const res = await fetch(`${BASE_URL}/api/v1/explore/ai/status`, {
      method: "GET",
      signal,
    })
    if (!res.ok) {
      return {
        available: false,
        model: "offline",
        router_model: "offline",
        planner_model: "offline",
        structured_output: false,
        offline_fallback_active: true,
      }
    }
    return (await res.json()) as AIStatusInfo
  } catch {
    return {
      available: false,
      model: "offline",
      router_model: "offline",
      planner_model: "offline",
      structured_output: false,
      offline_fallback_active: true,
    }
  }
}
