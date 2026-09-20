/**
 * TRINETRA / Shanetra Explore Architecture
 * Centralized Explore API Client
 * Phase 2: Bounded requests, request cancellation (AbortController), and error normalization.
 */

import { ExploreDataset, ExploreLayerDefinition } from "./types"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000"

export interface CatalogStatus {
  local_provider: string
  stac_provider: string
  stac_endpoint: string
  cache: string
  indexed_assets: number
}

class ExploreApiClient {
  private activeControllers: Map<string, AbortController> = new Map()

  private getOrSetController(key: string): AbortController {
    if (this.activeControllers.has(key)) {
      this.activeControllers.get(key)!.abort()
    }
    const controller = new AbortController()
    this.activeControllers.set(key, controller)
    return controller
  }

  async getCatalogStatus(): Promise<CatalogStatus | null> {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/explore/catalog/status`, {
        headers: { Accept: "application/json" },
      })
      if (!res.ok) return null
      return await res.json()
    } catch {
      return null
    }
  }

  async searchDatasets(
    params: {
      bbox?: number[]
      datetime_start?: string
      datetime_end?: string
      collections?: string[]
      provider?: "all" | "local" | "copernicus"
      limit?: number
    },
    customSignal?: AbortSignal
  ): Promise<ExploreDataset[]> {
    const controller = this.getOrSetController("search")
    const signal = customSignal || controller.signal

    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/explore/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          bbox: params.bbox,
          datetime_start: params.datetime_start,
          datetime_end: params.datetime_end,
          collections: params.collections,
          provider: params.provider || "all",
          limit: params.limit || 15,
        }),
        signal,
      })

      if (!res.ok) return []
      const data = await res.json()
      const items = data.items || []

      return items.map((item: any) => ({
        id: item.id,
        provider: item.provider,
        collection: item.collection,
        title: item.properties?.sensor || item.id,
        datetime: item.datetime,
        bbox: item.bbox,
        cloudCover: item.cloud_cover,
        thumbnailUrl: item.thumbnail_url ? `${BACKEND_URL}${item.thumbnail_url}` : undefined,
        assets: item.assets || {},
        properties: item.properties || {},
      }))
    } catch (err: any) {
      if (err.name === "AbortError") {
        return []
      }
      console.warn("[ExploreApiClient] Search error:", err)
      return []
    } finally {
      this.activeControllers.delete("search")
    }
  }

  async getLayers(): Promise<ExploreLayerDefinition[]> {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/explore/layers`, {
        headers: { Accept: "application/json" },
      })
      if (!res.ok) return []
      const data = await res.json()
      return data.map((l: any) => ({
        id: l.id,
        label: l.name,
        category: l.category,
        rendererSupport: l.renderer_support || ["2d", "3d"],
        sourceType: "raster",
        tileTemplate: l.tile_template ? `${BACKEND_URL}${l.tile_template}` : undefined,
        minZoom: l.min_zoom,
        maxZoom: l.max_zoom,
        defaultVisible: l.default_visible,
        userControllable: l.user_controllable,
        aiControllable: l.ai_controllable,
        expensive: l.expensive,
        opacity: l.opacity ?? 1.0,
        attribution: l.attribution,
        assetId: l.asset_id,
      }))
    } catch {
      return []
    }
  }

  async registerDatasetLayer(assetId: string, title?: string): Promise<ExploreLayerDefinition | null> {
    try {
      const url = new URL(`${BACKEND_URL}/api/v1/explore/layers/register`)
      url.searchParams.set("asset_id", assetId)
      if (title) url.searchParams.set("title", title)

      const res = await fetch(url.toString(), {
        method: "POST",
        headers: { Accept: "application/json" },
      })
      if (!res.ok) return null
      const l = await res.json()
      return {
        id: l.id,
        label: l.name,
        category: l.category,
        rendererSupport: l.renderer_support || ["2d", "3d"],
        sourceType: "raster",
        tileTemplate: l.tile_template ? `${BACKEND_URL}${l.tile_template}` : undefined,
        minZoom: l.min_zoom,
        maxZoom: l.max_zoom,
        defaultVisible: l.default_visible,
        userControllable: l.user_controllable,
        aiControllable: l.ai_controllable,
        expensive: l.expensive,
        opacity: l.opacity ?? 1.0,
        attribution: l.attribution,
        assetId: l.asset_id,
      }
    } catch {
      return null
    }
  }
}

export const exploreApi = new ExploreApiClient()
