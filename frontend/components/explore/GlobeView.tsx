"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * GlobeView Component — CesiumJS 3D Earth Globe
 * Phase 1 Foundation
 */

import React, { useEffect, useRef } from "react"
import { DEFAULT_CAMERA_STATE } from "@/lib/explore/constants"
import { globeController } from "@/lib/explore/globe-controller"
import { globeState } from "@/lib/explore/globe-state"
import { performanceMonitor } from "@/lib/explore/performance"
import { GlobeCameraState, RendererAdapter } from "@/lib/explore/types"

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
      script.addEventListener("load", () => resolve((window as any).Cesium))
      script.addEventListener("error", () => reject(new Error("Failed to load /cesium/Cesium.js")))
    }
  })
}

export default function GlobeView() {
  const containerRef = useRef<HTMLDivElement>(null)
  const viewerRef = useRef<any>(null)
  const cesiumLayersRef = useRef<Map<string, any>>(new Map())

  useEffect(() => {
    if (typeof window === "undefined" || !containerRef.current) return

    let isMounted = true
    performanceMonitor.startInitTimer()
    globeState.setRendererStatus("loading")

    loadCesiumGlobal()
      .then((Cesium) => {
        if (!isMounted || !containerRef.current) return

        try {
          // Check WebGL support
          if (
            Cesium.FeatureDetection &&
            !Cesium.FeatureDetection.supportsWebGL(containerRef.current)
          ) {
            globeState.setWebglSupported(false)
            globeState.setRendererStatus("error", "WebGL not supported by hardware/browser")
            return
          }

          // Initialize lightweight, conservative viewer (Section 31: requestRenderMode)
          const creditDiv = document.createElement("div")
          creditDiv.style.display = "none"

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
            shouldAnimate: false,
            requestRenderMode: true,
            maximumRenderTimeChange: Infinity,
            contextOptions: { webgl: { preserveDrawingBuffer: true } },
          })

          viewerRef.current = viewer

          // Add clean Esri World Dark Gray Basemap (100% public, zero watermark)
          viewer.imageryLayers.removeAll()
          viewer.imageryLayers.addImageryProvider(
            new Cesium.UrlTemplateImageryProvider({
              url: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
              credit: "Esri / OpenStreetMap",
            })
          )

          // Set initial camera to India / Central subcontinent
          const currentCam = globeState.getState().camera
          viewer.camera.setView({
            destination: Cesium.Cartesian3.fromDegrees(
              currentCam.longitude,
              currentCam.latitude,
              15000000 / Math.pow(2, currentCam.zoom - 2)
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
              const destHeight = 15000000 / Math.pow(2, (target.zoom ?? 5) - 2)
              viewerRef.current.camera.flyTo({
                destination: Cesium.Cartesian3.fromDegrees(
                  target.longitude,
                  target.latitude,
                  destHeight
                ),
                orientation: {
                  heading: Cesium.Math.toRadians(target.heading ?? 0),
                  pitch: Cesium.Math.toRadians(target.pitch ?? -45),
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
              if (layerId === "layer-base-dark" && viewerRef.current.imageryLayers.length > 0) {
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
              if (layerId === "layer-base-dark" && viewerRef.current.imageryLayers.length > 0) {
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
              const CesiumGlobal = (window as any).Cesium
              if (!CesiumGlobal) return
              try {
                const existing = viewerRef.current.entities.getById("trinetra-aoi-entity")
                if (existing) viewerRef.current.entities.remove(existing)

                if (!geom) return
                const coords = geom.coordinates ? (geom.coordinates[0] || []) : []
                const flatHierarchy = coords.flatMap((pt: [number, number]) => [pt[0], pt[1]])
                if (flatHierarchy.length >= 6) {
                  viewerRef.current.entities.add({
                    id: "trinetra-aoi-entity",
                    polygon: {
                      hierarchy: CesiumGlobal.Cartesian3.fromDegreesArray(flatHierarchy),
                      material: CesiumGlobal.Color.CYAN.withAlpha(0.2),
                      outline: true,
                      outlineColor: CesiumGlobal.Color.CYAN,
                      outlineWidth: 2,
                    },
                  })
                  viewerRef.current.scene.requestRender()
                }
              } catch (e) {
                console.warn("[GlobeView] Failed to add AOI entity to Cesium:", e)
              }
            },
            clearAOI: () => {
              if (!viewerRef.current) return
              const existing = viewerRef.current.entities.getById("trinetra-aoi-entity")
              if (existing) {
                viewerRef.current.entities.remove(existing)
                viewerRef.current.scene.requestRender()
              }
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
        } catch (initErr: any) {
          console.error("[GlobeView] Cesium initialization error:", initErr)
          globeState.setRendererStatus("error", initErr?.message || "Cesium WebGL Init Failed")
        }
      })
      .catch((importErr) => {
        console.error("[GlobeView] Failed to load Cesium script:", importErr)
        globeState.setRendererStatus("error", "Cesium module load failure")
      })

    return () => {
      isMounted = false
      globeController.unregisterAdapter("3d")
      if (viewerRef.current && !viewerRef.current.isDestroyed()) {
        try {
          viewerRef.current.destroy()
        } catch (e) {
          // Safe teardown
        }
        viewerRef.current = null
      }
    }
  }, [])

  return (
    <div className="globe-container" ref={containerRef} style={{ width: "100%", height: "100%" }} />
  )
}
