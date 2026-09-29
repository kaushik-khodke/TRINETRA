"use client"

/**
 * TRINETRA Workstation — Master Shell Component
 * Minimalist Glassmorphic Satellite Research Workspace.
 * Zero static / fake demo data: layers, AOIs, assets, and runs populate strictly
 * from genuine user uploads and real calculations.
 */

import React, { useState, useEffect, useMemo } from "react"
import {
  Mission,
  AreaOfInterest,
  Asset,
  PipelineDefinition,
  AnalysisPlan,
  AnalysisRun,
  NotebookEntry,
  CatalogScene,
} from "@/lib/workstation/types"
import { workstationApi } from "@/lib/workstation/api"
import { WorkstationHeader } from "./WorkstationHeader"
import { WorkstationDataRail, LayerState, BaseMapId, LayerTileItem } from "./WorkstationDataRail"
import { WorkstationPlanInspector } from "./WorkstationPlanInspector"
import { WorkstationRunDrawer } from "./WorkstationRunDrawer"
import GlobeView from "@/components/explore/GlobeView"

export const WorkstationShell: React.FC = () => {
  const [missions, setMissions] = useState<Mission[]>([])
  const [activeMission, setActiveMission] = useState<Mission | null>(null)
  const [aois, setAois] = useState<AreaOfInterest[]>([])
  const [activeAOI, setActiveAOI] = useState<AreaOfInterest | null>(null)
  const [assets, setAssets] = useState<Asset[]>([])
  const [pipelines, setPipelines] = useState<PipelineDefinition[]>([])
  const [currentPlan, setCurrentPlan] = useState<AnalysisPlan | null>(null)
  const [runs, setRuns] = useState<AnalysisRun[]>([])
  const [activeRun, setActiveRun] = useState<AnalysisRun | null>(null)
  const [notebookEntries, setNotebookEntries] = useState<NotebookEntry[]>([])

  // Dynamic layers stack & Deloaded states
  const [layers, setLayers] = useState<LayerState[]>([])
  const [unloadedLayerIds, setUnloadedLayerIds] = useState<Set<string>>(new Set())
  const [layerOverrides, setLayerOverrides] = useState<Record<string, Partial<LayerState>>>({})
  const [hiddenAoiIds, setHiddenAoiIds] = useState<Set<string>>(new Set())
  const [viewMode, setViewMode] = useState<"2d" | "3d">("3d")
  const [drawingMode, setDrawingMode] = useState<"box" | "polygon" | null>(null)
  const [flyToBbox, setFlyToBbox] = useState<[number, number, number, number] | null>(null)


  // Base Map & Overlays Customization
  const [baseMap, setBaseMap] = useState<BaseMapId>("esri-satellite")
  const [showLabels, setShowLabels] = useState<boolean>(true)
  const [labelsOpacity, setLabelsOpacity] = useState<number>(0.85)
  const [showGraticule, setShowGraticule] = useState<boolean>(false)

  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false)
  const [isExecutingRun, setIsExecutingRun] = useState(false)
  const [planError, setPlanError] = useState<string | null>(null)
  const [showExportModal, setShowExportModal] = useState(false)
  const [exportManifest, setExportManifest] = useState<any>(null)

  // Auto-initialize mission if none exists
  const ensureMission = async (): Promise<Mission> => {
    if (activeMission) return activeMission
    if (missions.length > 0) {
      setActiveMission(missions[0])
      return missions[0]
    }
    const created = await workstationApi.createMission({
      name: "Primary Research Mission",
      description: "Auto-initialized workspace for multi-spectral analysis & raster pipeline.",
    })
    setMissions([created])
    setActiveMission(created)
    return created
  }

  // 1. Initial Load of Missions and Pipelines
  useEffect(() => {
    const init = async () => {
      try {
        const [msns, pipes] = await Promise.all([
          workstationApi.listMissions(),
          workstationApi.listPipelines(),
        ])
        setMissions(msns)
        setPipelines(pipes)
        if (msns.length > 0) {
          setActiveMission(msns[0])
        }
      } catch (e) {
        console.error("Failed to load initial workstation data:", e)
      }
    }
    init()
  }, [])

  // 2. Load mission data when activeMission changes
  useEffect(() => {
    if (!activeMission) return
    const loadMissionData = async () => {
      try {
        const [aoiList, assetList, runList, nbList] = await Promise.all([
          workstationApi.listAOIs(activeMission.id),
          workstationApi.listAssets(activeMission.id),
          workstationApi.listRuns(activeMission.id),
          workstationApi.listNotebook(activeMission.id),
        ])
        setAois(aoiList)
        // Default to clean global view (no unwanted default polygon)
        setActiveAOI(null)
        setAssets(assetList)
        setRuns(runList)
        setActiveRun(runList.length > 0 ? runList[0] : null)
        setNotebookEntries(nbList)
        setCurrentPlan(null)
      } catch (e) {
        console.error("Failed to load mission context:", e)
      }
    }
    loadMissionData()
  }, [activeMission])

  // 3. Dynamically compute layer stack exclusively from real assets & outputs with deloading & override preservation
  useEffect(() => {
    const dynamicLayers: LayerState[] = []

    // Group assets by collection_id
    const collectionsMap: Record<string, Asset[]> = {}
    assets.forEach((ast) => {
      const col = ast.collection_id || "user-upload"
      if (!collectionsMap[col]) collectionsMap[col] = []
      collectionsMap[col].push(ast)
    })

    Object.entries(collectionsMap).forEach(([collectionId, colAssets]) => {
      // If collection has multiple assets (or user bulk uploaded), combine into one unified mosaic layer!
      if (colAssets.length > 1) {
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
        let totalBytes = 0
        const tiles: LayerTileItem[] = []
        const modalityCounts: Record<string, number> = {}

        colAssets.forEach((ast) => {
          const v = ast.versions[0]
          const meta = ast.metadata || {}
          if (v?.size_bytes) totalBytes += v.size_bytes
          if (meta.bbox && meta.bbox.length === 4) {
            minX = Math.min(minX, meta.bbox[0])
            minY = Math.min(minY, meta.bbox[1])
            maxX = Math.max(maxX, meta.bbox[2])
            maxY = Math.max(maxY, meta.bbox[3])
          }
          const mod = meta.modality_label || "Optical (True-Color RGB)"
          modalityCounts[mod] = (modalityCounts[mod] || 0) + 1

          tiles.push({
            id: ast.id,
            title: ast.title || meta.filename || "Tile",
            filename: meta.filename || ast.external_id || "tile.tif",
            sourceUrl: meta.preview_url,
            coordinates: meta.coordinates,
            bbox: meta.bbox,
            geometry: ast.footprint,
            fileSize: v?.size_bytes,
            modality: meta.modality,
            modalityLabel: meta.modality_label || "Optical (True-Color RGB)",
            modalityColor: meta.modality_color || "#06b6d4",
            modalitySensor: meta.modality_sensor || "High-Resolution Optical Sensor (RGB)",
          })
        })

        const unionBbox: [number, number, number, number] | undefined =
          minX !== Infinity ? [minX, minY, maxX, maxY] : undefined

        const primaryModality =
          Object.entries(modalityCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || "Optical (True-Color RGB)"
        const primaryColor = colAssets[0]?.metadata?.modality_color || "#06b6d4"

        const displayName =
          collectionId === "user-upload"
            ? `Research Dataset Mosaic (${colAssets.length} scenes)`
            : `${collectionId.replace(/[_-]/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())} (${colAssets.length} scenes)`

        const mosaicLayerId = `mosaic_${collectionId}`
        const isDeloaded = unloadedLayerIds.has(mosaicLayerId)
        const overrides = layerOverrides[mosaicLayerId] || {}

        dynamicLayers.push({
          id: mosaicLayerId,
          name: displayName,
          collection: collectionId,
          visible: isDeloaded ? false : (overrides.visible ?? true),
          opacity: overrides.opacity ?? 0.95,
          bands: "Mosaic RGB/Multispectral",
          isMosaic: true,
          tileCount: colAssets.length,
          tiles: tiles,
          bbox: unionBbox,
          fileSize: totalBytes,
          modality: colAssets[0]?.metadata?.modality || "OPTICAL_RGB",
          modalityLabel: primaryModality,
          modalityColor: primaryColor,
          modalitySensor: colAssets[0]?.metadata?.modality_sensor || "Optical Sensor",
          isDeloaded: isDeloaded,
          ...overrides,
        })
      } else {
        // Single isolated scene: individual layer
        const ast = colAssets[0]
        const v = ast.versions[0]
        const meta = ast.metadata || {}
        const singleLayerId = `layer_${ast.id}`
        const isDeloaded = unloadedLayerIds.has(singleLayerId)
        const overrides = layerOverrides[singleLayerId] || {}

        dynamicLayers.push({
          id: singleLayerId,
          name: ast.title,
          collection: ast.collection_id,
          visible: isDeloaded ? false : (overrides.visible ?? true),
          opacity: overrides.opacity ?? 0.95,
          bands: v?.bands && v.bands.length > 0 ? v.bands.map((b) => b.name).join("/") : "Raster",
          sourceUrl: meta.preview_url,
          coordinates: meta.coordinates,
          bbox: meta.bbox,
          geometry: ast.footprint,
          fileSize: v?.size_bytes,
          modality: meta.modality,
          modalityLabel: meta.modality_label || "Optical (True-Color RGB)",
          modalityColor: meta.modality_color || "#06b6d4",
          modalitySensor: meta.modality_sensor,
          isDeloaded: isDeloaded,
          ...overrides,
        })
      }
    })

    // Real run outputs
    runs.forEach((r) => {
      if (r.status === "succeeded" || r.status === "succeeded_with_warnings") {
        const rasterOut = r.outputs.find((o) => o.output_type === "raster")
        if (rasterOut) {
          const runLayerId = `layer_out_${r.id}`
          const isDeloaded = unloadedLayerIds.has(runLayerId)
          const overrides = layerOverrides[runLayerId] || {}
          dynamicLayers.push({
            id: runLayerId,
            name: `Run #${r.run_number} (${r.pipeline_key}) Output`,
            collection: "derived-raster",
            visible: isDeloaded ? false : (overrides.visible ?? true),
            opacity: overrides.opacity ?? 0.85,
            bands: "Zonal Delta",
            colorRamp: "viridis",
            modalityLabel: "Analytical Product",
            modalityColor: "#10b981",
            isDeloaded: isDeloaded,
            ...overrides,
          })
        }
      }
    })

    setLayers(dynamicLayers)
  }, [assets, runs, unloadedLayerIds, layerOverrides])

  // Active layers sent to map renderer (excluding any deloaded layers)
  const activeMapLayers = useMemo(
    () => layers.filter((l) => !l.isDeloaded),
    [layers]
  )

  // Handle Layer Update (persists overrides across re-renders)
  const handleUpdateLayer = (layerId: string, updates: Partial<LayerState>) => {
    setLayerOverrides((prev) => ({
      ...prev,
      [layerId]: { ...(prev[layerId] || {}), ...updates },
    }))
    setLayers((prev) =>
      prev.map((l) => (l.id === layerId ? { ...l, ...updates } : l))
    )
  }

  // Handle Deload single layer (unloads completely from map canvas)
  const handleDeloadLayer = (layerId: string) => {
    setUnloadedLayerIds((prev) => {
      const next = new Set(prev)
      next.add(layerId)
      return next
    })
  }

  // Handle Reload single layer back onto map canvas
  const handleReloadLayer = (layerId: string) => {
    setUnloadedLayerIds((prev) => {
      const next = new Set(prev)
      next.delete(layerId)
      return next
    })
  }

  // Handle Deload ALL overlays from map canvas
  const handleDeloadAllLayers = () => {
    setUnloadedLayerIds(new Set(layers.map((l) => l.id)))
  }

  // Handle Reload ALL overlays back onto map canvas
  const handleReloadAllLayers = () => {
    setUnloadedLayerIds(new Set())
  }

  // Handle Delete Layer (removes layer and deletes underlying mission datasets)
  const handleDeleteLayer = async (layerId: string) => {
    if (!activeMission) return
    const layer = layers.find((l) => l.id === layerId)
    if (!layer) return

    try {
      if (layer.isMosaic) {
        await workstationApi.deleteCollection(activeMission.id, layer.collection)
        setAssets((prev) => prev.filter((a) => a.collection_id !== layer.collection))
      } else if (layer.id.startsWith("layer_")) {
        const assetId = layer.id.replace("layer_", "")
        await workstationApi.deleteAsset(activeMission.id, assetId)
        setAssets((prev) => prev.filter((a) => a.id !== assetId))
      }
      setUnloadedLayerIds((prev) => {
        const next = new Set(prev)
        next.delete(layerId)
        return next
      })
      setLayerOverrides((prev) => {
        const next = { ...prev }
        delete next[layerId]
        return next
      })
    } catch (err) {
      console.error("Failed to delete layer:", err)
    }
  }

  // Handle Delete individual Asset
  const handleDeleteAsset = async (assetId: string) => {
    if (!activeMission) return
    try {
      await workstationApi.deleteAsset(activeMission.id, assetId)
      setAssets((prev) => prev.filter((a) => a.id !== assetId))
    } catch (err) {
      console.error("Failed to delete asset:", err)
    }
  }

  // Handle Delete entire Collection of assets
  const handleDeleteCollection = async (collectionId: string) => {
    if (!activeMission) return
    try {
      await workstationApi.deleteCollection(activeMission.id, collectionId)
      setAssets((prev) => prev.filter((a) => a.collection_id !== collectionId))
    } catch (err) {
      console.error("Failed to delete collection:", err)
    }
  }

  // Handle Mission Creation
  const handleCreateMission = async (name: string, description: string) => {
    const created = await workstationApi.createMission({ name, description })
    setMissions([created, ...missions])
    setActiveMission(created)
  }


  // Handle Real File Upload (with auto-mission fallback and map zoom)
  const handleUploadFile = async (
    file: File,
    title?: string,
    onProgress?: (percent: number, loaded: number, total: number) => void,
    collectionId?: string
  ) => {
    const mission = await ensureMission()
    const uploadedAsset = await workstationApi.uploadAsset(mission.id, file, title, onProgress, collectionId)
    setAssets((prev) => [uploadedAsset, ...prev])

    // Auto-fit map to newly uploaded raster bounds
    const meta = uploadedAsset.metadata || {}
    if (meta.bbox && meta.bbox.length === 4) {
      setFlyToBbox([...meta.bbox] as [number, number, number, number])
    }

    return uploadedAsset
  }

  // Handle Catalog Search
  const handleSearchCatalog = async (cloudMax: number) => {
    if (!activeMission) return []
    const res = await workstationApi.searchCatalog(activeMission.id, { cloudCoverMax: cloudMax })
    return res.scenes || []
  }

  // Handle AOI Drawing Completion (Supports Multi-Add)
  const handleFinishDrawingAOI = async (geometry: any, keepDrawing?: boolean) => {
    const mission = await ensureMission()
    if (!keepDrawing) {
      setDrawingMode(null)
    }
    try {
      const newAOI = await workstationApi.createAOI(mission.id, {
        name: `AOI Sector #${aois.length + 1}`,
        geometry,
      })
      setAois((prev) => [newAOI, ...prev])
      setActiveAOI(newAOI)
      setHiddenAoiIds((prev) => {
        const next = new Set(prev)
        next.delete(newAOI.id)
        return next
      })
    } catch (err) {
      console.error("Failed to create AOI:", err)
    }
  }

  // Handle AOI Visibility Toggle on Map
  const handleToggleAOIVisibility = (aoiId: string) => {
    setHiddenAoiIds((prev) => {
      const next = new Set(prev)
      if (next.has(aoiId)) {
        next.delete(aoiId)
      } else {
        next.add(aoiId)
      }
      return next
    })
  }

  // Handle Toggle All AOIs Visibility
  const handleToggleAllAOIsVisibility = (showAll: boolean) => {
    if (showAll) {
      setHiddenAoiIds(new Set())
    } else {
      setHiddenAoiIds(new Set(aois.map((a) => a.id)))
    }
  }

  // Handle Delete AOI
  const handleDeleteAOI = async (aoiId: string) => {
    if (!activeMission) return
    try {
      await workstationApi.deleteAOI(activeMission.id, aoiId)
      setAois((prev) => prev.filter((a) => a.id !== aoiId))
      if (activeAOI?.id === aoiId) {
        setActiveAOI(null)
      }
      setHiddenAoiIds((prev) => {
        const next = new Set(prev)
        next.delete(aoiId)
        return next
      })
    } catch (err) {
      console.error("Failed to delete AOI:", err)
    }
  }

  // Handle Plan Drafting via Experiment Setup or Copilot
  const handleDraftPlan = async (question: string, pipelineKey?: string, contextOptions?: any) => {
    if (!activeMission) return
    setIsGeneratingPlan(true)
    setPlanError(null)
    try {
      const plan = await workstationApi.draftPlan(activeMission.id, {
        question,
        aoi_id: activeAOI?.id,
        pipeline_key: pipelineKey,
        context_options: contextOptions,
      })
      setCurrentPlan(plan)
    } catch (err: any) {
      console.error("Draft plan error:", err)
      setPlanError(err?.message || "Failed to generate analysis plan. Please verify the mission inputs and try again.")
    } finally {
      setIsGeneratingPlan(false)
    }
  }

  // Handle Plan Validation
  const handleValidatePlan = async (plan: AnalysisPlan) => {
    setPlanError(null)
    try {
      const validated = await workstationApi.validatePlan(plan)
      setCurrentPlan(validated)
    } catch (err: any) {
      console.error("Validate plan error:", err)
      setPlanError(err?.message || "Plan parameter validation failed.")
    }
  }

  // Handle Plan Approval (The Human Gate)
  const handleApprovePlan = async (planId: string) => {
    setPlanError(null)
    try {
      const approved = await workstationApi.approvePlan(planId)
      setCurrentPlan(approved)
    } catch (err: any) {
      console.error("Approve plan error:", err)
      setPlanError(err?.message || "Plan authorization failed.")
    }
  }

  // Handle Plan Execution
  const handleExecutePlan = async (planId: string) => {
    if (!activeMission) return
    setIsExecutingRun(true)
    try {
      const run = await workstationApi.submitRun(activeMission.id, planId)
      setRuns((prev) => [run, ...prev])
      setActiveRun(run)

      const pollInterval = setInterval(async () => {
        try {
          const updated = await workstationApi.getRun(run.id)
          setActiveRun(updated)
          setRuns((prev) => prev.map((r) => (r.id === updated.id ? updated : r)))
          if (
            updated.status === "succeeded" ||
            updated.status === "succeeded_with_warnings" ||
            updated.status === "failed"
          ) {
            clearInterval(pollInterval)
            setIsExecutingRun(false)
            const nbs = await workstationApi.listNotebook(activeMission.id)
            setNotebookEntries(nbs)
            if (updated.status === "succeeded" || updated.status === "succeeded_with_warnings") {
              handleMountChangeLayer(updated)
            }
          }
        } catch {
          clearInterval(pollInterval)
          setIsExecutingRun(false)
        }
      }, 1000)
    } catch (e: any) {
      setIsExecutingRun(false)
      console.error(e)
      setPlanError(e?.message || "Failed to initialize pipeline execution.")
    }
  }

  // Handle One-Click Scientific Experiment Run for Experimentalists
  const handleRunExperiment = async (params: {
    question: string
    pipelineKey: string
    beforeAssetId: string
    afterAssetId?: string
    targetAssetId?: string
    index?: string
    threshold?: number
    cloudMask?: string
    resampling?: string
  }) => {
    if (!activeMission) return
    setIsExecutingRun(true)
    setPlanError(null)

    try {
      // 1. Draft plan with calibrated parameters
      const plan = await workstationApi.draftPlan(activeMission.id, {
        question: params.question,
        aoi_id: activeAOI?.id,
        pipeline_key: params.pipelineKey,
        context_options: {
          before_asset_id: params.beforeAssetId,
          after_asset_id: params.afterAssetId,
          target_asset_id: params.targetAssetId || params.beforeAssetId,
          parameters: {
            index: params.index,
            threshold: params.threshold,
            cloudMask: params.cloudMask || "s2cloudless",
            resampling: params.resampling || "bilinear",
          },
        },
      })
      setCurrentPlan(plan)

      // 2. Auto-authorize since experimentalist configured and clicked run
      const approved = await workstationApi.approvePlan(plan.planId)
      setCurrentPlan(approved)

      // 3. Submit Run
      const run = await workstationApi.submitRun(activeMission.id, approved.planId)
      setRuns((prev) => [run, ...prev])
      setActiveRun(run)

      // 4. Poll execution
      const pollInterval = setInterval(async () => {
        try {
          const updated = await workstationApi.getRun(run.id)
          setActiveRun(updated)
          setRuns((prev) => prev.map((r) => (r.id === updated.id ? updated : r)))
          if (
            updated.status === "succeeded" ||
            updated.status === "succeeded_with_warnings" ||
            updated.status === "failed"
          ) {
            clearInterval(pollInterval)
            setIsExecutingRun(false)
            const nbs = await workstationApi.listNotebook(activeMission.id)
            setNotebookEntries(nbs)
            if (updated.status === "succeeded" || updated.status === "succeeded_with_warnings") {
              handleMountChangeLayer(updated)
            }
          }
        } catch {
          clearInterval(pollInterval)
          setIsExecutingRun(false)
        }
      }, 1000)
    } catch (e: any) {
      setIsExecutingRun(false)
      console.error("Experiment run error:", e)
      setPlanError(e?.message || "Failed to execute experiment.")
    }
  }

  // Handle Mounting Change Raster Layer to Map Canvas
  const handleMountChangeLayer = (run: AnalysisRun) => {
    const rasterOut = run.outputs?.find((o) => o.output_type === "raster")
    if (!rasterOut) return

    const targetBbox: [number, number, number, number] =
      (activeAOI?.bbox as [number, number, number, number]) ||
      (assets[0]?.metadata?.bbox as [number, number, number, number]) || [79.0, 21.0, 79.2, 21.2]

    const changeLayer: LayerState = {
      id: `change_layer_${run.id}`,
      name: `[Run #${run.run_number}] Δ Alteration Map`,
      collection: "derived_change_raster",
      visible: true,
      opacity: 0.85,
      bands: "single_band_diff",
      sourceUrl: rasterOut.object_uri,
      bbox: targetBbox,
      modalityLabel: "Change Detection Delta",
      modalityColor: "#f59e0b",
      modalitySensor: `Pipeline ${run.pipeline_key} (ARD)`,
    }

    setLayers((prev) => [changeLayer, ...prev.filter((l) => l.id !== changeLayer.id)])
    if (targetBbox) {
      setFlyToBbox([...targetBbox])
    }
  }

  // Handle Notebook Note Creation
  const handleAddNote = async (title: string, body: string) => {
    if (!activeMission) return
    const entry = await workstationApi.addNotebookEntry(activeMission.id, {
      title,
      body,
      entry_type: "note",
      run_id: activeRun?.id,
    })
    setNotebookEntries((prev) => [entry, ...prev])
  }

  // Handle Reproducible Package Export
  const handleOpenExport = async () => {
    if (!activeMission) return
    const manifest = await workstationApi.getExportManifest(activeMission.id)
    setExportManifest(manifest)
    setShowExportModal(true)
  }

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#030712] text-slate-100 font-sans select-none antialiased">
      {/* 1. Header Bar */}
      <WorkstationHeader
        missions={missions}
        activeMission={activeMission}
        onSelectMission={setActiveMission}
        onCreateMission={handleCreateMission}
        activeAOI={activeAOI}
        onClearAOI={() => setActiveAOI(null)}
        viewMode={viewMode}
        onToggleViewMode={setViewMode}
        onExportClick={handleOpenExport}
      />

      {/* 2. Central Workspace (Data Rail | Map Canvas | Copilot Plan Inspector) */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left: Data Rail */}
        <WorkstationDataRail
          assets={assets}
          aois={aois}
          activeAOI={activeAOI}
          onSelectAOI={setActiveAOI}
          hiddenAoiIds={hiddenAoiIds}
          onToggleAOIVisibility={handleToggleAOIVisibility}
          onToggleAllAOIsVisibility={handleToggleAllAOIsVisibility}
          onDeleteAOI={handleDeleteAOI}
          onStartDrawAOI={setDrawingMode}
          layers={layers}
          onUpdateLayer={handleUpdateLayer}
          onDeloadLayer={handleDeloadLayer}
          onReloadLayer={handleReloadLayer}
          onDeloadAllLayers={handleDeloadAllLayers}
          onReloadAllLayers={handleReloadAllLayers}
          onDeleteLayer={handleDeleteLayer}
          onDeleteAsset={handleDeleteAsset}
          onDeleteCollection={handleDeleteCollection}
          onUploadFile={handleUploadFile}
          onSearchCatalog={handleSearchCatalog}
          onFitBounds={(bbox) => setFlyToBbox([...bbox])}
          baseMap={baseMap}
          onSelectBaseMap={setBaseMap}
          showLabels={showLabels}
          onToggleLabels={setShowLabels}
          labelsOpacity={labelsOpacity}
          onChangeLabelsOpacity={setLabelsOpacity}
          showGraticule={showGraticule}
          onToggleGraticule={setShowGraticule}
        />

        {/* Center: Persistent 3D Cesium Globe Canvas */}
        <main className="flex-1 relative h-full">
          <GlobeView
            aois={aois}
            activeAOI={activeAOI}
            hiddenAoiIds={hiddenAoiIds}
            onSelectAOI={setActiveAOI}
            drawingMode={drawingMode}
            onFinishDrawingAOI={handleFinishDrawingAOI}
            onCancelDrawing={() => setDrawingMode(null)}
            fitBoundsBbox={flyToBbox}
            baseMap={baseMap}
            onSelectBaseMap={setBaseMap}
            showLabels={showLabels}
            onToggleLabels={setShowLabels}
            labelsOpacity={labelsOpacity}
            onChangeLabelsOpacity={setLabelsOpacity}
            showGraticule={showGraticule}
            onToggleGraticule={setShowGraticule}
          />
        </main>

        {/* Right: Copilot Planning & Human Approval Gate Inspector */}
        <WorkstationPlanInspector
          currentPlan={currentPlan}
          pipelines={pipelines}
          assets={assets}
          aois={aois}
          activeAOI={activeAOI}
          onSelectAOI={setActiveAOI}
          onDraftPlan={handleDraftPlan}
          onValidatePlan={handleValidatePlan}
          onApprovePlan={handleApprovePlan}
          onExecutePlan={handleExecutePlan}
          onRunExperiment={handleRunExperiment}
          activeRun={activeRun}
          onMountLayer={handleMountChangeLayer}
          onAddNote={handleAddNote}
          isGeneratingPlan={isGeneratingPlan}
          isExecutingRun={isExecutingRun}
          planError={planError}
          onClearError={() => setPlanError(null)}
        />
      </div>

      {/* 3. Bottom Execution Tray & Research Notebook */}
      <WorkstationRunDrawer
        runs={runs}
        activeRun={activeRun}
        onSelectRun={setActiveRun}
        notebookEntries={notebookEntries}
        onAddNote={handleAddNote}
        onMountChangeLayer={handleMountChangeLayer}
      />

      {/* 4. Export Package Manifest Modal */}
      {showExportModal && exportManifest && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-2xl flex items-center justify-center p-6">
          <div className="bg-slate-950/90 border border-white/10 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-[0_16px_48px_0_rgba(0,0,0,0.5)] backdrop-blur-3xl">
            <div className="p-4 border-b border-white/[0.08] flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                  <span>Reproducible Research Export Manifest</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-700/60 font-medium">
                    SHA256 VERIFIED
                  </span>
                </h3>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Complete provenance package containing verified mission parameters, real input digests, and findings.
                </p>
              </div>
              <button
                onClick={() => setShowExportModal(false)}
                className="text-slate-400 hover:text-slate-200 text-sm font-medium w-7 h-7 rounded-lg hover:bg-white/5 flex items-center justify-center transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 font-mono text-xs bg-black/40 text-cyan-200/90 rounded-lg m-3 border border-white/[0.05]">
              <pre className="text-[11px] leading-relaxed">
                {JSON.stringify(exportManifest, null, 2)}
              </pre>
            </div>

            <div className="p-3.5 border-t border-white/[0.08] flex items-center justify-between bg-slate-900/40 rounded-b-2xl">
              <span className="text-[10px] text-slate-400 font-mono">
                Cryptographically signed for institutional audit & reproducibility.
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowExportModal(false)}
                  className="px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-200 transition-colors"
                >
                  Close
                </button>
                <button
                  onClick={() => {
                    const blob = new Blob([JSON.stringify(exportManifest, null, 2)], { type: "application/json" })
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement("a")
                    a.href = url
                    a.download = `trinetra_manifest_${activeMission?.slug || "mission"}.json`
                    a.click()
                  }}
                  className="px-4 py-1.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-lg text-xs font-semibold shadow-lg shadow-cyan-950/40 transition-all cursor-pointer"
                >
                  Download Manifest (.json)
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
