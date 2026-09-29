"use client"

/**
 * TRINETRA Explore — Workstation Layers & Bulk Upload State Bridge
 * Connects Explore (2D MapLibre & 3D Cesium) to the backend workstation asset & raster engine.
 * Supports multi-file & folder uploads, unified mosaic rendering, layer deloading/reloading, and per-layer opacity.
 */

import { useState, useEffect } from "react"
import { Asset } from "@/lib/workstation/types"
import { workstationApi } from "@/lib/workstation/api"
import { LayerState, LayerTileItem } from "@/components/workstation/WorkstationDataRail"
import { globeCommandBus } from "./globe-command-bus"

export interface WorkstationLayersSnapshot {
  layers: LayerState[]
  assets: Asset[]
  unloadedLayerIds: Set<string>
  loading: boolean
  activeMissionId: string | null
}

class WorkstationLayersStateManager {
  private layers: LayerState[] = []
  private assets: Asset[] = []
  private unloadedLayerIds: Set<string> = new Set()
  private layerOverrides: Record<string, Partial<LayerState>> = {}
  private activeMissionId: string | null = null
  private loading: boolean = false
  private listeners: Set<(snapshot: WorkstationLayersSnapshot) => void> = new Set()

  getSnapshot(): WorkstationLayersSnapshot {
    return {
      layers: this.layers,
      assets: this.assets,
      unloadedLayerIds: new Set(this.unloadedLayerIds),
      loading: this.loading,
      activeMissionId: this.activeMissionId,
    }
  }

  private notify(): void {
    const snapshot = this.getSnapshot()
    this.listeners.forEach((fn) => fn(snapshot))
  }

  subscribe(listener: (snapshot: WorkstationLayersSnapshot) => void): () => void {
    this.listeners.add(listener)
    listener(this.getSnapshot())
    return () => this.listeners.delete(listener)
  }

  async ensureMission(): Promise<string> {
    if (this.activeMissionId) return this.activeMissionId
    try {
      const msns = await workstationApi.listMissions()
      if (msns && msns.length > 0) {
        this.activeMissionId = msns[0].id
        return msns[0].id
      }
      const created = await workstationApi.createMission({
        name: "Primary Research Mission",
        description: "Auto-initialized workspace for multi-spectral analysis & raster pipeline.",
      })
      this.activeMissionId = created.id
      return created.id
    } catch (e) {
      console.warn("[WorkstationLayersState] Mission init fallback:", e)
      this.activeMissionId = "mission_default"
      return "mission_default"
    }
  }

  async loadAssets(): Promise<void> {
    this.loading = true
    this.notify()
    try {
      const missionId = await this.ensureMission()
      const assetList = await workstationApi.listAssets(missionId)
      this.assets = assetList || []
      this.recalculateLayers()
    } catch (e) {
      console.error("[WorkstationLayersState] Failed to load assets:", e)
    } finally {
      this.loading = false
      this.notify()
    }
  }

  private recalculateLayers(): void {
    const dynamicLayers: LayerState[] = []
    const collectionsMap: Record<string, Asset[]> = {}

    this.assets.forEach((ast) => {
      const col = ast.collection_id || "user-upload"
      if (!collectionsMap[col]) collectionsMap[col] = []
      collectionsMap[col].push(ast)
    })

    Object.entries(collectionsMap).forEach(([collectionId, colAssets]) => {
      if (colAssets.length > 1) {
        let minX = Infinity,
          minY = Infinity,
          maxX = -Infinity,
          maxY = -Infinity
        let totalBytes = 0

        const tiles: LayerTileItem[] = colAssets.map((ast) => {
          const v = ast.versions?.[0]
          const meta = ast.metadata || {}
          const astBbox: [number, number, number, number] =
            meta.bbox && meta.bbox.length === 4
              ? (meta.bbox as [number, number, number, number])
              : [77.62, 23.03, 77.72, 23.13]

          minX = Math.min(minX, astBbox[0])
          minY = Math.min(minY, astBbox[1])
          maxX = Math.max(maxX, astBbox[2])
          maxY = Math.max(maxY, astBbox[3])
          totalBytes += v?.size_bytes || 0

          const tileCoords: [number, number][] =
            meta.coordinates && meta.coordinates.length === 4
              ? meta.coordinates
              : [
                  [astBbox[0], astBbox[3]],
                  [astBbox[2], astBbox[3]],
                  [astBbox[2], astBbox[1]],
                  [astBbox[0], astBbox[1]],
                ]

          return {
            id: ast.id,
            title: ast.title || meta.filename || "Tile",
            filename: meta.filename || ast.external_id || "tile.tif",
            sourceUrl: meta.preview_url || `/api/workstation/assets/${ast.id}/preview`,
            bbox: astBbox,
            coordinates: tileCoords,
            fileSize: v?.size_bytes,
            modality: meta.modality || "Optical",
            modalityLabel: meta.modality_label || "Optical Multi-Spectral",
            modalityColor: meta.modality_color || "#06b6d4",
            modalitySensor: meta.modality_sensor || "Sentinel-2 MSI",
          }
        })

        const mosaicBbox: [number, number, number, number] =
          minX !== Infinity ? [minX, minY, maxX, maxY] : [77.62, 23.03, 77.72, 23.13]
        const first = colAssets[0]
        const primaryModality = first.metadata?.modality_label || "Optical"

        dynamicLayers.push({
          id: `mosaic_${collectionId}`,
          name: collectionId.replace(/^upload_/, "Mosaic: ").replace(/_/g, " "),
          collection: collectionId,
          visible: true,
          opacity: 0.9,
          bands: "B4, B3, B2",
          colorRamp: "Natural Color",
          bbox: mosaicBbox,
          fileSize: totalBytes,
          modality: first.metadata?.modality || "Optical",
          modalityLabel: `${primaryModality} (${colAssets.length} Scenes)`,
          modalityColor: first.metadata?.modality_color || "#06b6d4",
          modalityBgColor: "rgba(6, 182, 212, 0.12)",
          modalitySensor: first.metadata?.modality_sensor || "Multi-Tile Sensor",
          isMosaic: true,
          tileCount: colAssets.length,
          tiles,
        })
      } else {
        const ast = colAssets[0]
        const v = ast.versions?.[0]
        const meta = ast.metadata || {}
        const astBbox: [number, number, number, number] =
          meta.bbox && meta.bbox.length === 4
            ? (meta.bbox as [number, number, number, number])
            : [77.62, 23.03, 77.72, 23.13]

        const coordinates: [number, number][] =
          meta.coordinates && meta.coordinates.length === 4
            ? meta.coordinates
            : [
                [astBbox[0], astBbox[3]],
                [astBbox[2], astBbox[3]],
                [astBbox[2], astBbox[1]],
                [astBbox[0], astBbox[1]],
              ]

        const modality = meta.modality || "RGB"

        dynamicLayers.push({
          id: ast.id,
          name: ast.title || meta.filename || "Scene",
          collection: ast.collection_id || "user-upload",
          visible: true,
          opacity: 0.9,
          bands: "True Color RGB",
          colorRamp: "Natural RGB",
          sourceUrl: meta.preview_url || `/api/workstation/assets/${ast.id}/preview`,
          coordinates,
          bbox: astBbox,
          fileSize: v?.size_bytes,
          modality,
          modalityLabel: meta.modality_label || (modality === "SAR" ? "Sentinel-1 SAR" : `${modality} Raster`),
          modalityColor: meta.modality_color || (modality === "SAR" ? "#eab308" : "#06b6d4"),
          modalityBgColor: modality === "SAR" ? "rgba(234, 179, 8, 0.12)" : "rgba(6, 182, 212, 0.12)",
          modalitySensor: meta.modality_sensor || "Multi-Spectral Imagery",
          isMosaic: false,
          tileCount: 1,
        })
      }
    })

    // Preserve overrides and deloaded statuses
    const merged = dynamicLayers.map((l) => {
      const isDeloaded = this.unloadedLayerIds.has(l.id)
      const ov = this.layerOverrides[l.id] || {}
      return {
        ...l,
        ...ov,
        isDeloaded,
      }
    })

    this.layers = merged
    this.notify()
  }

  async uploadFile(
    file: File,
    title?: string,
    onProgress?: (percent: number, loaded: number, total: number) => void,
    collectionId?: string
  ): Promise<any> {
    const missionId = await this.ensureMission()
    const result = await workstationApi.uploadAsset(missionId, file, title, onProgress, collectionId)
    await this.loadAssets()
    return result
  }

  updateLayer(layerId: string, updates: Partial<LayerState>): void {
    this.layerOverrides[layerId] = {
      ...(this.layerOverrides[layerId] || {}),
      ...updates,
    }
    this.layers = this.layers.map((l) => (l.id === layerId ? { ...l, ...updates } : l))
    this.notify()
  }

  deloadLayer(layerId: string): void {
    this.unloadedLayerIds.add(layerId)
    this.layers = this.layers.map((l) => (l.id === layerId ? { ...l, isDeloaded: true } : l))
    this.notify()
  }

  reloadLayer(layerId: string): void {
    this.unloadedLayerIds.delete(layerId)
    this.layers = this.layers.map((l) => (l.id === layerId ? { ...l, isDeloaded: false } : l))
    this.notify()
  }

  deloadAllLayers(): void {
    const newDeloaded = new Set(this.unloadedLayerIds)
    this.layers.forEach((l) => newDeloaded.add(l.id))
    this.unloadedLayerIds = newDeloaded
    this.layers = this.layers.map((l) => ({ ...l, isDeloaded: true }))
    this.notify()
  }

  reloadAllLayers(): void {
    this.unloadedLayerIds.clear()
    this.layers = this.layers.map((l) => ({ ...l, isDeloaded: false }))
    this.notify()
  }

  async deleteLayer(layerId: string): Promise<void> {
    const missionId = await this.ensureMission()
    const target = this.layers.find((l) => l.id === layerId)
    if (!target) return

    if (target.isMosaic && target.collection) {
      await workstationApi.deleteCollection(missionId, target.collection)
    } else {
      await workstationApi.deleteAsset(missionId, target.id)
    }
    this.unloadedLayerIds.delete(layerId)
    delete this.layerOverrides[layerId]
    await this.loadAssets()
  }

  async deleteAsset(assetId: string): Promise<void> {
    const missionId = await this.ensureMission()
    await workstationApi.deleteAsset(missionId, assetId)
    await this.loadAssets()
  }

  async deleteCollection(collectionId: string): Promise<void> {
    const missionId = await this.ensureMission()
    await workstationApi.deleteCollection(missionId, collectionId)
    await this.loadAssets()
  }

  fitBounds(bbox: [number, number, number, number]): void {
    globeCommandBus.dispatch({
      type: "FOCUS_ANALYSIS_REGION",
      findingId: "layer_extent_zoom",
      bounds: bbox,
    })
  }
}

export const workstationLayersState = new WorkstationLayersStateManager()

export function useWorkstationLayers(): WorkstationLayersSnapshot {
  const [snapshot, setSnapshot] = useState<WorkstationLayersSnapshot>(workstationLayersState.getSnapshot())

  useEffect(() => {
    return workstationLayersState.subscribe(setSnapshot)
  }, [])

  return snapshot
}
