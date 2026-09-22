"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * GlobeView Component — CesiumJS 3D Earth Globe
 * Phase 1 Foundation
 */

import React, { useEffect, useRef } from "react"
import { BASEMAP_PRESETS, DEFAULT_CAMERA_STATE, REEARTH_TERRAIN_URL } from "@/lib/explore/constants"
import { globeController } from "@/lib/explore/globe-controller"
import { globeState } from "@/lib/explore/globe-state"
import { performanceMonitor } from "@/lib/explore/performance"
import { GlobeCameraState, RendererAdapter } from "@/lib/explore/types"
import { globeCommandBus } from "@/lib/explore/globe-command-bus"

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

          // Check for credentials in localStorage or process.env
          const ionToken =
            (typeof window !== "undefined" && localStorage.getItem("trinetra_cesium_ion_token")) ||
            process.env.NEXT_PUBLIC_CESIUM_ION_TOKEN ||
            ""
          const googleApiKey =
            (typeof window !== "undefined" && localStorage.getItem("trinetra_google_maps_api_key")) ||
            process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ||
            ""

          if (ionToken) {
            Cesium.Ion.defaultAccessToken = ionToken
          }
          if (googleApiKey) {
            Cesium.GoogleMaps.defaultApiKey = googleApiKey
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
            shouldAnimate: false,
            requestRenderMode: true,
            maximumRenderTimeChange: Infinity,
            msaaSamples: 4,
            contextOptions: { webgl: { preserveDrawingBuffer: true } },
          })

          viewerRef.current = viewer

          // Atmospheric lighting and realism matching Shatnetra
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

          // Attach Keyless 3D Global Terrain (Re:Earth ellipsoidal quantized-mesh)
          try {
            Cesium.CesiumTerrainProvider.fromUrl(REEARTH_TERRAIN_URL)
              .then((terrainProvider: any) => {
                if (viewerRef.current && !viewerRef.current.isDestroyed()) {
                  viewerRef.current.terrainProvider = terrainProvider
                  viewerRef.current.scene.requestRender()
                }
              })
              .catch((err: any) => {
                console.warn("[GlobeView] Keyless 3D terrain fallback to flat ellipsoid:", err)
                if (viewerRef.current && !viewerRef.current.isDestroyed()) {
                  viewerRef.current.terrainProvider = new Cesium.EllipsoidTerrainProvider()
                }
              })
          } catch {
            if (viewerRef.current && !viewerRef.current.isDestroyed()) {
              viewerRef.current.terrainProvider = new Cesium.EllipsoidTerrainProvider()
            }
          }

          // Add Default Authentic Esri World Satellite Imagery via ArcGisMapServerImageryProvider
          // Fetches official ArcGIS MapServer tile scheme up to sub-meter LOD without missing tile errors!
          viewer.imageryLayers.removeAll()
          if (Cesium.ArcGisMapServerImageryProvider && Cesium.ArcGisMapServerImageryProvider.fromUrl) {
            Cesium.ArcGisMapServerImageryProvider.fromUrl(
              "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer",
              {
                credit: "Powered by Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community",
                enablePickFeatures: false,
              }
            ).then((esriProvider: any) => {
              if (viewerRef.current && !viewerRef.current.isDestroyed()) {
                viewerRef.current.imageryLayers.removeAll()
                const layer = viewerRef.current.imageryLayers.addImageryProvider(esriProvider, 0)
                layer.alpha = 1.0
                layer.show = true
                viewerRef.current.scene.requestRender()
              }
            }).catch((err: any) => {
              console.warn("[GlobeView] ArcGisMapServerImageryProvider error, fallback to UrlTemplate:", err)
              if (viewerRef.current && !viewerRef.current.isDestroyed()) {
                viewerRef.current.imageryLayers.removeAll()
                const fallbackLayer = viewerRef.current.imageryLayers.addImageryProvider(
                  new Cesium.UrlTemplateImageryProvider({
                    url: "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                    credit: "Powered by Esri — Source: Esri, Maxar, Earthstar Geographics",
                    maximumLevel: 18,
                  }),
                  0
                )
                fallbackLayer.alpha = 1.0
                fallbackLayer.show = true
                viewerRef.current.scene.requestRender()
              }
            })
          } else {
            const fallbackLayer = viewer.imageryLayers.addImageryProvider(
              new Cesium.UrlTemplateImageryProvider({
                url: "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                credit: "Powered by Esri — Source: Esri, Maxar, Earthstar Geographics",
                maximumLevel: 18,
              }),
              0
            )
            fallbackLayer.alpha = 1.0
            fallbackLayer.show = true
          }

          // Unsharp Mask Sharpening Post-Process Stage for crisp satellite details
          try {
            if (Cesium.PostProcessStage) {
              const sharpenStage = new Cesium.PostProcessStage({
                name: "trinetra_sharpen",
                fragmentShader: SHARPEN_SHADER,
                uniforms: {
                  amount: 1.08,
                },
              })
              viewer.scene.postProcessStages.add(sharpenStage)
            }
          } catch (postErr) {
            console.warn("[GlobeView] Sharpen shader attachment error:", postErr)
          }

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
                const [w, s, e, n] = target.bounds
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
                if (basemapId === "google-3d") {
                  const gKey =
                    localStorage.getItem("trinetra_google_maps_api_key") ||
                    process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ||
                    ""
                  const ionTok =
                    localStorage.getItem("trinetra_cesium_ion_token") ||
                    process.env.NEXT_PUBLIC_CESIUM_ION_TOKEN ||
                    ""
                  if (ionTok) CesiumGlobal.Ion.defaultAccessToken = ionTok
                  if (gKey) CesiumGlobal.GoogleMaps.defaultApiKey = gKey

                  try {
                    const tileset = await CesiumGlobal.createGooglePhotorealistic3DTileset({
                      onlyUsingWithGoogleGeocoder: true,
                    })
                    viewerRef.current.scene.primitives.add(tileset)
                    viewerRef.current.scene.globe.show = false
                    viewerRef.current.scene.requestRender()
                    return
                  } catch (err) {
                    console.warn("[GlobeView] Google 3D Tiles failed, reverting to globe surface:", err)
                  }
                }

                viewerRef.current.scene.globe.show = true
                const preset = BASEMAP_PRESETS[basemapId]
                const credit = preset?.attribution || "TRINETRA Earth Observation"

                let newProvider: any = null
                if (basemapId === "satellite" && CesiumGlobal.ArcGisMapServerImageryProvider?.fromUrl) {
                  try {
                    newProvider = await CesiumGlobal.ArcGisMapServerImageryProvider.fromUrl(
                      "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer",
                      {
                        credit: "Powered by Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community",
                        enablePickFeatures: false,
                      }
                    )
                  } catch (eArc) {
                    console.warn("[GlobeView] ArcGisMapServerImageryProvider switch fallback:", eArc)
                  }
                }

                if (!newProvider) {
                  const resolvedUrl = tileUrl || preset?.tileUrl || BASEMAP_PRESETS.satellite.tileUrl
                  newProvider = new CesiumGlobal.UrlTemplateImageryProvider({
                    url: resolvedUrl,
                    credit: credit,
                    maximumLevel: preset?.maxZoom || 18,
                  })
                }

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
                const coords = geom.coordinates ? (geom.coordinates[0] || []) : []
                const flatHierarchy = coords.flatMap((pt: [number, number]) => [pt[0], pt[1]])
                if (flatHierarchy.length >= 6) {
                  // Semi-transparent glowing cyan polygon fill
                  viewerRef.current.entities.add({
                    id: "trinetra-aoi-entity",
                    polygon: {
                      hierarchy: CesiumGlobal.Cartesian3.fromDegreesArray(flatHierarchy),
                      material: CesiumGlobal.Color.fromCssColorString("#06b6d4").withAlpha(0.22),
                      height: 0,
                    },
                  })
                  // Sharp vibrant cyan boundary border clamped to ground
                  viewerRef.current.entities.add({
                    id: "trinetra-aoi-outline",
                    polyline: {
                      positions: CesiumGlobal.Cartesian3.fromDegreesArray(flatHierarchy),
                      width: 3.5,
                      material: CesiumGlobal.Color.fromCssColorString("#22d3ee"),
                      clampToGround: true,
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
              const existingPoly = viewerRef.current.entities.getById("trinetra-aoi-entity")
              if (existingPoly) viewerRef.current.entities.remove(existingPoly)
              const existingOutline = viewerRef.current.entities.getById("trinetra-aoi-outline")
              if (existingOutline) viewerRef.current.entities.remove(existingOutline)
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

          // Subscribe to GlobeCommandBus for focus and AOI
          const unsubBus = globeCommandBus.subscribe((cmd) => {
            if (!viewerRef.current || !Cesium) return
            if (cmd.type === "FOCUS_ANALYSIS_REGION" && cmd.bounds && cmd.bounds.length === 4) {
              const b = cmd.bounds
              viewerRef.current.camera.flyTo({
                destination: Cesium.Rectangle.fromDegrees(b[0], b[1], b[2], b[3]),
                duration: 1.5,
              })
            } else if (cmd.type === "SET_AOI") {
              adapter.setAOI?.(cmd.geometry)
            } else if (cmd.type === "CLEAR_AOI") {
              adapter.clearAOI?.()
            }
          })

          // Save unsub function on viewer for unmount
          ;(viewerRef.current as any).__unsubBus = unsubBus
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

  return (
    <div className="globe-container" ref={containerRef} style={{ width: "100%", height: "100%" }} />
  )
}
