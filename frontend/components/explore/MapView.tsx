"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * MapView Component — MapLibre GL JS 2D Vector/Raster Map
 * Phase 4: AOI Vector Rendering & Interactive Selection, Dual Observation Layers, Camera Synchronization.
 * Robust 2D AOI Drawing with Drag & Two-Click Box Mode, Real-Time Polygon Rubber-Band Preview,
 * and In-Map Interactive Controls.
 */

import React, { useEffect, useRef, useState } from "react"
import maplibregl, { Map as MapLibreMap } from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"
import { BASEMAP_PRESETS, DEFAULT_2D_BASEMAP_STYLE, DEFAULT_CAMERA_STATE } from "@/lib/explore/constants"
import { globeController } from "@/lib/explore/globe-controller"
import { globeState } from "@/lib/explore/globe-state"
import { performanceMonitor } from "@/lib/explore/performance"
import { GlobeCameraState, RendererAdapter } from "@/lib/explore/types"
import { aoiStateManager, AOIDrawMode } from "@/lib/explore/aoi-state"
import { globeCommandBus } from "@/lib/explore/globe-command-bus"
import { cameraSyncBus } from "@/lib/explore/camera-sync"
import { Check, X } from "lucide-react"

interface MapViewProps {
  viewId?: "view-a" | "view-b"
}

export default function MapView({ viewId = "view-a" }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapLibreMap | null>(null)

  // Drawing state
  const [currentDrawMode, setCurrentDrawMode] = useState<AOIDrawMode>(null)
  const [polygonPointCount, setPolygonPointCount] = useState<number>(0)
  const currentDrawModeRef = useRef<AOIDrawMode>(null)
  const drawStartRef = useRef<[number, number] | null>(null)
  const downPixelRef = useRef<{ x: number; y: number } | null>(null)
  const isDraggingBoxRef = useRef<boolean>(false)
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

        // Setup draw preview source and layers
        if (!map.getSource("explore-aoi-draw-preview")) {
          map.addSource("explore-aoi-draw-preview", {
            type: "geojson",
            data: { type: "FeatureCollection", features: [] },
          })

          map.addLayer({
            id: "explore-aoi-draw-preview-fill",
            type: "fill",
            source: "explore-aoi-draw-preview",
            paint: {
              "fill-color": "#06b6d4",
              "fill-opacity": 0.22,
            },
          })

          map.addLayer({
            id: "explore-aoi-draw-preview-line",
            type: "line",
            source: "explore-aoi-draw-preview",
            paint: {
              "line-color": "#22d3ee",
              "line-width": 2.5,
              "line-dasharray": [2, 1],
            },
          })
        }

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

      // -------------------------------------------------------------
      // Interactive AOI Drawing Handlers (Box & Polygon)
      // -------------------------------------------------------------
      map.on("mousedown", (e) => {
        const mode = currentDrawModeRef.current
        if (mode === "rectangle") {
          drawStartRef.current = [e.lngLat.lng, e.lngLat.lat]
          downPixelRef.current = { x: e.point.x, y: e.point.y }
          isDraggingBoxRef.current = false
        }
      })

      map.on("mousemove", (e) => {
        const mode = currentDrawModeRef.current
        const lngLat: [number, number] = [e.lngLat.lng, e.lngLat.lat]

        // Rectangle dragging preview
        if (mode === "rectangle" && drawStartRef.current) {
          if (downPixelRef.current) {
            const dx = Math.abs(e.point.x - downPixelRef.current.x)
            const dy = Math.abs(e.point.y - downPixelRef.current.y)
            if (dx > 4 || dy > 4) {
              isDraggingBoxRef.current = true
            }
          }

          const [x1, y1] = drawStartRef.current
          const [x2, y2] = lngLat
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
          updateDrawPreview(map, previewBox)
        }

        // Polygon rubber-band line preview
        if (mode === "polygon" && polygonPointsRef.current.length > 0) {
          const pts = [...polygonPointsRef.current, lngLat]
          if (pts.length === 2) {
            updateDrawPreview(map, { type: "LineString", coordinates: pts })
          } else {
            const closedPreview = [...pts, pts[0]]
            updateDrawPreview(map, { type: "Polygon", coordinates: [closedPreview] })
          }
        }
      })

      map.on("mouseup", (e) => {
        const mode = currentDrawModeRef.current
        if (mode === "rectangle" && drawStartRef.current && isDraggingBoxRef.current) {
          const start = drawStartRef.current
          const end: [number, number] = [e.lngLat.lng, e.lngLat.lat]
          drawStartRef.current = null
          downPixelRef.current = null
          isDraggingBoxRef.current = false

          const minX = Math.min(start[0], end[0])
          const maxX = Math.max(start[0], end[0])
          const minY = Math.min(start[1], end[1])
          const maxY = Math.max(start[1], end[1])

          if (Math.abs(maxX - minX) > 0.0001 && Math.abs(maxY - minY) > 0.0001) {
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
            updateDrawPreview(map, null)
            aoiStateManager.setAOI(boxGeoJSON)
          }
        }
      })

      map.on("click", (e) => {
        const mode = currentDrawModeRef.current
        if (!mode) return

        const lngLat: [number, number] = [e.lngLat.lng, e.lngLat.lat]

        // Rectangle 2-Click Mode
        if (mode === "rectangle") {
          if (isDraggingBoxRef.current) {
            // Already handled in mouseup
            return
          }
          if (!drawStartRef.current) {
            drawStartRef.current = lngLat
          } else {
            const [x1, y1] = drawStartRef.current
            const [x2, y2] = lngLat
            const minX = Math.min(x1, x2)
            const maxX = Math.max(x1, x2)
            const minY = Math.min(y1, y2)
            const maxY = Math.max(y1, y2)

            if (Math.abs(maxX - minX) > 0.0001 && Math.abs(maxY - minY) > 0.0001) {
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
              updateDrawPreview(map, null)
              aoiStateManager.setAOI(boxGeoJSON)
            }
          }
        } else if (mode === "polygon") {
          // Polygon Vertex Click
          const pts = polygonPointsRef.current
          if (pts.length > 0) {
            const last = pts[pts.length - 1]
            if (Math.hypot(last[0] - lngLat[0], last[1] - lngLat[1]) < 1e-6) {
              return
            }
          }

          polygonPointsRef.current.push(lngLat)
          setPolygonPointCount(polygonPointsRef.current.length)

          if (polygonPointsRef.current.length === 1) {
            updateDrawPreview(map, { type: "Point", coordinates: lngLat })
          } else if (polygonPointsRef.current.length === 2) {
            updateDrawPreview(map, { type: "LineString", coordinates: polygonPointsRef.current })
          } else {
            const closed = [...polygonPointsRef.current, polygonPointsRef.current[0]]
            updateDrawPreview(map, { type: "Polygon", coordinates: [closed] })
          }
        }
      })

      map.on("dblclick", (e) => {
        const mode = currentDrawModeRef.current
        if (mode === "polygon") {
          e.preventDefault()
          const rawPts = polygonPointsRef.current
          const deduped = rawPts.filter(
            (p, i, a) => i === 0 || Math.hypot(p[0] - a[i - 1][0], p[1] - a[i - 1][1]) > 1e-6
          )
          if (deduped.length >= 3) {
            const closedRing = [...deduped, deduped[0]]
            const polyGeoJSON = {
              type: "Polygon",
              coordinates: [closedRing],
            }
            polygonPointsRef.current = []
            setPolygonPointCount(0)
            updateDrawPreview(map, null)
            aoiStateManager.setAOI(polyGeoJSON)
          }
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
          if (
            (layerId === "layer-base-satellite" || layerId === "layer-base-dark") &&
            mapRef.current.getLayer("esri-satellite-layer")
          ) {
            mapRef.current.setLayoutProperty("esri-satellite-layer", "visibility", visible ? "visible" : "none")
            return
          }
          if (mapRef.current.getLayer(layerId)) {
            mapRef.current.setLayoutProperty(layerId, "visibility", visible ? "visible" : "none")
          }
        },
        setLayerOpacity: (layerId, opacity) => {
          if (!mapRef.current) return
          if (
            (layerId === "layer-base-satellite" || layerId === "layer-base-dark") &&
            mapRef.current.getLayer("esri-satellite-layer")
          ) {
            mapRef.current.setPaintProperty("esri-satellite-layer", "raster-opacity", opacity)
            return
          }
          if (mapRef.current.getLayer(layerId)) {
            mapRef.current.setPaintProperty(layerId, "raster-opacity", opacity)
          }
        },
        setBasemap: (basemapId: string, tileUrl?: string) => {
          if (!mapRef.current) return
          const m = mapRef.current
          const preset = BASEMAP_PRESETS[basemapId]
          const resolvedUrl = tileUrl || preset?.tileUrl || BASEMAP_PRESETS.satellite.tileUrl
          const layerId = "esri-satellite-layer"
          const sourceId = "esri-satellite"

          try {
            if (m.getLayer(layerId)) m.removeLayer(layerId)
            if (m.getSource(sourceId)) m.removeSource(sourceId)

            m.addSource(sourceId, {
              type: "raster",
              tiles: [resolvedUrl],
              tileSize: 256,
              attribution: preset?.attribution || "TRINETRA Earth Observation",
            })

            const firstLayerId = m.getStyle().layers?.[0]?.id
            m.addLayer(
              {
                id: layerId,
                type: "raster",
                source: sourceId,
                minzoom: 0,
                maxzoom: 20,
              },
              firstLayerId
            )
          } catch (err) {
            console.warn("[MapView] Failed to switch basemap:", err)
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
        } else if (cmd.type === "SET_BASEMAP") {
          adapter.setBasemap?.(cmd.basemapId, cmd.tileUrl)
        } else if (cmd.type === "SHOW_LAYER") {
          adapter.setLayerVisibility?.(cmd.layerId, true)
        } else if (cmd.type === "HIDE_LAYER") {
          adapter.setLayerVisibility?.(cmd.layerId, false)
        } else if (cmd.type === "SET_LAYER_OPACITY") {
          adapter.setLayerOpacity?.(cmd.layerId, cmd.opacity)
        } else if (cmd.type === "ADD_LAYER") {
          adapter.addLayerSource?.(cmd.layer)
        } else if (cmd.type === "REMOVE_LAYER") {
          adapter.removeLayerSource?.(cmd.layerId)
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

      // Listen to AOIStateManager
      const unsubAOI = aoiStateManager.subscribe((state) => {
        currentDrawModeRef.current = state.drawMode
        setCurrentDrawMode(state.drawMode)
        if (!mapRef.current) return
        const m = mapRef.current

        if (state.drawMode) {
          m.dragPan.disable()
          m.doubleClickZoom.disable()
          m.getCanvas().style.cursor = "crosshair"
        } else {
          m.dragPan.enable()
          m.doubleClickZoom.enable()
          m.getCanvas().style.cursor = ""
          drawStartRef.current = null
          downPixelRef.current = null
          isDraggingBoxRef.current = false
          polygonPointsRef.current = []
          setPolygonPointCount(0)
          updateDrawPreview(m, null)
        }

        if (state.activeAOI) {
          updateAOILayers(m, state.activeAOI)
        }
      })

      return () => {
        unsubBus()
        unsubSync()
        unsubAOI()
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

  // Finish Polygon Ring Manual Trigger
  const handleFinishPolygon = () => {
    const rawPts = polygonPointsRef.current
    const deduped = rawPts.filter(
      (p, i, a) => i === 0 || Math.hypot(p[0] - a[i - 1][0], p[1] - a[i - 1][1]) > 1e-6
    )
    if (deduped.length >= 3) {
      const closedRing = [...deduped, deduped[0]]
      const polyGeoJSON = {
        type: "Polygon",
        coordinates: [closedRing],
      }
      polygonPointsRef.current = []
      setPolygonPointCount(0)
      if (mapRef.current) updateDrawPreview(mapRef.current, null)
      aoiStateManager.setAOI(polyGeoJSON)
    }
  }

  // Cancel Drawing Trigger
  const handleCancelDrawing = () => {
    aoiStateManager.setDrawMode(null)
  }

  return (
    <div className="relative w-full h-full overflow-hidden">
      <div className="map-container" ref={containerRef} style={{ width: "100%", height: "100%" }} />

      {/* Floating Interactive 2D Drawing Guide & Action Bar */}
      {currentDrawMode && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-[#0a0e18]/85 border border-cyan-500/40 rounded-2xl px-4 py-2 flex items-center gap-3 shadow-2xl shadow-cyan-950/50 z-30 backdrop-blur-2xl animate-in fade-in slide-in-from-top-2">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping shrink-0" />
          <div className="text-xs text-slate-100 font-medium tracking-wide">
            {currentDrawMode === "rectangle" ? (
              <span>Drag to draw box, or click two opposite corners</span>
            ) : (
              <span>
                Click to place polygon vertices ({polygonPointCount} added) · Double-click to close
              </span>
            )}
          </div>

          <div className="flex items-center gap-1.5 ml-2 border-l border-white/10 pl-3">
            {currentDrawMode === "polygon" && polygonPointCount >= 3 && (
              <button
                type="button"
                onClick={handleFinishPolygon}
                className="px-2.5 py-1 bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-lg text-xs font-bold transition-all shadow-sm flex items-center gap-1 cursor-pointer"
              >
                <Check className="w-3.5 h-3.5 stroke-[3]" />
                <span>Finish Ring</span>
              </button>
            )}

            <button
              type="button"
              onClick={handleCancelDrawing}
              className="px-2 py-1 bg-white/[0.05] hover:bg-white/[0.1] text-slate-300 hover:text-white rounded-lg text-xs font-medium border border-white/[0.08] transition-all flex items-center gap-1 cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
              <span>Cancel</span>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function updateDrawPreview(map: MapLibreMap, geometry: any | null) {
  if (!map || !map.isStyleLoaded()) return
  const src = map.getSource("explore-aoi-draw-preview") as maplibregl.GeoJSONSource
  if (!src) return

  if (!geometry) {
    src.setData({ type: "FeatureCollection", features: [] })
    return
  }

  const features: any[] = []
  if (geometry.type === "Polygon") {
    features.push({
      type: "Feature",
      geometry,
      properties: {},
    })
  } else if (geometry.type === "LineString") {
    features.push({
      type: "Feature",
      geometry,
      properties: {},
    })
  } else if (geometry.type === "Point") {
    features.push({
      type: "Feature",
      geometry,
      properties: {},
    })
  }

  src.setData({
    type: "FeatureCollection",
    features,
  })
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
