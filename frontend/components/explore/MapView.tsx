"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * MapView Component — MapLibre GL JS 2D Vector/Raster Map
 * Phase 4: AOI Vector Rendering & Interactive Selection, Dual Observation Layers, Camera Synchronization.
 */

import React, { useEffect, useRef } from "react"
import maplibregl, { Map as MapLibreMap } from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"
import { DEFAULT_2D_BASEMAP_STYLE, DEFAULT_CAMERA_STATE } from "@/lib/explore/constants"
import { globeController } from "@/lib/explore/globe-controller"
import { globeState } from "@/lib/explore/globe-state"
import { performanceMonitor } from "@/lib/explore/performance"
import { GlobeCameraState, RendererAdapter } from "@/lib/explore/types"
import { aoiStateManager } from "@/lib/explore/aoi-state"
import { globeCommandBus } from "@/lib/explore/globe-command-bus"
import { cameraSyncBus } from "@/lib/explore/camera-sync"

interface MapViewProps {
  viewId?: "view-a" | "view-b"
}

export default function MapView({ viewId = "view-a" }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const drawStartRef = useRef<[number, number] | null>(null)
  const polygonPointsRef = useRef<[number, number][]>([])

  useEffect(() => {
    if (!containerRef.current) return

    performanceMonitor.startInitTimer()
    globeState.setRendererStatus("loading")

    // Check WebGL availability
    const canvas = document.createElement("canvas")
    const gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl")
    if (!gl) {
      globeState.setWebglSupported(false)
      globeState.setRendererStatus("error", "WebGL not supported by current browser environment")
      return
    }

    const currentCam = globeState.getState().camera

    try {
      const map = new maplibregl.Map({
        container: containerRef.current,
        style: DEFAULT_2D_BASEMAP_STYLE as any,
        center: [currentCam.longitude, currentCam.latitude],
        zoom: currentCam.zoom,
        pitch: 0,
        bearing: 0,
        attributionControl: false,
      })

      mapRef.current = map

      // Map loaded successfully
      map.on("load", () => {
        performanceMonitor.recordInitComplete("2d")
        globeState.setRendererStatus("ready")

        // If AOI was already set, display it
        const currentAOI = aoiStateManager.getState().activeAOI
        if (currentAOI) {
          updateAOILayers(map, currentAOI)
        }
      })

      // Sync camera state on movement
      const handleCameraChange = () => {
        if (!map) return
        performanceMonitor.recordFrame()
        const center = map.getCenter()
        const zoom = map.getZoom()
        const bearing = map.getBearing()
        const pitch = map.getPitch()

        const cam: GlobeCameraState = {
          latitude: center.lat,
          longitude: center.lng,
          zoom: zoom,
          heading: bearing,
          pitch: pitch,
          roll: 0,
        }

        globeState.setCamera(cam)
        cameraSyncBus.dispatch(viewId, cam)
      }

      map.on("move", handleCameraChange)
      map.on("zoom", handleCameraChange)
      map.on("rotate", handleCameraChange)
      map.on("pitch", handleCameraChange)

      // Interactive AOI Drawing Handlers
      map.on("click", (e) => {
        const { drawMode } = aoiStateManager.getState()
        if (!drawMode) return

        const lngLat: [number, number] = [e.lngLat.lng, e.lngLat.lat]

        if (drawMode === "rectangle") {
          if (!drawStartRef.current) {
            // First corner
            drawStartRef.current = lngLat
          } else {
            // Second corner: finalize box
            const [x1, y1] = drawStartRef.current
            const [x2, y2] = lngLat
            const minX = Math.min(x1, x2)
            const maxX = Math.max(x1, x2)
            const minY = Math.min(y1, y2)
            const maxY = Math.max(y1, y2)

            const boxGeoJSON = {
              type: "Polygon",
              coordinates: [
                [
                  [minX, minY],
                  [maxX, minY],
                  [maxX, maxY],
                  [minX, maxY],
                  [minX, minY],
                ],
              ],
            }

            drawStartRef.current = null
            aoiStateManager.setAOI(boxGeoJSON)
          }
        } else if (drawMode === "polygon") {
          polygonPointsRef.current.push(lngLat)
          if (polygonPointsRef.current.length >= 3) {
            // Render temporary preview
            const previewRing = [...polygonPointsRef.current, polygonPointsRef.current[0]]
            updateAOILayers(map, { type: "Polygon", coordinates: [previewRing] })
          }
        }
      })

      map.on("dblclick", (e) => {
        const { drawMode } = aoiStateManager.getState()
        if (drawMode === "polygon" && polygonPointsRef.current.length >= 3) {
          e.preventDefault()
          const closedRing = [...polygonPointsRef.current, polygonPointsRef.current[0]]
          const polyGeoJSON = {
            type: "Polygon",
            coordinates: [closedRing],
          }
          polygonPointsRef.current = []
          aoiStateManager.setAOI(polyGeoJSON)
        }
      })

      map.on("mousemove", (e) => {
        const { drawMode } = aoiStateManager.getState()
        if (drawMode === "rectangle" && drawStartRef.current) {
          const [x1, y1] = drawStartRef.current
          const [x2, y2] = [e.lngLat.lng, e.lngLat.lat]
          const minX = Math.min(x1, x2)
          const maxX = Math.max(x1, x2)
          const minY = Math.min(y1, y2)
          const maxY = Math.max(y1, y2)

          const previewBox = {
            type: "Polygon",
            coordinates: [
              [
                [minX, minY],
                [maxX, minY],
                [maxX, maxY],
                [minX, maxY],
                [minX, minY],
              ],
            ],
          }
          updateAOILayers(map, previewBox)
        }
      })

      map.on("error", (e) => {
        console.warn("[MapView] MapLibre internal warning/error:", e)
      })

      // Register with centralized GlobeController
      const adapter: RendererAdapter = {
        flyTo: (target) => {
          if (!mapRef.current) return
          mapRef.current.flyTo({
            center: [target.longitude, target.latitude],
            zoom: target.zoom ?? mapRef.current.getZoom(),
            bearing: target.heading ?? 0,
            pitch: target.pitch ?? 0,
            duration: (target.duration ?? 1.5) * 1000,
          })
        },
        resetView: () => {
          if (!mapRef.current) return
          mapRef.current.flyTo({
            center: [DEFAULT_CAMERA_STATE.longitude, DEFAULT_CAMERA_STATE.latitude],
            zoom: DEFAULT_CAMERA_STATE.zoom,
            bearing: 0,
            pitch: 0,
            duration: 1200,
          })
        },
        setLayerVisibility: (layerId, visible) => {
          if (!mapRef.current) return
          if (layerId === "layer-base-dark" && mapRef.current.getLayer("esri-dark-layer")) {
            mapRef.current.setLayoutProperty("esri-dark-layer", "visibility", visible ? "visible" : "none")
            return
          }
          if (mapRef.current.getLayer(layerId)) {
            mapRef.current.setLayoutProperty(layerId, "visibility", visible ? "visible" : "none")
          }
        },
        setLayerOpacity: (layerId, opacity) => {
          if (!mapRef.current) return
          if (layerId === "layer-base-dark" && mapRef.current.getLayer("esri-dark-layer")) {
            mapRef.current.setPaintProperty("esri-dark-layer", "raster-opacity", opacity)
            return
          }
          if (mapRef.current.getLayer(layerId)) {
            mapRef.current.setPaintProperty(layerId, "raster-opacity", opacity)
          }
        },
        addLayerSource: (layerDef) => {
          if (!mapRef.current || !layerDef.tileTemplate) return
          const m = mapRef.current
          if (m.getLayer(layerDef.id)) return

          try {
            if (!m.getSource(layerDef.id)) {
              m.addSource(layerDef.id, {
                type: "raster",
                tiles: [layerDef.tileTemplate],
                tileSize: 256,
                minzoom: layerDef.minZoom ?? 0,
                maxzoom: layerDef.maxZoom ?? 20,
              })
            }

            m.addLayer({
              id: layerDef.id,
              type: "raster",
              source: layerDef.id,
              paint: {
                "raster-opacity": layerDef.opacity ?? 1.0,
              },
            })
          } catch (e) {
            console.warn("[MapView] Failed to attach tile layer:", e)
          }
        },
        removeLayerSource: (layerId) => {
          if (!mapRef.current) return
          const m = mapRef.current
          try {
            if (m.getLayer(layerId)) m.removeLayer(layerId)
            if (m.getSource(layerId)) m.removeSource(layerId)
          } catch (e) {
            // Safe removal
          }
        },
        setAOI: (geom) => {
          if (mapRef.current) updateAOILayers(mapRef.current, geom)
        },
        clearAOI: () => {
          if (mapRef.current) updateAOILayers(mapRef.current, null)
        },
        getCameraState: (): GlobeCameraState => {
          if (!mapRef.current) return { ...DEFAULT_CAMERA_STATE }
          const c = mapRef.current.getCenter()
          return {
            latitude: c.lat,
            longitude: c.lng,
            zoom: mapRef.current.getZoom(),
            heading: mapRef.current.getBearing(),
            pitch: mapRef.current.getPitch(),
          }
        },
        destroy: () => {
          if (mapRef.current) {
            mapRef.current.remove()
            mapRef.current = null
          }
        },
      }

      globeController.registerAdapter("2d", adapter)

      // Listen to GlobeCommandBus
      const unsubBus = globeCommandBus.subscribe((cmd) => {
        if (!mapRef.current) return
        if (cmd.type === "SET_AOI") {
          updateAOILayers(mapRef.current, cmd.geometry)
        } else if (cmd.type === "CLEAR_AOI") {
          updateAOILayers(mapRef.current, null)
        } else if (cmd.type === "FOCUS_ANALYSIS_REGION") {
          const b = cmd.bounds
          if (b && b.length === 4) {
            mapRef.current.fitBounds(
              [
                [b[0], b[1]],
                [b[2], b[3]],
              ],
              { padding: 50, maxZoom: 17, duration: 1000 }
            )
          }
        }
      })

      // Listen to CameraSyncBus
      const unsubSync = cameraSyncBus.subscribe(({ origin, camera }) => {
        if (!mapRef.current || origin === viewId) return
        const c = mapRef.current.getCenter()
        const latDiff = Math.abs(c.lat - camera.latitude)
        const lngDiff = Math.abs(c.lng - camera.longitude)
        const zoomDiff = Math.abs(mapRef.current.getZoom() - camera.zoom)

        if (latDiff > 0.0001 || lngDiff > 0.0001 || zoomDiff > 0.01) {
          mapRef.current.jumpTo({
            center: [camera.longitude, camera.latitude],
            zoom: camera.zoom,
            bearing: camera.heading,
            pitch: camera.pitch,
          })
        }
      })

      return () => {
        unsubBus()
        unsubSync()
        globeController.unregisterAdapter("2d")
        if (mapRef.current) {
          mapRef.current.remove()
          mapRef.current = null
        }
      }
    } catch (err: any) {
      console.error("[MapView] Failed to initialize MapLibre GL:", err)
      globeState.setRendererStatus("error", err?.message || "Failed to initialize MapLibre")
    }
  }, [viewId])

  return (
    <div className="map-container" ref={containerRef} style={{ width: "100%", height: "100%" }} />
  )
}

function updateAOILayers(map: MapLibreMap, geometry: any | null) {
  if (!map || !map.isStyleLoaded()) return

  const sourceId = "trinetra-aoi-source"
  const fillId = "trinetra-aoi-fill"
  const outlineId = "trinetra-aoi-outline"

  if (!geometry) {
    if (map.getLayer(fillId)) map.removeLayer(fillId)
    if (map.getLayer(outlineId)) map.removeLayer(outlineId)
    if (map.getSource(sourceId)) map.removeSource(sourceId)
    return
  }

  const data = {
    type: "Feature",
    geometry: geometry.type === "Feature" ? geometry.geometry : geometry,
    properties: {},
  }

  const existingSource = map.getSource(sourceId) as maplibregl.GeoJSONSource
  if (existingSource) {
    existingSource.setData(data as any)
  } else {
    try {
      map.addSource(sourceId, {
        type: "geojson",
        data: data as any,
      })

      map.addLayer({
        id: fillId,
        type: "fill",
        source: sourceId,
        paint: {
          "fill-color": "#06b6d4",
          "fill-opacity": 0.18,
        },
      })

      map.addLayer({
        id: outlineId,
        type: "line",
        source: sourceId,
        paint: {
          "line-color": "#22d3ee",
          "line-width": 2.5,
          "line-dasharray": [2, 1],
        },
      })
    } catch (e) {
      console.warn("[MapView] Could not attach AOI vector layers:", e)
    }
  }
}
