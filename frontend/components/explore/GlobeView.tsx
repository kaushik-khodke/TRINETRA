"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * GlobeView Component — CesiumJS 3D Earth Globe
 * Phase 1 Foundation
 */

import React, { useEffect, useRef, useState } from "react"
import { BASEMAP_PRESETS, DEFAULT_CAMERA_STATE, REEARTH_TERRAIN_URL } from "@/lib/explore/constants"
import { globeController } from "@/lib/explore/globe-controller"
import { globeState } from "@/lib/explore/globe-state"
import { performanceMonitor } from "@/lib/explore/performance"
import { GlobeCameraState, RendererAdapter } from "@/lib/explore/types"
import { globeCommandBus } from "@/lib/explore/globe-command-bus"
import { aoiStateManager } from "@/lib/explore/aoi-state"
import { AreaOfInterest } from "@/lib/workstation/types"
import { Check, X } from "lucide-react"

const SHARPEN_SHADER = `
  uniform sampler2D colorTexture;
  uniform vec2 colorTextureDimensions;
  uniform float amount;
  in vec2 v_textureCoordinates;

  void main() {
    vec2 uv = v_textureCoordinates;
    vec2 texel = 1.0 / colorTextureDimensions;
    vec4 center = texture(colorTexture, uv);
    vec4 blur = (
      texture(colorTexture, uv + vec2(-texel.x, -texel.y)) +
      texture(colorTexture, uv + vec2( 0.0,     -texel.y)) +
      texture(colorTexture, uv + vec2( texel.x, -texel.y)) +
      texture(colorTexture, uv + vec2(-texel.x,  0.0))     +
      center +
      texture(colorTexture, uv + vec2( texel.x,  0.0))     +
      texture(colorTexture, uv + vec2(-texel.x,  texel.y)) +
      texture(colorTexture, uv + vec2( 0.0,      texel.y)) +
      texture(colorTexture, uv + vec2( texel.x,  texel.y))
    ) / 9.0;
    vec4 sharpened = center + (center - blur) * amount;
    out_FragColor = vec4(clamp(sharpened.rgb, 0.0, 1.0), center.a);
  }
`

/**
 * Picks accurate ground lon/lat degrees from Cesium canvas pixel coordinates.
 * Intersects with 3D terrain mesh or falls back to WGS84 ellipsoid.
 */
function getLonLatFromPixel(
  viewer: any,
  Cesium: any,
  windowPosition: { x: number; y: number }
): [number, number] | null {
  if (!viewer || viewer.isDestroyed() || !viewer.scene || !windowPosition) return null
  const scene = viewer.scene
  let cartesian = null

  try {
    const ray = viewer.camera.getPickRay(windowPosition)
    if (ray) {
      cartesian = scene.globe.pick(ray, scene)
    }
  } catch {}

  if (!cartesian) {
    try {
      cartesian = viewer.camera.pickEllipsoid(windowPosition, scene.globe.ellipsoid)
    } catch {}
  }

  if (!cartesian) return null

  try {
    const cartographic = Cesium.Cartographic.fromCartesian(cartesian)
    if (!cartographic) return null
    const lon = Cesium.Math.toDegrees(cartographic.longitude)
    const lat = Cesium.Math.toDegrees(cartographic.latitude)
    if (!isFinite(lon) || !isFinite(lat)) return null
    return [lon, lat]
  } catch {
    return null
  }
}

/**
 * Client-only standalone loader for CesiumJS
 * Keeps Cesium strictly out of the main Next.js/Turbopack bundle
 */
function loadCesiumGlobal(): Promise<any> {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("SSR not supported"))
  }

  if ((window as any).Cesium) {
    return Promise.resolve((window as any).Cesium)
  }

  return new Promise((resolve, reject) => {
    // Configure Cesium static base asset URL
    ;(window as any).CESIUM_BASE_URL = "/cesium"

    // Load Cesium widgets CSS dynamically if not already in document
    const cssId = "cesium-widgets-css"
    if (!document.getElementById(cssId)) {
      const link = document.createElement("link")
      link.id = cssId
      link.rel = "stylesheet"
      link.href = "/cesium/Widgets/widgets.css"
      document.head.appendChild(link)
    }

    const scriptId = "cesium-standalone-script"
    let script = document.getElementById(scriptId) as HTMLScriptElement
    if (!script) {
      script = document.createElement("script")
      script.id = scriptId
      script.src = "/cesium/Cesium.js"
      script.async = true
      script.onload = () => {
        if ((window as any).Cesium) {
          resolve((window as any).Cesium)
        } else {
          reject(new Error("Cesium global object not found"))
        }
      }
      script.onerror = () => reject(new Error("Failed to load /cesium/Cesium.js"))
      document.body.appendChild(script)
    } else {
      if ((window as any).Cesium) {
        resolve((window as any).Cesium)
      } else {
        script.addEventListener("load", () => resolve((window as any).Cesium))
        script.addEventListener("error", () => reject(new Error("Failed to load /cesium/Cesium.js")))
      }
    }
  })
}

export interface GlobeViewProps {
  viewId?: "view-a" | "view-b"
  aois?: AreaOfInterest[]
  activeAOI?: AreaOfInterest | null
  hiddenAoiIds?: Set<string>
  onSelectAOI?: (aoi: AreaOfInterest) => void
  drawingMode?: "box" | "polygon" | "rectangle" | null
  onFinishDrawingAOI?: (geometry: any, keepDrawing?: boolean) => void
  onCancelDrawing?: () => void
  fitBoundsBbox?: [number, number, number, number] | null
}

export default function GlobeView({
  viewId = "view-a",
  aois,
  activeAOI,
  hiddenAoiIds,
  onSelectAOI,
  drawingMode,
  onFinishDrawingAOI,
  onCancelDrawing,
  fitBoundsBbox,
}: GlobeViewProps = {}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const viewerRef = useRef<any>(null)
  const cesiumLayersRef = useRef<Map<string, any>>(new Map())
  const firstCornerRef = useRef<[number, number] | null>(null)
  const downPixelRef = useRef<{ x: number; y: number } | null>(null)
  const isMouseDownRef = useRef<boolean>(false)
  const polygonPointsRef = useRef<[number, number][]>([])
  const aoiHandlerRef = useRef<any>(null)

  // Workstation and Drawing Refs to avoid stale closures
  const drawingModeRef = React.useRef(drawingMode)
  drawingModeRef.current = drawingMode
  const onFinishDrawingAOIRef = React.useRef(onFinishDrawingAOI)
  onFinishDrawingAOIRef.current = onFinishDrawingAOI
  const onCancelDrawingRef = React.useRef(onCancelDrawing)
  onCancelDrawingRef.current = onCancelDrawing

  const [activeDrawMode, setActiveDrawMode] = React.useState<string | null>(null)
  const [pointCount, setPointCount] = React.useState<number>(0)

  useEffect(() => {
    if (typeof window === "undefined" || !containerRef.current) return

    let isMounted = true
    performanceMonitor.startInitTimer()
    globeState.setRendererStatus("loading")

    loadCesiumGlobal()
      .then((Cesium) => {
        if (!isMounted || !containerRef.current) return

        try {
          // Check WebGL support natively
          const canvas = document.createElement("canvas")
          const gl =
            canvas.getContext("webgl2") ||
            canvas.getContext("webgl") ||
            canvas.getContext("experimental-webgl")
          if (!gl) {
            globeState.setWebglSupported(false)
            globeState.setRendererStatus("error", "WebGL not supported by hardware/browser")
            return
          }

          // Provider credit container
          const creditDiv = document.createElement("div")
          creditDiv.id = "cesium-credits"
          creditDiv.style.position = "absolute"
          creditDiv.style.bottom = "6px"
          creditDiv.style.left = "8px"
          creditDiv.style.color = "rgba(255, 255, 255, 0.45)"
          creditDiv.style.fontSize = "10px"
          creditDiv.style.zIndex = "10"
          creditDiv.style.pointerEvents = "none"
          containerRef.current.appendChild(creditDiv)

          const viewer = new Cesium.Viewer(containerRef.current, {
            animation: false,
            timeline: false,
            fullscreenButton: false,
            geocoder: false,
            homeButton: false,
            infoBox: false,
            sceneModePicker: false,
            selectionIndicator: false,
            navigationHelpButton: false,
            baseLayerPicker: false,
            baseLayer: false, // Critical: Disables Cesium Ion default imagery token requirement
            creditContainer: creditDiv,
            shouldAnimate: true,
            requestRenderMode: false,
            msaaSamples: 4,
            contextOptions: { webgl: { preserveDrawingBuffer: true } },
          })

          viewerRef.current = viewer

          // Add resilient render error recovery to prevent WebGL scene freezing
          try {
            ;(viewer as any).showErrorPanel = (title: string, message: string, err: any) => {
              console.warn("[GlobeView] Cesium viewer error panel suppressed:", title, message, err)
            }
            if (viewer.cesiumWidget) {
              ;(viewer.cesiumWidget as any).showErrorPanel = (title: string, message: string, err: any) => {
                console.warn("[GlobeView] CesiumWidget error panel suppressed:", title, message, err)
              }
            }
            viewer.scene.renderError.addEventListener((scene: any, error: any) => {
              console.warn("[GlobeView] Intercepted Cesium render error, clearing corrupt geometries:", error)
              try {
                const existingPoly = viewer.entities.getById("trinetra-aoi-entity")
                if (existingPoly) viewer.entities.remove(existingPoly)
                const existingOutline = viewer.entities.getById("trinetra-aoi-outline")
                if (existingOutline) viewer.entities.remove(existingOutline)
              } catch {}
              viewer.useDefaultRenderLoop = true
            })
          } catch (e) {
            // Non-blocking
          }

          // Atmospheric lighting and realism matching Shanetra
          try {
            viewer.scene.globe.show = true
            if (viewer.scene.skyAtmosphere) {
              viewer.scene.skyAtmosphere.show = true
              viewer.scene.skyAtmosphere.atmosphereLightIntensity = 18
              viewer.scene.skyAtmosphere.saturationShift = -0.12
              viewer.scene.skyAtmosphere.brightnessShift = -0.08
            }
          } catch (e) {
            // Non-blocking scene enhancement
          }

          // Use default reliable ellipsoid terrain
          viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider()

          // Add Default Authentic High-Resolution Esri World Satellite Imagery
          viewer.imageryLayers.removeAll()
          const esriProvider = new Cesium.UrlTemplateImageryProvider({
            url: "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            credit: "Powered by Esri — Source: Esri, Maxar, Earthstar Geographics",
            maximumLevel: 19,
          })
          const baseLayer = viewer.imageryLayers.addImageryProvider(esriProvider, 0)
          baseLayer.alpha = 1.0
          baseLayer.show = true

          // Set initial camera to India / Central subcontinent
          const currentCam = globeState.getState().camera
          viewer.camera.setView({
            destination: Cesium.Cartesian3.fromDegrees(
              currentCam.longitude,
              currentCam.latitude,
              15000000 / Math.pow(2, Math.max(1, currentCam.zoom - 2))
            ),
            orientation: {
              heading: Cesium.Math.toRadians(currentCam.heading || 0),
              pitch: Cesium.Math.toRadians(currentCam.pitch || -90),
              roll: 0,
            },
          })

          performanceMonitor.recordInitComplete("3d")
          globeState.setRendererStatus("ready")
          viewer.scene.requestRender()

          // Camera sync listener
          const removeCameraListener = viewer.camera.changed.addEventListener(() => {
            if (!viewerRef.current) return
            performanceMonitor.recordFrame()

            const cartographic = Cesium.Cartographic.fromCartesian(viewer.camera.position)
            const lat = Cesium.Math.toDegrees(cartographic.latitude)
            const lng = Cesium.Math.toDegrees(cartographic.longitude)
            const height = cartographic.height

            // Calculate approximate zoom from altitude
            const zoom = Math.max(1, Math.min(20, Math.round(27 - Math.log2(height))))

            globeState.setCamera({
              latitude: lat,
              longitude: lng,
              zoom: zoom,
              heading: Cesium.Math.toDegrees(viewer.camera.heading),
              pitch: Cesium.Math.toDegrees(viewer.camera.pitch),
              roll: Cesium.Math.toDegrees(viewer.camera.roll),
            })
          })

          // Register adapter with centralized GlobeController
          const adapter: RendererAdapter = {
            flyTo: (target) => {
              if (!viewerRef.current) return
              const CesiumGlobal = (window as any).Cesium || Cesium

              // Clamped downward pitch (-15 to -90 deg), default to -50 deg bird's-eye perspective
              const safePitch =
                typeof target.pitch === "number" && target.pitch <= -15 && target.pitch >= -90
                  ? target.pitch
                  : -50

              const pitchRad = CesiumGlobal.Math.toRadians(safePitch)
              const headingRad = CesiumGlobal.Math.toRadians(target.heading ?? 0)

              // If bounding box provided, use Cesium.Rectangle for ideal framing
              if (target.bounds && target.bounds.length === 4) {
                const [rawW, rawS, rawE, rawN] = target.bounds
                const w = Math.max(-179.9, Math.min(179.9, rawW))
                const s = Math.max(-85.0, Math.min(85.0, rawS))
                const e = Math.min(179.9, Math.max(-179.9, rawE))
                const n = Math.min(85.0, Math.max(-85.0, rawN))

                // If bounds span > 180 deg or wrap abnormally, fall back to coordinate centering below
                if (Math.abs(e - w) < 180 && w <= e && s <= n) {
                  viewerRef.current.camera.flyTo({
                    destination: CesiumGlobal.Rectangle.fromDegrees(w, s, e, n),
                    orientation: {
                      heading: headingRad,
                      pitch: pitchRad,
                      roll: 0,
                    },
                    duration: target.duration ?? 1.5,
                  })
                  return
                }
              }

              // Calculate camera offset so line-of-sight centers exactly on target ground point
              const destHeight = 15000000 / Math.pow(2, (target.zoom ?? 11.5) - 2)
              const pitchDown = Math.abs(pitchRad)
              const groundOffset =
                pitchDown < Math.PI / 2 - 0.05 ? destHeight / Math.tan(pitchDown) : 0

              const metersPerDegreeLat = 111320
              const latRad = CesiumGlobal.Math.toRadians(target.latitude)
              const metersPerDegreeLon = 111320 * Math.max(0.1, Math.cos(latRad))

              const dLat = (groundOffset * Math.cos(headingRad)) / metersPerDegreeLat
              const dLon = (groundOffset * Math.sin(headingRad)) / metersPerDegreeLon

              const camLat = Math.max(-89.9, Math.min(89.9, target.latitude - dLat))
              const camLon = Math.max(-180, Math.min(180, target.longitude - dLon))

              viewerRef.current.camera.flyTo({
                destination: CesiumGlobal.Cartesian3.fromDegrees(
                  camLon,
                  camLat,
                  destHeight
                ),
                orientation: {
                  heading: headingRad,
                  pitch: pitchRad,
                  roll: 0,
                },
                duration: target.duration ?? 1.5,
              })
            },
            resetView: () => {
              if (!viewerRef.current) return
              viewerRef.current.camera.flyTo({
                destination: Cesium.Cartesian3.fromDegrees(
                  DEFAULT_CAMERA_STATE.longitude,
                  DEFAULT_CAMERA_STATE.latitude,
                  10000000
                ),
                orientation: {
                  heading: 0,
                  pitch: Cesium.Math.toRadians(-90),
                  roll: 0,
                },
                duration: 1.5,
              })
            },
            setLayerVisibility: (layerId, visible) => {
              if (!viewerRef.current) return
              if (
                (layerId === "layer-base-satellite" || layerId === "layer-base-dark") &&
                viewerRef.current.imageryLayers.length > 0
              ) {
                viewerRef.current.imageryLayers.get(0).show = visible
                viewerRef.current.scene.requestRender()
                return
              }
              const imgLayer = cesiumLayersRef.current.get(layerId)
              if (imgLayer) {
                imgLayer.show = visible
                viewerRef.current.scene.requestRender()
              }
            },
            setLayerOpacity: (layerId, opacity) => {
              if (!viewerRef.current) return
              if (
                (layerId === "layer-base-satellite" || layerId === "layer-base-dark") &&
                viewerRef.current.imageryLayers.length > 0
              ) {
                viewerRef.current.imageryLayers.get(0).alpha = opacity
                viewerRef.current.scene.requestRender()
                return
              }
              const imgLayer = cesiumLayersRef.current.get(layerId)
              if (imgLayer) {
                imgLayer.alpha = opacity
                viewerRef.current.scene.requestRender()
              }
            },
            setBasemap: async (basemapId: string, tileUrl?: string) => {
              if (!viewerRef.current) return
              const CesiumGlobal = (window as any).Cesium
              if (!CesiumGlobal) return

              try {
                viewerRef.current.scene.globe.show = true
                const preset = BASEMAP_PRESETS[basemapId]
                const credit = preset?.attribution || "TRINETRA Earth Observation"
                const resolvedUrl = tileUrl || preset?.tileUrl || BASEMAP_PRESETS.satellite.tileUrl

                const newProvider = new CesiumGlobal.UrlTemplateImageryProvider({
                  url: resolvedUrl,
                  credit: credit,
                  maximumLevel: preset?.maxZoom || 19,
                })

                if (viewerRef.current.imageryLayers.length > 0) {
                  viewerRef.current.imageryLayers.remove(viewerRef.current.imageryLayers.get(0), true)
                }
                const newBaseLayer = viewerRef.current.imageryLayers.addImageryProvider(newProvider, 0)
                newBaseLayer.alpha = 1.0
                newBaseLayer.show = true
                viewerRef.current.scene.requestRender()
              } catch (err) {
                console.error("[GlobeView] Failed to switch basemap:", err)
              }
            },
            addLayerSource: (layerDef) => {
              if (!viewerRef.current || !layerDef.tileTemplate) return
              const CesiumGlobal = (window as any).Cesium
              if (!CesiumGlobal) return
              try {
                const provider = new CesiumGlobal.UrlTemplateImageryProvider({
                  url: layerDef.tileTemplate,
                })
                const imgLayer = viewerRef.current.imageryLayers.addImageryProvider(provider)
                imgLayer.alpha = layerDef.opacity ?? 1.0
                imgLayer.show = true
                cesiumLayersRef.current.set(layerDef.id, imgLayer)
                viewerRef.current.scene.requestRender()
              } catch (e) {
                console.warn("[GlobeView] Failed to add imagery layer to Cesium:", e)
              }
            },
            removeLayerSource: (layerId) => {
              if (!viewerRef.current) return
              const imgLayer = cesiumLayersRef.current.get(layerId)
              if (imgLayer) {
                viewerRef.current.imageryLayers.remove(imgLayer, true)
                cesiumLayersRef.current.delete(layerId)
                viewerRef.current.scene.requestRender()
              }
            },
            setAOI: (geom) => {
              if (!viewerRef.current) return
              const CesiumGlobal = (window as any).Cesium || Cesium
              if (!CesiumGlobal) return
              try {
                const existingPoly = viewerRef.current.entities.getById("trinetra-aoi-entity")
                if (existingPoly) viewerRef.current.entities.remove(existingPoly)
                const existingOutline = viewerRef.current.entities.getById("trinetra-aoi-outline")
                if (existingOutline) viewerRef.current.entities.remove(existingOutline)

                if (!geom) return
                const rawCoords = geom.coordinates ? (geom.coordinates[0] || []) : []
                if (!rawCoords || rawCoords.length < 3) return

                let minLon = 180, maxLon = -180
                const sanitizedCoords: [number, number][] = []
                for (const pt of rawCoords) {
                  if (!Array.isArray(pt) || pt.length < 2) continue
                  const lon = Math.max(-179.9, Math.min(179.9, Number(pt[0]) || 0))
                  const lat = Math.max(-85.0, Math.min(85.0, Number(pt[1]) || 0))
                  if (lon < minLon) minLon = lon
                  if (lon > maxLon) maxLon = lon
                  sanitizedCoords.push([lon, lat])
                }

                if (sanitizedCoords.length < 3) return

                // Deduplicate adjacent vertices to avoid zero-length segments that trigger splitLongitude DeveloperError
                const uniqueCoords: [number, number][] = []
                for (const pt of sanitizedCoords) {
                  if (uniqueCoords.length === 0) {
                    uniqueCoords.push(pt)
                  } else {
                    const prev = uniqueCoords[uniqueCoords.length - 1]
                    if (Math.abs(prev[0] - pt[0]) > 1e-6 || Math.abs(prev[1] - pt[1]) > 1e-6) {
                      uniqueCoords.push(pt)
                    }
                  }
                }

                if (uniqueCoords.length < 3) return

                // Check if polygon spans or touches the antimeridian (+-180)
                const crossesOrNearMeridian =
                  Math.abs(maxLon - minLon) >= 180 ||
                  Math.abs(minLon) >= 175 ||
                  Math.abs(maxLon) >= 175

                // Cesium polygon hierarchy expects outer ring WITHOUT duplicate closing vertex
                const polyCoords = [...uniqueCoords]
                if (
                  polyCoords.length > 3 &&
                  Math.abs(polyCoords[0][0] - polyCoords[polyCoords.length - 1][0]) < 1e-6 &&
                  Math.abs(polyCoords[0][1] - polyCoords[polyCoords.length - 1][1]) < 1e-6
                ) {
                  polyCoords.pop()
                }

                if (polyCoords.length < 3) return

                const flatHierarchy = polyCoords.flatMap((pt) => [pt[0], pt[1]])
                if (flatHierarchy.length >= 6) {
                  // Only use ClassificationType.BOTH if away from antimeridian to avoid Cesium splitLongitude DeveloperError
                  const classificationType =
                    !crossesOrNearMeridian && CesiumGlobal.ClassificationType
                      ? CesiumGlobal.ClassificationType.BOTH
                      : undefined

                  // Semi-transparent glowing cyan polygon fill clamped to terrain
                  viewerRef.current.entities.add({
                    id: "trinetra-aoi-entity",
                    polygon: {
                      hierarchy: CesiumGlobal.Cartesian3.fromDegreesArray(flatHierarchy),
                      material: CesiumGlobal.Color.fromCssColorString("#06b6d4").withAlpha(0.22),
                      classificationType: classificationType,
                    },
                  })

                  // Outline: safely closed ring
                  const outlineCoords = [...polyCoords, polyCoords[0]]
                  const flatOutline = outlineCoords.flatMap((pt) => [pt[0], pt[1]])

                  try {
                    viewerRef.current.entities.add({
                      id: "trinetra-aoi-outline",
                      polyline: {
                        positions: CesiumGlobal.Cartesian3.fromDegreesArray(flatOutline),
                        width: 3.5,
                        material: CesiumGlobal.Color.fromCssColorString("#22d3ee"),
                        clampToGround: !crossesOrNearMeridian,
                      },
                    })
                  } catch (outlineErr) {
                    console.warn("[GlobeView] Could not add clamped outline, falling back to unclamped:", outlineErr)
                    try {
                      viewerRef.current.entities.add({
                        id: "trinetra-aoi-outline",
                        polyline: {
                          positions: CesiumGlobal.Cartesian3.fromDegreesArray(flatOutline),
                          width: 2.5,
                          material: CesiumGlobal.Color.fromCssColorString("#22d3ee"),
                          clampToGround: false,
                        },
                      })
                    } catch {}
                  }

                  viewerRef.current.scene.requestRender()
                }
              } catch (e) {
                console.warn("[GlobeView] Failed to add AOI entity to Cesium:", e)
              }
            },
            clearAOI: () => {
              if (!viewerRef.current || viewerRef.current.isDestroyed()) return
              const existingPoly = viewerRef.current.entities.getById("trinetra-aoi-entity")
              if (existingPoly) viewerRef.current.entities.remove(existingPoly)
              const existingOutline = viewerRef.current.entities.getById("trinetra-aoi-outline")
              if (existingOutline) viewerRef.current.entities.remove(existingOutline)
              clearDrawPreviews()
              viewerRef.current.scene.requestRender()
            },
            getCameraState: (): GlobeCameraState => {

              if (!viewerRef.current) return { ...DEFAULT_CAMERA_STATE }
              const cart = Cesium.Cartographic.fromCartesian(viewerRef.current.camera.position)
              return {
                latitude: Cesium.Math.toDegrees(cart.latitude),
                longitude: Cesium.Math.toDegrees(cart.longitude),
                zoom: Math.max(1, Math.min(20, Math.round(27 - Math.log2(cart.height)))),
                heading: Cesium.Math.toDegrees(viewerRef.current.camera.heading),
                pitch: Cesium.Math.toDegrees(viewerRef.current.camera.pitch),
              }
            },
            destroy: () => {
              if (removeCameraListener) removeCameraListener()
              if (viewerRef.current && !viewerRef.current.isDestroyed()) {
                viewerRef.current.destroy()
                viewerRef.current = null
              }
            },
          }

          globeController.registerAdapter("3d", adapter)

          // ---------------------------------------------------------------
          // Interactive AOI Drawing & ScreenSpaceEventHandler Integration
          // ---------------------------------------------------------------
          const updatePreview = (coords: [number, number][]) => {
            if (!viewerRef.current || viewerRef.current.isDestroyed()) return
            const CesiumGlobal = (window as any).Cesium || Cesium
            if (!CesiumGlobal) return

            const flatCoords = coords.flatMap((pt) => [pt[0], pt[1]])
            if (flatCoords.length < 4) {
              clearDrawPreviews()
              return
            }

            const existingPoly = viewerRef.current.entities.getById("trinetra-aoi-draw-preview")
            if (existingPoly) viewerRef.current.entities.remove(existingPoly)

            const existingLine = viewerRef.current.entities.getById("trinetra-aoi-draw-outline")
            if (existingLine) viewerRef.current.entities.remove(existingLine)

            if (flatCoords.length >= 6) {
              viewerRef.current.entities.add({
                id: "trinetra-aoi-draw-preview",
                polygon: {
                  hierarchy: CesiumGlobal.Cartesian3.fromDegreesArray(flatCoords),
                  material: CesiumGlobal.Color.fromCssColorString("#06b6d4").withAlpha(0.2),
                  classificationType: CesiumGlobal.ClassificationType ? CesiumGlobal.ClassificationType.BOTH : undefined,
                },
              })
            }

            viewerRef.current.entities.add({
              id: "trinetra-aoi-draw-outline",
              polyline: {
                positions: CesiumGlobal.Cartesian3.fromDegreesArray(flatCoords),
                width: 2.5,
                material: CesiumGlobal.Color.fromCssColorString("#22d3ee"),
                clampToGround: true,
              },
            })

            viewerRef.current.scene.requestRender()
          }

          const clearDrawPreviews = () => {
            if (!viewerRef.current || viewerRef.current.isDestroyed()) return
            const existingPoly = viewerRef.current.entities.getById("trinetra-aoi-draw-preview")
            if (existingPoly) viewerRef.current.entities.remove(existingPoly)
            const existingLine = viewerRef.current.entities.getById("trinetra-aoi-draw-outline")
            if (existingLine) viewerRef.current.entities.remove(existingLine)
            viewerRef.current.scene.requestRender()
          }

          const getDrawMode = () => {
            if (drawingModeRef.current !== undefined) {
              if (drawingModeRef.current === "box") return "rectangle"
              return drawingModeRef.current
            }
            return aoiStateManager.getState().drawMode
          }

          const commitBox = (minX: number, minY: number, maxX: number, maxY: number) => {
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
            firstCornerRef.current = null
            downPixelRef.current = null
            isMouseDownRef.current = false
            clearDrawPreviews()
            if (onFinishDrawingAOIRef.current) {
              onFinishDrawingAOIRef.current(boxGeoJSON)
            } else {
              aoiStateManager.setAOI(boxGeoJSON)
            }
          }

          // Render pre-existing active AOI if already configured (explore mode)
          if (!aois) {
            const existingAOI = aoiStateManager.getState().activeAOI
            if (existingAOI) {
              adapter.setAOI?.(existingAOI)
            }
          }

          // Disable default double-click zooming behavior in Cesium
          viewer.screenSpaceEventHandler.removeInputAction(Cesium.ScreenSpaceEventType.LEFT_DOUBLE_CLICK)

          const aoiHandler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas)
          aoiHandlerRef.current = aoiHandler

          // LEFT_DOWN: Record drag start or first/second corner
          aoiHandler.setInputAction((movement: any) => {
            const drawMode = getDrawMode()
            if (!drawMode) return

            const coords = getLonLatFromPixel(viewerRef.current, Cesium, movement.position)
            if (!coords) return

            isMouseDownRef.current = true
            downPixelRef.current = { x: movement.position.x, y: movement.position.y }

            if (drawMode === "rectangle") {
              if (!firstCornerRef.current) {
                firstCornerRef.current = coords
              } else {
                // Second corner click in two-click mode
                const [x1, y1] = firstCornerRef.current
                const [x2, y2] = coords
                const minX = Math.min(x1, x2)
                const maxX = Math.max(x1, x2)
                const minY = Math.min(y1, y2)
                const maxY = Math.max(y1, y2)

                if (Math.hypot(maxX - minX, maxY - minY) > 0.0002) {
                  commitBox(minX, minY, maxX, maxY)
                }
              }
            } else if (drawMode === "polygon") {
              polygonPointsRef.current.push(coords)
              setPointCount(polygonPointsRef.current.length)
              if (polygonPointsRef.current.length >= 2) {
                const previewRing = [...polygonPointsRef.current, polygonPointsRef.current[0]]
                updatePreview(previewRing)
              }
            }
          }, Cesium.ScreenSpaceEventType.LEFT_DOWN)

          // MOUSE_MOVE: Real-time dynamic preview box/polygon
          aoiHandler.setInputAction((movement: any) => {
            const drawMode = getDrawMode()
            if (!drawMode) return

            const coords = getLonLatFromPixel(viewerRef.current, Cesium, movement.endPosition)
            if (!coords) return

            if (drawMode === "rectangle" && firstCornerRef.current) {
              const [x1, y1] = firstCornerRef.current
              const [x2, y2] = coords
              const minX = Math.min(x1, x2)
              const maxX = Math.max(x1, x2)
              const minY = Math.min(y1, y2)
              const maxY = Math.max(y1, y2)

              const previewRing: [number, number][] = [
                [minX, minY],
                [maxX, minY],
                [maxX, maxY],
                [minX, maxY],
                [minX, minY],
              ]
              updatePreview(previewRing)
            } else if (drawMode === "polygon" && polygonPointsRef.current.length > 0) {
              const previewRing: [number, number][] = [
                ...polygonPointsRef.current,
                coords,
                polygonPointsRef.current[0],
              ]
              updatePreview(previewRing)
            }
          }, Cesium.ScreenSpaceEventType.MOUSE_MOVE)

          // LEFT_UP: Drag-to-draw finalize
          aoiHandler.setInputAction((movement: any) => {
            const drawMode = getDrawMode()
            if (!drawMode) return

            const currentDownPixel = downPixelRef.current
            isMouseDownRef.current = false
            downPixelRef.current = null

            if (drawMode === "rectangle" && firstCornerRef.current) {
              const endCoords = getLonLatFromPixel(viewerRef.current, Cesium, movement.position)
              if (!endCoords) return

              const pixelDist = currentDownPixel
                ? Math.hypot(movement.position.x - currentDownPixel.x, movement.position.y - currentDownPixel.y)
                : 0

              const [x1, y1] = firstCornerRef.current
              const [x2, y2] = endCoords
              const minX = Math.min(x1, x2)
              const maxX = Math.max(x1, x2)
              const minY = Math.min(y1, y2)
              const maxY = Math.max(y1, y2)
              const coordDist = Math.hypot(maxX - minX, maxY - minY)

              // If user dragged more than 10 pixels and coordinates changed by > 0.0002 deg, finalize box
              if (pixelDist > 10 && coordDist > 0.0002) {
                commitBox(minX, minY, maxX, maxY)
              }
            }
          }, Cesium.ScreenSpaceEventType.LEFT_UP)

          // LEFT_DOUBLE_CLICK: Finalize polygon
          aoiHandler.setInputAction(() => {
            const drawMode = getDrawMode()
            const rawPts = polygonPointsRef.current
            const deduped = rawPts.filter((p, i, a) => i === 0 || Math.hypot(p[0] - a[i - 1][0], p[1] - a[i - 1][1]) > 1e-6)
            if (drawMode === "polygon" && deduped.length >= 3) {
              const closedRing = [...deduped, deduped[0]]
              const polyGeoJSON = {
                type: "Polygon",
                coordinates: [closedRing],
              }
              polygonPointsRef.current = []
              setPointCount(0)
              clearDrawPreviews()
              if (onFinishDrawingAOIRef.current) {
                onFinishDrawingAOIRef.current(polyGeoJSON)
              } else {
                aoiStateManager.setAOI(polyGeoJSON)
              }
            }
          }, Cesium.ScreenSpaceEventType.LEFT_DOUBLE_CLICK)

          // RIGHT_CLICK: Close polygon or cancel active drawing
          aoiHandler.setInputAction(() => {
            const drawMode = getDrawMode()
            const rawPts = polygonPointsRef.current
            const deduped = rawPts.filter((p, i, a) => i === 0 || Math.hypot(p[0] - a[i - 1][0], p[1] - a[i - 1][1]) > 1e-6)
            if (drawMode === "polygon" && deduped.length >= 3) {
              const closedRing = [...deduped, deduped[0]]
              const polyGeoJSON = {
                type: "Polygon",
                coordinates: [closedRing],
              }
              polygonPointsRef.current = []
              setPointCount(0)
              clearDrawPreviews()
              if (onFinishDrawingAOIRef.current) {
                onFinishDrawingAOIRef.current(polyGeoJSON)
              } else {
                aoiStateManager.setAOI(polyGeoJSON)
              }
            } else if (drawMode) {
              firstCornerRef.current = null
              downPixelRef.current = null
              polygonPointsRef.current = []
              setPointCount(0)
              clearDrawPreviews()
              if (onCancelDrawingRef.current) {
                onCancelDrawingRef.current()
              } else {
                aoiStateManager.setDrawMode(null)
              }
            }
          }, Cesium.ScreenSpaceEventType.RIGHT_CLICK)

          // Subscribe to aoiStateManager: Lock camera & update cursor when drawing (Explore mode)
          const unsubAOI = aoiStateManager.subscribe((state) => {
            if (drawingModeRef.current !== undefined) return // Workstation mode controls its own drawing
            if (!viewerRef.current || viewerRef.current.isDestroyed()) return
            const canvas = viewerRef.current.scene?.canvas
            const controller = viewerRef.current.scene?.screenSpaceCameraController
            if (!controller) return

            setActiveDrawMode(state.drawMode)
            if (state.drawMode) {
              controller.enableRotate = false
              controller.enableTranslate = false
              controller.enableTilt = false
              controller.enableLook = false
              controller.enableZoom = false
              if (canvas) canvas.style.cursor = "crosshair"
            } else {
              controller.enableRotate = true
              controller.enableTranslate = true
              controller.enableTilt = true
              controller.enableLook = true
              controller.enableZoom = true
              if (canvas) canvas.style.cursor = "default"

              firstCornerRef.current = null
              downPixelRef.current = null
              isMouseDownRef.current = false
              polygonPointsRef.current = []
              setPointCount(0)
              clearDrawPreviews()
            }
          })

          // Subscribe to GlobeCommandBus for focus and AOI
          const unsubBus = globeCommandBus.subscribe((cmd) => {
            if (!viewerRef.current || !Cesium) return
            if (cmd.type === "FOCUS_ANALYSIS_REGION" && cmd.bounds && cmd.bounds.length === 4) {
              const b = cmd.bounds
              const w = Math.max(-179.9, Math.min(179.9, b[0]))
              const s = Math.max(-85.0, Math.min(85.0, b[1]))
              const e = Math.min(179.9, Math.max(-179.9, b[2]))
              const n = Math.min(85.0, Math.max(-85.0, b[3]))
              if (Math.abs(e - w) < 180 && w <= e && s <= n) {
                viewerRef.current.camera.flyTo({
                  destination: Cesium.Rectangle.fromDegrees(w, s, e, n),
                  duration: 1.5,
                })
              }
            } else if (cmd.type === "SET_AOI") {
              adapter.setAOI?.(cmd.geometry)
            } else if (cmd.type === "CLEAR_AOI") {
              adapter.clearAOI?.()
            } else if (cmd.type === "SET_BASEMAP") {
              adapter.setBasemap?.(cmd.basemapId, cmd.tileUrl)
            } else if (cmd.type === "SHOW_LAYER") {
              adapter.setLayerVisibility?.(cmd.layerId, true)
            } else if (cmd.type === "HIDE_LAYER") {
              adapter.setLayerVisibility?.(cmd.layerId, false)
            } else if (cmd.type === "SET_LAYER_OPACITY") {
              adapter.setLayerOpacity?.(cmd.layerId, cmd.opacity)
            }
          })

          // Save unsub functions on viewer for unmount
          ;(viewerRef.current as any).__unsubBus = unsubBus
          ;(viewerRef.current as any).__unsubAOI = unsubAOI
          ;(viewerRef.current as any).__aoiHandler = aoiHandler
        } catch (initErr: any) {
          console.error("[GlobeView] Cesium initialization error:", initErr)
          globeState.setRendererStatus("error", initErr?.message || "Cesium WebGL Init Failed")
        }
      })
      .catch((importErr) => {
        console.error("[GlobeView] Failed to load Cesium script:", importErr)
        globeState.setRendererStatus("error", "Cesium module load failure")
      })

    // Escape key cancels in-progress AOI drawing
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        const { drawMode } = aoiStateManager.getState()
        if (drawMode) {
          aoiStateManager.setDrawMode(null)
        }
      }
    }
    window.addEventListener("keydown", handleKeyDown)

    return () => {
      isMounted = false
      window.removeEventListener("keydown", handleKeyDown)
      globeController.unregisterAdapter("3d")
      if (viewerRef.current && !viewerRef.current.isDestroyed()) {
        try {
          if ((viewerRef.current as any).__unsubAOI) {
            ;(viewerRef.current as any).__unsubAOI()
          }
          if ((viewerRef.current as any).__aoiHandler) {
            ;(viewerRef.current as any).__aoiHandler.destroy()
          }
          if ((viewerRef.current as any).__unsubBus) {
            ;(viewerRef.current as any).__unsubBus()
          }
          viewerRef.current.destroy()
        } catch (e) {
          // Safe teardown
        }
        viewerRef.current = null
      }
    }
  }, [])

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
      setPointCount(0)
      if (viewerRef.current && !viewerRef.current.isDestroyed()) {
        const existingPoly = viewerRef.current.entities.getById("trinetra-aoi-draw-preview")
        if (existingPoly) viewerRef.current.entities.remove(existingPoly)
        const existingLine = viewerRef.current.entities.getById("trinetra-aoi-draw-outline")
        if (existingLine) viewerRef.current.entities.remove(existingLine)
        viewerRef.current.scene.requestRender()
      }
      if (onFinishDrawingAOIRef.current) {
        onFinishDrawingAOIRef.current(polyGeoJSON)
      } else {
        aoiStateManager.setAOI(polyGeoJSON)
      }
    }
  }

  // Cancel Drawing Trigger
  const handleCancelDrawing = () => {
    polygonPointsRef.current = []
    setPointCount(0)
    firstCornerRef.current = null
    downPixelRef.current = null
    isMouseDownRef.current = false
    if (viewerRef.current && !viewerRef.current.isDestroyed()) {
      const existingPoly = viewerRef.current.entities.getById("trinetra-aoi-draw-preview")
      if (existingPoly) viewerRef.current.entities.remove(existingPoly)
      const existingLine = viewerRef.current.entities.getById("trinetra-aoi-draw-outline")
      if (existingLine) viewerRef.current.entities.remove(existingLine)
      viewerRef.current.scene.requestRender()
    }
    if (onCancelDrawingRef.current) {
      onCancelDrawingRef.current()
    } else {
      aoiStateManager.setDrawMode(null)
    }
  }

  // Workstation Mode: Camera Lock on drawingMode
  useEffect(() => {
    if (drawingMode === undefined) return
    const mode = drawingMode ? (drawingMode === "box" ? "rectangle" : drawingMode) : null
    setActiveDrawMode(mode)
    if (!viewerRef.current || viewerRef.current.isDestroyed()) return
    const canvas = viewerRef.current.scene?.canvas
    const controller = viewerRef.current.scene?.screenSpaceCameraController
    if (!controller) return

    if (mode) {
      controller.enableRotate = false
      controller.enableTranslate = false
      controller.enableTilt = false
      controller.enableLook = false
      controller.enableZoom = false
      if (canvas) canvas.style.cursor = "crosshair"
    } else {
      controller.enableRotate = true
      controller.enableTranslate = true
      controller.enableTilt = true
      controller.enableLook = true
      controller.enableZoom = true
      if (canvas) canvas.style.cursor = "default"
      firstCornerRef.current = null
      downPixelRef.current = null
      isMouseDownRef.current = false
      polygonPointsRef.current = []
      setPointCount(0)
      const existingPoly = viewerRef.current.entities.getById("trinetra-aoi-draw-preview")
      if (existingPoly) viewerRef.current.entities.remove(existingPoly)
      const existingLine = viewerRef.current.entities.getById("trinetra-aoi-draw-outline")
      if (existingLine) viewerRef.current.entities.remove(existingLine)
      viewerRef.current.scene.requestRender()
    }
  }, [drawingMode])

  // Workstation Mode: Render all mission AOIs on 3D Globe
  useEffect(() => {
    if (!viewerRef.current || viewerRef.current.isDestroyed() || !aois) return
    const CesiumGlobal = (window as any).Cesium
    if (!CesiumGlobal) return

    const toRemove: any[] = []
    for (let i = 0; i < viewerRef.current.entities.values.length; i++) {
      const ent = viewerRef.current.entities.values[i]
      if (ent.id && typeof ent.id === "string" && ent.id.startsWith("workstation-aoi-")) {
        toRemove.push(ent)
      }
    }
    toRemove.forEach((e) => viewerRef.current.entities.remove(e))

    aois.forEach((aoi) => {
      if (hiddenAoiIds?.has(aoi.id) || !aoi.geometry) return
      const isActive = activeAOI?.id === aoi.id
      const rawGeom = aoi.geometry as any
      const geom = rawGeom.type === "Feature" ? rawGeom.geometry : rawGeom
      if (geom.type === "Polygon" && geom.coordinates?.[0]) {
        const ring = geom.coordinates[0]
        const flat = ring.flatMap((pt: [number, number]) => [pt[0], pt[1]])
        if (flat.length >= 6) {
          try {
            viewerRef.current.entities.add({
              id: `workstation-aoi-${aoi.id}`,
              polygon: {
                hierarchy: CesiumGlobal.Cartesian3.fromDegreesArray(flat),
                material: CesiumGlobal.Color.fromCssColorString(isActive ? "#22d3ee" : "#38bdf8").withAlpha(isActive ? 0.32 : 0.16),
                classificationType: CesiumGlobal.ClassificationType ? CesiumGlobal.ClassificationType.BOTH : undefined,
              },
            })
            viewerRef.current.entities.add({
              id: `workstation-aoi-outline-${aoi.id}`,
              polyline: {
                positions: CesiumGlobal.Cartesian3.fromDegreesArray(flat),
                width: isActive ? 3.0 : 1.8,
                material: CesiumGlobal.Color.fromCssColorString(isActive ? "#22d3ee" : "#38bdf8"),
                clampToGround: true,
              },
            })
          } catch (err) {
            console.warn("[GlobeView] Failed to add workstation AOI to Cesium:", aoi.id, err)
          }
        }
      }
    })
    viewerRef.current.scene.requestRender()
  }, [aois, activeAOI, hiddenAoiIds])

  // Fly Camera to fitBoundsBbox if requested
  useEffect(() => {
    if (!viewerRef.current || viewerRef.current.isDestroyed() || !fitBoundsBbox || fitBoundsBbox.length !== 4) return
    const CesiumGlobal = (window as any).Cesium
    if (!CesiumGlobal) return
    try {
      const [minX, minY, maxX, maxY] = fitBoundsBbox
      const rect = CesiumGlobal.Rectangle.fromDegrees(minX, minY, maxX, maxY)
      viewerRef.current.camera.flyTo({
        destination: rect,
        duration: 1.2,
      })
    } catch {}
  }, [fitBoundsBbox])

  return (
    <div className="relative w-full h-full overflow-hidden">
      <div className="globe-container" ref={containerRef} style={{ width: "100%", height: "100%" }} />

      {/* Floating Interactive 3D Drawing Guide & Action Bar */}
      {activeDrawMode && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-[#0a0e18]/85 border border-cyan-500/40 rounded-2xl px-4 py-2 flex items-center gap-3 shadow-2xl shadow-cyan-950/50 z-30 backdrop-blur-2xl animate-in fade-in slide-in-from-top-2">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping shrink-0" />
          <div className="text-xs text-slate-100 font-medium tracking-wide">
            {activeDrawMode === "rectangle" ? (
              <span>Drag to draw 3D box, or click two opposite corners</span>
            ) : (
              <span>
                Click to place 3D polygon vertices ({pointCount} added) · Double-click to close
              </span>
            )}
          </div>

          <div className="flex items-center gap-1.5 ml-2 border-l border-white/10 pl-3">
            {activeDrawMode === "polygon" && pointCount >= 3 && (
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
