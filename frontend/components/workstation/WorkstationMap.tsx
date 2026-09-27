"use client"

/**
 * TRINETRA Workstation — Interactive Map Canvas
 * Persistent MapLibre GL 2D / Cesium 3D Globe with active AOI vector rendering,
 * interactive drawing tools, dynamic raster layer synchronization, customizable base maps,
 * reference overlays, and unified multi-tile mosaic raster rendering.
 */

import React, { useEffect, useRef, useState } from "react"
import maplibregl, { Map as MapLibreMap } from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"
import { AreaOfInterest } from "@/lib/workstation/types"
import { LayerState, BaseMapId, BASE_MAP_OPTIONS } from "./WorkstationDataRail"
import { Plus, Minus, Compass, Maximize2, Crosshair, Layers, Check, Grid } from "lucide-react"

interface Props {
  aois?: AreaOfInterest[]
  activeAOI: AreaOfInterest | null
  hiddenAoiIds?: Set<string>
  onSelectAOI?: (aoi: AreaOfInterest) => void
  layers: LayerState[]
  viewMode: "2d" | "3d"
  drawingMode: "box" | "polygon" | null
  onFinishDrawingAOI: (geometry: any, keepDrawing?: boolean) => void
  onCancelDrawing: () => void
  fitBoundsBbox?: [number, number, number, number] | null
  baseMap?: BaseMapId
  onSelectBaseMap?: (id: BaseMapId) => void
  showLabels?: boolean
  onToggleLabels?: (show: boolean) => void
  labelsOpacity?: number
  onChangeLabelsOpacity?: (val: number) => void
  showGraticule?: boolean
  onToggleGraticule?: (show: boolean) => void
}

export const WorkstationMap: React.FC<Props> = ({
  aois = [],
  activeAOI,
  hiddenAoiIds = new Set(),
  onSelectAOI,
  layers,
  viewMode,
  drawingMode,
  onFinishDrawingAOI,
  onCancelDrawing,
  fitBoundsBbox,
  baseMap = "esri-satellite",
  onSelectBaseMap,
  showLabels = true,
  onToggleLabels,
  labelsOpacity = 0.85,
  onChangeLabelsOpacity,
  showGraticule = false,
  onToggleGraticule,
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const [telemetry, setTelemetry] = useState({
    lat: 23.08,
    lon: 77.67,
    zoom: 8.5,
  })

  // Quick Basemap Selector Floating Dropdown
  const [showBasemapDropdown, setShowBasemapDropdown] = useState(false)
  const [keepDrawingConsecutive, setKeepDrawingConsecutive] = useState(false)
  const [polygonPointCount, setPolygonPointCount] = useState(0)

  const drawStartRef = useRef<[number, number] | null>(null)
  const polygonPointsRef = useRef<[number, number][]>([])
  const downPixelRef = useRef<{ x: number; y: number } | null>(null)
  const isDraggingBoxRef = useRef<boolean>(false)

  const aoisRef = useRef(aois)
  aoisRef.current = aois
  const onSelectAOIRef = useRef(onSelectAOI)
  onSelectAOIRef.current = onSelectAOI
  const drawingModeRef = useRef(drawingMode)
  drawingModeRef.current = drawingMode
  const onFinishDrawingAOIRef = useRef(onFinishDrawingAOI)
  onFinishDrawingAOIRef.current = onFinishDrawingAOI
  const keepDrawingConsecutiveRef = useRef(keepDrawingConsecutive)
  keepDrawingConsecutiveRef.current = keepDrawingConsecutive

  // Track mounted raster & vector layer and source IDs for seamless deloading/cleanup
  const mountedLayerIdsRef = useRef<Set<string>>(new Set())
  const mountedSourceIdsRef = useRef<Set<string>>(new Set())

  useEffect(() => {
    if (!containerRef.current) return

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {
          "esri-satellite": {
            type: "raster",
            tiles: [
              "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            ],
            tileSize: 256,
            attribution: "Esri, Maxar",
          },
          "carto-dark": {
            type: "raster",
            tiles: [
              "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
            ],
            tileSize: 256,
            attribution: "© CartoDB, © OpenStreetMap",
          },
          "carto-positron": {
            type: "raster",
            tiles: [
              "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
            ],
            tileSize: 256,
            attribution: "© CartoDB, © OpenStreetMap",
          },
          "osm-standard": {
            type: "raster",
            tiles: [
              "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            ],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors",
          },
          "esri-topo": {
            type: "raster",
            tiles: [
              "https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
            ],
            tileSize: 256,
            attribution: "Esri Topographic",
          },
          "esri-boundaries-labels": {
            type: "raster",
            tiles: [
              "https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
            ],
            tileSize: 256,
            attribution: "Esri Places & Boundaries",
          },
        },
        layers: [
          // 0. Blank canvas deep dark background
          {
            id: "base-canvas-bg",
            type: "background",
            paint: {
              "background-color": "#030712",
            },
          },
          // 1. Esri Satellite Base
          {
            id: "base-layer-esri-satellite",
            type: "raster",
            source: "esri-satellite",
            layout: { visibility: baseMap === "esri-satellite" ? "visible" : "none" },
            minzoom: 0,
            maxzoom: 19,
          },
          // 2. Carto Dark Matter Base
          {
            id: "base-layer-carto-dark",
            type: "raster",
            source: "carto-dark",
            layout: { visibility: baseMap === "carto-dark" ? "visible" : "none" },
            minzoom: 0,
            maxzoom: 19,
          },
          // 3. Carto Positron Base
          {
            id: "base-layer-carto-positron",
            type: "raster",
            source: "carto-positron",
            layout: { visibility: baseMap === "carto-positron" ? "visible" : "none" },
            minzoom: 0,
            maxzoom: 19,
          },
          // 4. OSM Standard Base
          {
            id: "base-layer-osm-standard",
            type: "raster",
            source: "osm-standard",
            layout: { visibility: baseMap === "osm-standard" ? "visible" : "none" },
            minzoom: 0,
            maxzoom: 19,
          },
          // 5. Esri Topographic Base
          {
            id: "base-layer-esri-topo",
            type: "raster",
            source: "esri-topo",
            layout: { visibility: baseMap === "esri-topo" ? "visible" : "none" },
            minzoom: 0,
            maxzoom: 19,
          },
          // 6. World Boundaries & Places Overlay
          {
            id: "labels-overlay",
            type: "raster",
            source: "esri-boundaries-labels",
            layout: { visibility: showLabels ? "visible" : "none" },
            paint: { "raster-opacity": labelsOpacity },
            minzoom: 0,
            maxzoom: 19,
          },
        ],
      },
      center: [77.67, 23.08],
      zoom: 8.5,
      attributionControl: false,
    })

    mapRef.current = map

    map.on("load", () => {
      // Add AOI source & layers
      map.addSource("workstation-aoi-src", {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: [],
        },
      })

      map.addLayer({
        id: "workstation-aoi-fill",
        type: "fill",
        source: "workstation-aoi-src",
        paint: {
          "fill-color": [
            "case",
            ["==", ["get", "isActive"], true],
            "#06b6d4",
            "#0284c7",
          ],
          "fill-opacity": [
            "case",
            ["==", ["get", "isActive"], true],
            0.25,
            0.12,
          ],
        },
      })

      map.addLayer({
        id: "workstation-aoi-line",
        type: "line",
        source: "workstation-aoi-src",
        paint: {
          "line-color": [
            "case",
            ["==", ["get", "isActive"], true],
            "#22d3ee",
            "#38bdf8",
          ],
          "line-width": [
            "case",
            ["==", ["get", "isActive"], true],
            2.5,
            1.5,
          ],
        },
      })

      // Click to select AOI on map
      map.on("click", "workstation-aoi-fill", (e) => {
        if (drawingModeRef.current) return
        const clickedId = e.features?.[0]?.properties?.id
        if (clickedId && onSelectAOIRef.current) {
          const found = aoisRef.current.find((a) => a.id === clickedId)
          if (found) {
            onSelectAOIRef.current(found)
          }
        }
      })

      // Add Drawing Preview Source & Layers
      map.addSource("draw-preview-src", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      })

      map.addLayer({
        id: "draw-preview-fill",
        type: "fill",
        source: "draw-preview-src",
        paint: {
          "fill-color": "#10b981",
          "fill-opacity": 0.25,
        },
      })

      map.addLayer({
        id: "draw-preview-line",
        type: "line",
        source: "draw-preview-src",
        paint: {
          "line-color": "#34d399",
          "line-width": 2,
        },
      })

      // Graticule Grid Lines Source & Layer
      const graticuleFeatures = generateGraticuleGeoJSON()
      map.addSource("graticule-src", {
        type: "geojson",
        data: graticuleFeatures,
      })
      map.addLayer({
        id: "graticule-line",
        type: "line",
        source: "graticule-src",
        layout: { visibility: showGraticule ? "visible" : "none" },
        paint: {
          "line-color": "#38bdf8",
          "line-opacity": 0.25,
          "line-width": 0.75,
          "line-dasharray": [4, 4],
        },
      })

      if (aois.length > 0 || activeAOI) {
        updateAOIGeometry(map, aois, activeAOI, hiddenAoiIds)
      }
    })

    map.on("move", () => {
      const center = map.getCenter()
      setTelemetry({
        lat: parseFloat(center.lat.toFixed(4)),
        lon: parseFloat(center.lng.toFixed(4)),
        zoom: parseFloat(map.getZoom().toFixed(1)),
      })
    })

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Sync Base Map changes seamlessly without restarting MapLibre
  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.isStyleLoaded()) return

    const baseMapLayerMap: Record<BaseMapId, string> = {
      "esri-satellite": "base-layer-esri-satellite",
      "carto-dark": "base-layer-carto-dark",
      "carto-positron": "base-layer-carto-positron",
      "osm-standard": "base-layer-osm-standard",
      "esri-topo": "base-layer-esri-topo",
      "blank-canvas": "",
    }

    Object.entries(baseMapLayerMap).forEach(([id, layerId]) => {
      if (layerId && map.getLayer(layerId)) {
        map.setLayoutProperty(layerId, "visibility", id === baseMap ? "visible" : "none")
      }
    })
  }, [baseMap])

  // Sync Labels & Graticule Overlay Visibility and Opacity
  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.isStyleLoaded()) return

    if (map.getLayer("labels-overlay")) {
      map.setLayoutProperty("labels-overlay", "visibility", showLabels ? "visible" : "none")
      map.setPaintProperty("labels-overlay", "raster-opacity", labelsOpacity)
    }

    if (map.getLayer("graticule-line")) {
      map.setLayoutProperty("graticule-line", "visibility", showGraticule ? "visible" : "none")
    }
  }, [showLabels, labelsOpacity, showGraticule])

  // Sync Layers (User-Uploaded GeoTIFFs, Mosaics, and Analysis Outputs) with FULL Deloading/Cleanup
  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.isStyleLoaded()) return

    // 1. Compute sets of currently desired MapLibre layer and source IDs
    const currentLayerIds = new Set<string>()
    const currentSourceIds = new Set<string>()

    layers.forEach((layer) => {
      if (layer.isMosaic && layer.tiles && layer.tiles.length > 0) {
        if (layer.bbox) {
          currentSourceIds.add(`src_mosaic_poly_${layer.id}`)
          currentLayerIds.add(`line_mosaic_${layer.id}`)
        }
        layer.tiles.forEach((tile) => {
          if (tile.sourceUrl && tile.coordinates && tile.coordinates.length === 4) {
            currentSourceIds.add(`src_tile_${tile.id}`)
            currentLayerIds.add(`img_tile_${tile.id}`)
          }
        })
      } else {
        const imgCoordinates =
          layer.coordinates ||
          (layer.bbox && layer.bbox.length === 4
            ? [
                [layer.bbox[0], layer.bbox[3]],
                [layer.bbox[2], layer.bbox[3]],
                [layer.bbox[2], layer.bbox[1]],
                [layer.bbox[0], layer.bbox[1]],
              ]
            : null)

        if (layer.sourceUrl && imgCoordinates && imgCoordinates.length === 4) {
          currentSourceIds.add(`src_${layer.id}`)
          currentLayerIds.add(`img_${layer.id}`)
        }

        if (layer.geometry) {
          currentSourceIds.add(`fpsrc_${layer.id}`)
          currentLayerIds.add(`fpline_${layer.id}`)
        }
      }
    })

    // 2. DELOAD / CLEANUP: Remove any layers that are no longer loaded or active
    mountedLayerIdsRef.current.forEach((layerId) => {
      if (!currentLayerIds.has(layerId)) {
        try {
          if (map.getLayer(layerId)) {
            map.removeLayer(layerId)
          }
        } catch (e) {
          console.warn("Deloading layer error:", layerId, e)
        }
        mountedLayerIdsRef.current.delete(layerId)
      }
    })

    // Remove any sources that are no longer loaded (MapLibre requires removing layers before sources)
    mountedSourceIdsRef.current.forEach((sourceId) => {
      if (!currentSourceIds.has(sourceId)) {
        try {
          if (map.getSource(sourceId)) {
            map.removeSource(sourceId)
          }
        } catch (e) {
          console.warn("Deloading source error:", sourceId, e)
        }
        mountedSourceIdsRef.current.delete(sourceId)
      }
    })

    // 3. SYNCHRONIZE & ATTACH ACTIVE LAYERS
    layers.forEach((layer) => {
      // 1. Unified Dataset Mosaic (e.g. multi-file or folder uploads)
      if (layer.isMosaic && layer.tiles && layer.tiles.length > 0) {
        // Add or update bounding polygon outline for entire mosaic
        if (layer.bbox) {
          const polySrcId = `src_mosaic_poly_${layer.id}`
          const polyLineId = `line_mosaic_${layer.id}`
          const [minX, minY, maxX, maxY] = layer.bbox
          const geojson = {
            type: "Feature",
            geometry: {
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
            },
          }
          if (!map.getSource(polySrcId)) {
            try {
              map.addSource(polySrcId, { type: "geojson", data: geojson as any })
              map.addLayer({
                id: polyLineId,
                type: "line",
                source: polySrcId,
                paint: {
                  "line-color": layer.modalityColor || "#06b6d4",
                  "line-width": 1.5,
                  "line-dasharray": [3, 2],
                },
              })
              mountedSourceIdsRef.current.add(polySrcId)
              mountedLayerIdsRef.current.add(polyLineId)
            } catch (e) {
              // Ignore if exists
            }
          } else if (map.getLayer(polyLineId)) {
            map.setLayoutProperty(polyLineId, "visibility", layer.visible ? "visible" : "none")
            mountedSourceIdsRef.current.add(polySrcId)
            mountedLayerIdsRef.current.add(polyLineId)
          }
        }

        // Add or sync each tile in the mosaic with the unified layer opacity
        layer.tiles.forEach((tile) => {
          if (!tile.sourceUrl || !tile.coordinates || tile.coordinates.length !== 4) return
          const tileSrcId = `src_tile_${tile.id}`
          const tileLyrId = `img_tile_${tile.id}`

          if (!map.getSource(tileSrcId)) {
            try {
              map.addSource(tileSrcId, {
                type: "image",
                url: tile.sourceUrl,
                coordinates: tile.coordinates as any,
              })
              const beforeLayer = map.getLayer("labels-overlay") ? "labels-overlay" : undefined
              map.addLayer(
                {
                  id: tileLyrId,
                  type: "raster",
                  source: tileSrcId,
                  layout: { visibility: layer.visible ? "visible" : "none" },
                  paint: {
                    "raster-opacity": layer.opacity,
                    "raster-resampling": "linear",
                  },
                },
                beforeLayer
              )
              mountedSourceIdsRef.current.add(tileSrcId)
              mountedLayerIdsRef.current.add(tileLyrId)
            } catch (e) {
              // Ignore concurrency
            }
          } else if (map.getLayer(tileLyrId)) {
            map.setLayoutProperty(tileLyrId, "visibility", layer.visible ? "visible" : "none")
            map.setPaintProperty(tileLyrId, "raster-opacity", layer.opacity)
            mountedSourceIdsRef.current.add(tileSrcId)
            mountedLayerIdsRef.current.add(tileLyrId)
          }
        })
        return
      }

      // 2. Individual Single-Scene GeoTIFF Image Layer or Analysis Output
      const imgCoordinates =
        layer.coordinates ||
        (layer.bbox && layer.bbox.length === 4
          ? [
              [layer.bbox[0], layer.bbox[3]], // Top-Left [lon, lat]
              [layer.bbox[2], layer.bbox[3]], // Top-Right [lon, lat]
              [layer.bbox[2], layer.bbox[1]], // Bottom-Right [lon, lat]
              [layer.bbox[0], layer.bbox[1]], // Bottom-Left [lon, lat]
            ]
          : null)

      if (layer.sourceUrl && imgCoordinates && imgCoordinates.length === 4) {
        const sourceId = `src_${layer.id}`
        const layerId = `img_${layer.id}`

        if (!map.getSource(sourceId)) {
          try {
            map.addSource(sourceId, {
              type: "image",
              url: layer.sourceUrl,
              coordinates: imgCoordinates as any,
            })
            const beforeLayer = map.getLayer("labels-overlay") ? "labels-overlay" : undefined
            map.addLayer(
              {
                id: layerId,
                type: "raster",
                source: sourceId,
                layout: { visibility: layer.visible ? "visible" : "none" },
                paint: {
                  "raster-opacity": layer.opacity,
                  "raster-resampling": "linear",
                },
              },
              beforeLayer
            )
            mountedSourceIdsRef.current.add(sourceId)
            mountedLayerIdsRef.current.add(layerId)
          } catch (e) {
            console.error("Error attaching raster image layer to map:", layer.id, e)
          }
        } else if (map.getLayer(layerId)) {
          map.setLayoutProperty(layerId, "visibility", layer.visible ? "visible" : "none")
          map.setPaintProperty(layerId, "raster-opacity", layer.opacity)
          mountedSourceIdsRef.current.add(sourceId)
          mountedLayerIdsRef.current.add(layerId)
        }
      }

      // 3. Dynamic Vector Footprint Perimeter
      if (layer.geometry) {
        const fpSrc = `fpsrc_${layer.id}`
        const fpLine = `fpline_${layer.id}`

        if (!map.getSource(fpSrc)) {
          try {
            map.addSource(fpSrc, {
              type: "geojson",
              data: {
                type: "Feature",
                geometry: layer.geometry,
                properties: { name: layer.name },
              },
            })
            map.addLayer({
              id: fpLine,
              type: "line",
              source: fpSrc,
              paint: {
                "line-color": layer.modalityColor || "#22d3ee",
                "line-width": 1.5,
                "line-dasharray": [3, 2],
              },
            })
            mountedSourceIdsRef.current.add(fpSrc)
            mountedLayerIdsRef.current.add(fpLine)
          } catch (e) {
            console.error("Error adding footprint polygon:", layer.id, e)
          }
        } else if (map.getLayer(fpLine)) {
          map.setLayoutProperty(fpLine, "visibility", layer.visible ? "visible" : "none")
          mountedSourceIdsRef.current.add(fpSrc)
          mountedLayerIdsRef.current.add(fpLine)
        }
      }
    })
  }, [layers])


  // Fly to explicit bounding box
  useEffect(() => {
    const map = mapRef.current
    if (!map || !fitBoundsBbox || fitBoundsBbox.length !== 4) return
    map.fitBounds(
      [
        [fitBoundsBbox[0], fitBoundsBbox[1]],
        [fitBoundsBbox[2], fitBoundsBbox[3]],
      ],
      { padding: 80, duration: 1200 }
    )
  }, [fitBoundsBbox])

  // Update AOIs on map when aois, activeAOI, or hiddenAoiIds change
  useEffect(() => {
    if (!mapRef.current || !mapRef.current.isStyleLoaded()) return
    updateAOIGeometry(mapRef.current, aois, activeAOI, hiddenAoiIds)
  }, [aois, activeAOI, hiddenAoiIds])

  const updateAOIGeometry = (
    map: MapLibreMap,
    allAois: AreaOfInterest[] = [],
    selectedAOI: AreaOfInterest | null = null,
    hiddenIds: Set<string> = new Set()
  ) => {
    const src = map.getSource("workstation-aoi-src") as maplibregl.GeoJSONSource
    if (!src) return

    const sourceList = allAois.length > 0 ? allAois : (selectedAOI ? [selectedAOI] : [])
    const visibleList = sourceList.filter((a) => !hiddenIds.has(a.id) && a.geometry)

    if (visibleList.length === 0) {
      src.setData({ type: "FeatureCollection", features: [] })
      return
    }

    const features = visibleList.map((a) => ({
      type: "Feature",
      geometry: a.geometry,
      properties: {
        id: a.id,
        name: a.name,
        isActive: a.id === selectedAOI?.id,
      },
    }))

    src.setData({
      type: "FeatureCollection",
      features: features as any,
    })

    if (selectedAOI?.bbox && selectedAOI.bbox.length === 4) {
      map.fitBounds(
        [
          [selectedAOI.bbox[0], selectedAOI.bbox[1]],
          [selectedAOI.bbox[2], selectedAOI.bbox[3]],
        ],
        { padding: 80, duration: 1000 }
      )
    }
  }

  // Interactive AOI Drawing Handlers
  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    if (!drawingMode) {
      map.dragPan.enable()
      map.doubleClickZoom.enable()
      map.getCanvas().style.cursor = ""
      drawStartRef.current = null
      downPixelRef.current = null
      isDraggingBoxRef.current = false
      polygonPointsRef.current = []
      setPolygonPointCount(0)
      const src = map.getSource("draw-preview-src") as maplibregl.GeoJSONSource
      if (src) src.setData({ type: "FeatureCollection", features: [] })
      return
    }

    // Lock navigation gestures so drawing is precise and smooth
    map.dragPan.disable()
    map.doubleClickZoom.disable()
    map.getCanvas().style.cursor = "crosshair"

    const isBox = drawingMode === "box" || (drawingMode as string) === "rectangle"

    const onMouseDown = (e: maplibregl.MapMouseEvent) => {
      if (isBox) {
        drawStartRef.current = [e.lngLat.lng, e.lngLat.lat]
        downPixelRef.current = { x: e.point.x, y: e.point.y }
        isDraggingBoxRef.current = false
      }
    }

    const onMouseMove = (e: maplibregl.MapMouseEvent) => {
      const lngLat: [number, number] = [e.lngLat.lng, e.lngLat.lat]

      // Box drag preview
      if (isBox && drawStartRef.current) {
        if (downPixelRef.current) {
          const dx = Math.abs(e.point.x - downPixelRef.current.x)
          const dy = Math.abs(e.point.y - downPixelRef.current.y)
          if (dx > 4 || dy > 4) {
            isDraggingBoxRef.current = true
          }
        }

        const start = drawStartRef.current
        const curr = lngLat
        const ring = [
          start,
          [curr[0], start[1]],
          curr,
          [start[0], curr[1]],
          start,
        ]
        const src = map.getSource("draw-preview-src") as maplibregl.GeoJSONSource
        if (src) {
          src.setData({
            type: "Feature",
            geometry: { type: "Polygon", coordinates: [ring] },
            properties: {},
          })
        }
      }

      // Polygon rubber-band line preview
      if (drawingMode === "polygon" && polygonPointsRef.current.length > 0) {
        const pts = [...polygonPointsRef.current, lngLat]
        const src = map.getSource("draw-preview-src") as maplibregl.GeoJSONSource
        if (src) {
          if (pts.length === 2) {
            src.setData({
              type: "Feature",
              geometry: { type: "LineString", coordinates: pts },
              properties: {},
            })
          } else {
            const closed = [...pts, pts[0]]
            src.setData({
              type: "Feature",
              geometry: { type: "Polygon", coordinates: [closed] },
              properties: {},
            })
          }
        }
      }
    }

    const onMouseUp = (e: maplibregl.MapMouseEvent) => {
      if (isBox && drawStartRef.current && isDraggingBoxRef.current) {
        const start = drawStartRef.current
        const end: [number, number] = [e.lngLat.lng, e.lngLat.lat]
        drawStartRef.current = null
        downPixelRef.current = null
        isDraggingBoxRef.current = false

        const minLng = Math.min(start[0], end[0])
        const maxLng = Math.max(start[0], end[0])
        const minLat = Math.min(start[1], end[1])
        const maxLat = Math.max(start[1], end[1])

        if (Math.abs(maxLng - minLng) > 0.0001 && Math.abs(maxLat - minLat) > 0.0001) {
          const geometry = {
            type: "Polygon",
            coordinates: [
              [
                [minLng, minLat],
                [maxLng, minLat],
                [maxLng, maxLat],
                [minLng, maxLat],
                [minLng, minLat],
              ],
            ],
          }

          const previewSrc = map.getSource("draw-preview-src") as maplibregl.GeoJSONSource
          if (previewSrc) previewSrc.setData({ type: "FeatureCollection", features: [] })
          onFinishDrawingAOI(geometry, keepDrawingConsecutiveRef.current)
        }
      }
    }

    const onClick = (e: maplibregl.MapMouseEvent) => {
      const lngLat: [number, number] = [e.lngLat.lng, e.lngLat.lat]

      // Box 2-click fallback
      if (isBox) {
        if (isDraggingBoxRef.current) {
          return // Handled on mouseup
        }
        if (!drawStartRef.current) {
          drawStartRef.current = lngLat
        } else {
          const start = drawStartRef.current
          const end = lngLat
          drawStartRef.current = null

          const minLng = Math.min(start[0], end[0])
          const maxLng = Math.max(start[0], end[0])
          const minLat = Math.min(start[1], end[1])
          const maxLat = Math.max(start[1], end[1])

          if (Math.abs(maxLng - minLng) > 0.0001 && Math.abs(maxLat - minLat) > 0.0001) {
            const geometry = {
              type: "Polygon",
              coordinates: [
                [
                  [minLng, minLat],
                  [maxLng, minLat],
                  [maxLng, maxLat],
                  [minLng, maxLat],
                  [minLng, minLat],
                ],
              ],
            }
            const previewSrc = map.getSource("draw-preview-src") as maplibregl.GeoJSONSource
            if (previewSrc) previewSrc.setData({ type: "FeatureCollection", features: [] })
            onFinishDrawingAOI(geometry, keepDrawingConsecutiveRef.current)
          }
        }
      } else if (drawingMode === "polygon") {
        // Dedup if point clicked matches last point
        const pts = polygonPointsRef.current
        if (pts.length > 0) {
          const last = pts[pts.length - 1]
          if (Math.hypot(last[0] - lngLat[0], last[1] - lngLat[1]) < 1e-6) {
            return
          }
        }

        polygonPointsRef.current.push(lngLat)
        setPolygonPointCount(polygonPointsRef.current.length)
        updateDrawPreview()
      }
    }

    const onDblClick = (e: maplibregl.MapMouseEvent) => {
      if (drawingMode === "polygon") {
        e.preventDefault()
        const rawPts = polygonPointsRef.current
        const deduped = rawPts.filter(
          (p, i, a) => i === 0 || Math.hypot(p[0] - a[i - 1][0], p[1] - a[i - 1][1]) > 1e-6
        )
        if (deduped.length >= 3) {
          const closed = [...deduped, deduped[0]]
          const geometry = {
            type: "Polygon",
            coordinates: [closed],
          }
          polygonPointsRef.current = []
          setPolygonPointCount(0)
          const previewSrc = map.getSource("draw-preview-src") as maplibregl.GeoJSONSource
          if (previewSrc) previewSrc.setData({ type: "FeatureCollection", features: [] })
          onFinishDrawingAOI(geometry, keepDrawingConsecutiveRef.current)
        }
      }
    }

    const updateDrawPreview = () => {
      const pts = polygonPointsRef.current
      const src = map.getSource("draw-preview-src") as maplibregl.GeoJSONSource
      if (!src) return

      if (pts.length < 2) {
        src.setData({ type: "FeatureCollection", features: [] })
        return
      }

      if (pts.length === 2) {
        src.setData({
          type: "Feature",
          geometry: { type: "LineString", coordinates: pts },
          properties: {},
        })
      } else {
        const closed = [...pts, pts[0]]
        src.setData({
          type: "Feature",
          geometry: { type: "Polygon", coordinates: [closed] },
          properties: {},
        })
      }
    }

    map.on("mousedown", onMouseDown)
    map.on("mousemove", onMouseMove)
    map.on("mouseup", onMouseUp)
    map.on("click", onClick)
    map.on("dblclick", onDblClick)

    return () => {
      map.off("mousedown", onMouseDown)
      map.off("mousemove", onMouseMove)
      map.off("mouseup", onMouseUp)
      map.off("click", onClick)
      map.off("dblclick", onDblClick)
    }
  }, [drawingMode])

  const handleZoomIn = () => mapRef.current?.zoomIn({ duration: 300 })
  const handleZoomOut = () => mapRef.current?.zoomOut({ duration: 300 })
  const handleResetNorth = () => mapRef.current?.resetNorth({ duration: 300 })
  const handleRecenterAOI = () => {
    if (activeAOI && activeAOI.bbox && activeAOI.bbox.length === 4 && mapRef.current) {
      mapRef.current.fitBounds(
        [
          [activeAOI.bbox[0], activeAOI.bbox[1]],
          [activeAOI.bbox[2], activeAOI.bbox[3]],
        ],
        { padding: 80, duration: 1000 }
      )
    }
  }

  return (
    <div className="relative w-full h-full overflow-hidden bg-slate-950">
      <div ref={containerRef} className="w-full h-full" />

      {/* Drawing Instructions Banner (Glassmorphic) */}
      {drawingMode && (
        <div className="absolute top-5 left-1/2 -translate-x-1/2 bg-slate-950/85 border border-cyan-500/40 rounded-2xl px-5 py-2 flex items-center gap-3.5 shadow-2xl shadow-cyan-950/50 z-20 backdrop-blur-2xl">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
          <div className="text-xs text-slate-100 font-medium tracking-wide">
            {drawingMode === "box"
              ? "Click and drag to define boundary extent."
              : `Click points to draw polygon (${polygonPointCount} points). Double-click or click Finish.`}
          </div>

          {drawingMode === "polygon" && polygonPointCount >= 3 && (
            <button
              onClick={() => {
                if (polygonPointsRef.current.length >= 3) {
                  const pts = [...polygonPointsRef.current]
                  pts.push(pts[0])
                  const geometry = { type: "Polygon", coordinates: [pts] }
                  polygonPointsRef.current = []
                  setPolygonPointCount(0)
                  const previewSrc = mapRef.current?.getSource("draw-preview-src") as maplibregl.GeoJSONSource
                  if (previewSrc) previewSrc.setData({ type: "FeatureCollection", features: [] })
                  onFinishDrawingAOI(geometry, keepDrawingConsecutive)
                }
              }}
              className="px-2.5 py-0.5 rounded-full bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-[10px] shadow-sm transition-colors cursor-pointer"
            >
              Finish Ring
            </button>
          )}

          <label className="flex items-center gap-1.5 cursor-pointer text-slate-300 text-[10px] font-mono border-l border-white/10 pl-2">
            <input
              type="checkbox"
              checked={keepDrawingConsecutive}
              onChange={(e) => setKeepDrawingConsecutive(e.target.checked)}
              className="accent-cyan-400 rounded cursor-pointer"
            />
            <span>Add Multiple</span>
          </label>

          <button
            onClick={() => {
              polygonPointsRef.current = []
              setPolygonPointCount(0)
              onCancelDrawing()
            }}
            className="px-2.5 py-0.5 rounded-full bg-white/[0.08] hover:bg-white/[0.15] text-[10px] text-slate-300 font-mono tracking-wider transition-colors cursor-pointer border border-white/[0.1]"
          >
            Cancel
          </button>
        </div>
      )}

      {/* Floating Map Quick Controls (Glassmorphic Dock) */}
      <div className="absolute top-4 right-4 flex flex-col gap-1.5 z-10">
        <div className="bg-slate-950/70 border border-white/[0.08] rounded-xl p-1 shadow-2xl backdrop-blur-2xl flex flex-col gap-1">
          <button
            onClick={handleZoomIn}
            title="Zoom In"
            className="w-8 h-8 rounded-lg bg-white/[0.03] hover:bg-white/[0.08] border border-transparent hover:border-white/[0.08] flex items-center justify-center text-slate-300 hover:text-cyan-400 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomOut}
            title="Zoom Out"
            className="w-8 h-8 rounded-lg bg-white/[0.03] hover:bg-white/[0.08] border border-transparent hover:border-white/[0.08] flex items-center justify-center text-slate-300 hover:text-cyan-400 transition-all cursor-pointer"
          >
            <Minus className="w-4 h-4" />
          </button>
          <button
            onClick={handleResetNorth}
            title="Reset North"
            className="w-8 h-8 rounded-lg bg-white/[0.03] hover:bg-white/[0.08] border border-transparent hover:border-white/[0.08] flex items-center justify-center text-slate-300 hover:text-cyan-400 transition-all cursor-pointer"
          >
            <Compass className="w-4 h-4" />
          </button>
          {activeAOI && (
            <button
              onClick={handleRecenterAOI}
              title="Fit to Active AOI"
              className="w-8 h-8 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400 transition-all cursor-pointer"
            >
              <Crosshair className="w-4 h-4" />
            </button>
          )}

          {/* Quick Basemap Floating Selector */}
          <div className="relative">
            <button
              onClick={() => setShowBasemapDropdown(!showBasemapDropdown)}
              title="Change Base Map & Overlays"
              className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all cursor-pointer border ${
                showBasemapDropdown
                  ? "bg-cyan-500/20 text-cyan-300 border-cyan-400"
                  : "bg-white/[0.03] hover:bg-white/[0.08] text-slate-300 hover:text-cyan-400 border-transparent hover:border-white/[0.08]"
              }`}
            >
              <Layers className="w-4 h-4" />
            </button>

            {showBasemapDropdown && (
              <div className="absolute right-10 top-0 w-64 bg-slate-950/95 border border-white/[0.12] rounded-xl p-3 shadow-2xl backdrop-blur-2xl z-30 space-y-2.5">
                <div className="text-[10px] font-mono uppercase text-slate-400 flex items-center justify-between border-b border-white/[0.06] pb-1.5">
                  <span>Base Map Canvas</span>
                  <span className="text-cyan-400 lowercase">{baseMap}</span>
                </div>

                <div className="grid grid-cols-2 gap-1.5">
                  {BASE_MAP_OPTIONS.map((opt) => (
                    <button
                      key={opt.id}
                      onClick={() => {
                        onSelectBaseMap?.(opt.id)
                        setShowBasemapDropdown(false)
                      }}
                      className={`text-left p-1.5 rounded-lg border text-[11px] font-medium transition-all cursor-pointer ${
                        baseMap === opt.id
                          ? "bg-cyan-500/20 border-cyan-400 text-cyan-300"
                          : "bg-white/[0.02] border-white/[0.06] hover:bg-white/[0.06] text-slate-300"
                      }`}
                    >
                      <div className="truncate">{opt.label}</div>
                      <div className="text-[8px] text-slate-400 truncate">{opt.tag}</div>
                    </button>
                  ))}
                </div>

                <div className="pt-2 border-t border-white/[0.06] space-y-1.5 text-xs text-slate-200">
                  <label className="flex items-center justify-between cursor-pointer">
                    <span className="text-[10px]">Boundaries & Labels</span>
                    <input
                      type="checkbox"
                      checked={showLabels}
                      onChange={(e) => onToggleLabels?.(e.target.checked)}
                      className="accent-cyan-400 rounded cursor-pointer"
                    />
                  </label>
                  <label className="flex items-center justify-between cursor-pointer">
                    <span className="text-[10px]">Coordinate Graticule</span>
                    <input
                      type="checkbox"
                      checked={showGraticule}
                      onChange={(e) => onToggleGraticule?.(e.target.checked)}
                      className="accent-cyan-400 rounded cursor-pointer"
                    />
                  </label>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Telemetry HUD (Bottom Right — Minimalist Glassmorphic Pill) */}
      <div className="absolute bottom-3 right-3 bg-slate-950/70 border border-white/[0.08] rounded-full px-4 py-1.5 flex items-center gap-4 text-[10px] font-mono text-slate-400 z-10 backdrop-blur-2xl shadow-xl pointer-events-none">
        <div>
          LAT <span className="text-cyan-300 font-semibold">{telemetry.lat}° N</span>
        </div>
        <div>
          LON <span className="text-cyan-300 font-semibold">{telemetry.lon}° E</span>
        </div>
        <div>
          ZOOM <span className="text-slate-200">{telemetry.zoom}</span>
        </div>
        <div className="hidden sm:inline">
          BASE <span className="text-slate-300 uppercase">{baseMap.replace("-", " ")}</span>
        </div>
        <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]" />
          ACCELERATED
        </div>
      </div>
    </div>
  )
}

function generateGraticuleGeoJSON(): any {
  const features: any[] = []
  // Longitude meridians every 5 degrees
  for (let lon = -180; lon <= 180; lon += 5) {
    const coords: [number, number][] = []
    for (let lat = -85; lat <= 85; lat += 2) {
      coords.push([lon, lat])
    }
    features.push({
      type: "Feature",
      geometry: { type: "LineString", coordinates: coords },
      properties: { label: `${lon}°` },
    })
  }
  // Latitude parallels every 5 degrees
  for (let lat = -80; lat <= 80; lat += 5) {
    const coords: [number, number][] = []
    for (let lon = -180; lon <= 180; lon += 2) {
      coords.push([lon, lat])
    }
    features.push({
      type: "Feature",
      geometry: { type: "LineString", coordinates: coords },
      properties: { label: `${lat}°` },
    })
  }
  return { type: "FeatureCollection", features }
}
