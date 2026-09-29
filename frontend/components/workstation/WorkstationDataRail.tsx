"use client"

/**
 * TRINETRA Workstation — Data Rail & Layer Control System
 * Supports Bulk Folder/Multi-file Uploads, Unified Mosaic Layers with single Opacity Slider,
 * EO Modality (Optical, RGB, SAR, DEM) Badges, Basemap & Overlay Switchers, and Scalable 772-Tile Browser.
 */

import React, { useState, useRef, useMemo } from "react"
import { Asset, AreaOfInterest, CatalogScene } from "@/lib/workstation/types"
import {
  Layers,
  Search,
  Sliders,
  Eye,
  EyeOff,
  Cloud,
  Folder,
  FolderUp,
  Square,
  CheckCircle2,
  FileCheck,
  ChevronLeft,
  ChevronRight,
  Filter,
  FileUp,
  Inbox,
  Crosshair,
  Loader2,
  Maximize2,
  HardDrive,
  Globe,
  Map as MapIcon,
  Sun,
  Moon,
  Mountain,
  Grid,
  ChevronDown,
  Sparkles,
  Radar,
  MountainSnow,
  Palette,
  ExternalLink,
  Trash2,
  X,
  Plus,
  MinusCircle,
  PlusCircle,
  FolderX,
} from "lucide-react"

export type BaseMapId =
  | "esri-satellite"
  | "carto-dark"
  | "carto-positron"
  | "osm-standard"
  | "esri-topo"
  | "blank-canvas"

export interface BaseMapOption {
  id: BaseMapId
  label: string
  subtitle: string
  tag: string
}

export const BASE_MAP_OPTIONS: BaseMapOption[] = [
  { id: "esri-satellite", label: "Esri Satellite", subtitle: "High-res optical orbital imagery", tag: "EO Satellite" },
  { id: "carto-dark", label: "Dark Matter", subtitle: "Deep high-contrast backdrop", tag: "Night Mode" },
  { id: "carto-positron", label: "Positron", subtitle: "Clean light minimalist canvas", tag: "Light" },
  { id: "osm-standard", label: "OpenStreetMap", subtitle: "Infrastructure & roads", tag: "Streets" },
  { id: "esri-topo", label: "Topographic", subtitle: "Contour elevation relief", tag: "Terrain" },
  { id: "blank-canvas", label: "Dark Canvas", subtitle: "Pure black grid (Rasters only)", tag: "Pure Data" },
]

export interface LayerTileItem {
  id: string
  title: string
  filename: string
  sourceUrl?: string
  coordinates?: [number, number][]
  bbox?: [number, number, number, number]
  geometry?: any
  fileSize?: number
  modality?: string
  modalityLabel?: string
  modalityColor?: string
  modalitySensor?: string
}

export interface LayerState {
  id: string
  name: string
  collection: string
  visible: boolean
  opacity: number
  bands: string
  colorRamp?: string
  sourceUrl?: string
  coordinates?: [number, number][]
  bbox?: [number, number, number, number]
  geometry?: any
  fileSize?: number
  modality?: string
  modalityLabel?: string
  modalityCategory?: string
  modalityColor?: string
  modalityBgColor?: string
  modalitySensor?: string
  isMosaic?: boolean
  tileCount?: number
  tiles?: LayerTileItem[]
  isDeloaded?: boolean
}

interface Props {
  assets: Asset[]
  aois: AreaOfInterest[]
  activeAOI: AreaOfInterest | null
  onSelectAOI: (aoi: AreaOfInterest | null) => void
  hiddenAoiIds?: Set<string>
  onToggleAOIVisibility?: (aoiId: string) => void
  onToggleAllAOIsVisibility?: (showAll: boolean) => void
  onDeleteAOI?: (aoiId: string) => Promise<void>
  onStartDrawAOI?: (type: "box" | "polygon") => void
  hideAoiTab?: boolean
  layers: LayerState[]
  onUpdateLayer: (layerId: string, updates: Partial<LayerState>) => void
  onDeloadLayer?: (layerId: string) => void
  onReloadLayer?: (layerId: string) => void
  onDeloadAllLayers?: () => void
  onReloadAllLayers?: () => void
  onDeleteLayer?: (layerId: string) => Promise<void>
  onDeleteAsset?: (assetId: string) => Promise<void>
  onDeleteCollection?: (collectionId: string) => Promise<void>
  onUploadFile: (
    file: File,
    title?: string,
    onProgress?: (percent: number, loaded: number, total: number) => void,
    collectionId?: string
  ) => Promise<any>
  onSearchCatalog: (cloudMax: number) => Promise<CatalogScene[]>
  onFitBounds?: (bbox: [number, number, number, number]) => void
  baseMap?: BaseMapId
  onSelectBaseMap?: (id: BaseMapId) => void
  showLabels?: boolean
  onToggleLabels?: (show: boolean) => void
  labelsOpacity?: number
  onChangeLabelsOpacity?: (val: number) => void
  showGraticule?: boolean
  onToggleGraticule?: (show: boolean) => void
}

type TabType = "layers" | "catalog" | "assets" | "aois"

export const WorkstationDataRail: React.FC<Props> = ({
  assets,
  aois,
  activeAOI,
  onSelectAOI,
  hiddenAoiIds = new Set(),
  onToggleAOIVisibility,
  onToggleAllAOIsVisibility,
  onDeleteAOI,
  onStartDrawAOI = () => {},
  hideAoiTab = false,
  layers,
  onUpdateLayer,
  onDeloadLayer,
  onReloadLayer,
  onDeloadAllLayers,
  onReloadAllLayers,
  onDeleteLayer,
  onDeleteAsset,
  onDeleteCollection,
  onUploadFile,
  onSearchCatalog,
  onFitBounds,
  baseMap = "esri-satellite",
  onSelectBaseMap,
  showLabels = true,
  onToggleLabels,
  labelsOpacity = 0.85,
  onChangeLabelsOpacity,
  showGraticule = false,
  onToggleGraticule,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>("layers")
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [cloudCoverMax, setCloudCoverMax] = useState(20)
  const [catalogScenes, setCatalogScenes] = useState<CatalogScene[]>([])
  const [isSearchingCatalog, setIsSearchingCatalog] = useState(false)

  // Bulk Upload State
  const [isUploading, setIsUploading] = useState(false)
  const [uploadFeedback, setUploadFeedback] = useState<string | null>(null)
  const [currentFileIndex, setCurrentFileIndex] = useState(0)
  const [totalBatchFiles, setTotalBatchFiles] = useState(0)
  const [currentFileName, setCurrentFileName] = useState("")
  const [currentFilePercent, setCurrentFilePercent] = useState(0)
  const [batchPercent, setBatchPercent] = useState(0)
  const [transferredInfo, setTransferredInfo] = useState("")

  // Mosaic tile accordion & search state
  const [expandedMosaics, setExpandedMosaics] = useState<Record<string, boolean>>({})
  const [mosaicTileSearch, setMosaicTileSearch] = useState<Record<string, string>>({})

  // Assets Tab Filter & Pagination
  const [assetFilter, setAssetFilter] = useState<string>("ALL")
  const [assetSearchQuery, setAssetSearchQuery] = useState("")
  const [assetPage, setAssetPage] = useState(1)
  const ASSETS_PER_PAGE = 25

  const fileInputRef = useRef<HTMLInputElement>(null)
  const folderInputRef = useRef<HTMLInputElement>(null)

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return "0 B"
    if (bytes >= 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const handleSearch = async () => {
    setIsSearchingCatalog(true)
    try {
      const results = await onSearchCatalog(cloudCoverMax)
      setCatalogScenes(results)
    } finally {
      setIsSearchingCatalog(false)
    }
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return
    await processBatchUpload(e.target.files)
  }

  const handleFolderChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return
    const files = Array.from(e.target.files)
    const folderName = files[0]?.webkitRelativePath?.split("/")[0] || "folder_mosaic"
    await processBatchUpload(files, folderName)
  }

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    if (!e.dataTransfer.files || e.dataTransfer.files.length === 0) return
    await processBatchUpload(e.dataTransfer.files)
  }

  const processBatchUpload = async (fileList: FileList | File[], folderCollectionId?: string) => {
    const files = Array.from(fileList).filter((f) =>
      /\.(tif|tiff|cog|geojson|json|hgt)$/i.test(f.name) ||
      f.type.includes("tiff") ||
      f.type.includes("image")
    )
    if (files.length === 0) {
      setUploadFeedback("Please select valid GeoTIFF / COG / GeoJSON satellite files.")
      setTimeout(() => setUploadFeedback(null), 4000)
      return
    }

    setIsUploading(true)
    setTotalBatchFiles(files.length)
    const totalBytes = files.reduce((acc, f) => acc + f.size, 0)
    let uploadedBytesBefore = 0
    const collectionName = folderCollectionId || (files.length > 1 ? `mosaic_${Date.now()}` : "user-upload")

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      setCurrentFileIndex(i + 1)
      setCurrentFileName(file.name)
      setCurrentFilePercent(0)
      setTransferredInfo(`0 MB / ${formatFileSize(file.size)}`)

      try {
        await onUploadFile(file, undefined, (percent, loaded) => {
          setCurrentFilePercent(percent)
          setTransferredInfo(`${formatFileSize(loaded)} / ${formatFileSize(file.size)}`)
          const currentTotal = uploadedBytesBefore + loaded
          setBatchPercent(Math.min(99, Math.round((currentTotal / totalBytes) * 100)))
        }, collectionName)
        uploadedBytesBefore += file.size
      } catch (err: any) {
        console.error("Upload error for file:", file.name, err)
        setUploadFeedback(`Error uploading ${file.name}: ${err.message}`)
      }
    }

    setBatchPercent(100)
    setUploadFeedback(
      `Ingested ${files.length} satellite raster${files.length > 1 ? "s" : ""} (${formatFileSize(totalBytes)}) into unified layer`
    )
    setIsUploading(false)
    setActiveTab("layers")
    if (fileInputRef.current) fileInputRef.current.value = ""
    if (folderInputRef.current) folderInputRef.current.value = ""
    setTimeout(() => setUploadFeedback(null), 6000)
  }

  // Split layers into active loaded layers vs deloaded layers
  const loadedLayers = useMemo(() => layers.filter((l) => !l.isDeloaded), [layers])
  const deloadedLayers = useMemo(() => layers.filter((l) => Boolean(l.isDeloaded)), [layers])

  // Filtered Assets for Tab 3
  const filteredAssets = useMemo(() => {
    return assets.filter((ast) => {
      const meta = ast.metadata || {}
      const mod = (meta.modality || "OPTICAL_RGB").toUpperCase()
      if (assetFilter !== "ALL") {
        if (assetFilter === "OPTICAL" && !mod.includes("OPTICAL")) return false
        if (assetFilter === "SAR" && !mod.includes("SAR")) return false
        if (assetFilter === "DEM" && !mod.includes("DEM")) return false
        if (assetFilter === "MULTISPECTRAL" && !mod.includes("MULTI")) return false
      }
      if (assetSearchQuery) {
        const q = assetSearchQuery.toLowerCase()
        const titleMatch = (ast.title || "").toLowerCase().includes(q)
        const fileMatch = (meta.filename || ast.external_id || "").toLowerCase().includes(q)
        return titleMatch || fileMatch
      }
      return true
    })
  }, [assets, assetFilter, assetSearchQuery])

  const paginatedAssets = useMemo(() => {
    const start = (assetPage - 1) * ASSETS_PER_PAGE
    return filteredAssets.slice(start, start + ASSETS_PER_PAGE)
  }, [filteredAssets, assetPage])

  const totalAssetPages = Math.ceil(filteredAssets.length / ASSETS_PER_PAGE) || 1

  if (isCollapsed) {
    return (
      <div className="w-12 bg-slate-950/60 border-r border-white/[0.08] backdrop-blur-2xl flex flex-col items-center py-3 select-none z-20">
        <button
          onClick={() => setIsCollapsed(false)}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-white/5 transition-colors cursor-pointer"
          title="Expand Rail"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
        <div className="flex flex-col gap-3 mt-4">
          <button
            onClick={() => {
              setIsCollapsed(false)
              setActiveTab("layers")
            }}
            className={`p-2 rounded-lg text-xs cursor-pointer transition-colors ${
              activeTab === "layers" ? "text-cyan-400 bg-white/[0.05]" : "text-slate-400 hover:text-slate-200"
            }`}
            title="Layers"
          >
            <Layers className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              setIsCollapsed(false)
              setActiveTab("catalog")
            }}
            className={`p-2 rounded-lg text-xs cursor-pointer transition-colors ${
              activeTab === "catalog" ? "text-cyan-400 bg-white/[0.05]" : "text-slate-400 hover:text-slate-200"
            }`}
            title="Catalog Discovery"
          >
            <Search className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              setIsCollapsed(false)
              setActiveTab("assets")
            }}
            className={`p-2 rounded-lg text-xs cursor-pointer transition-colors ${
              activeTab === "assets" ? "text-cyan-400 bg-white/[0.05]" : "text-slate-400 hover:text-slate-200"
            }`}
            title="Assets"
          >
            <HardDrive className="w-4 h-4" />
          </button>
          {!hideAoiTab && (
            <button
              onClick={() => {
                setIsCollapsed(false)
                setActiveTab("aois")
              }}
              className={`p-2 rounded-lg text-xs cursor-pointer transition-colors ${
                activeTab === "aois" ? "text-cyan-400 bg-white/[0.05]" : "text-slate-400 hover:text-slate-200"
              }`}
              title="AOIs"
            >
              <Square className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="w-full bg-slate-950/70 border-r border-white/[0.08] backdrop-blur-2xl flex flex-col h-full select-none z-20 transition-all text-slate-200">
      {/* Rail Navigation Tabs */}
      <div className="flex items-center justify-between border-b border-white/[0.08] px-3 pt-2">
        <div className="flex gap-1">
          <button
            onClick={() => setActiveTab("layers")}
            className={`flex items-center gap-1.5 px-2.5 py-2 text-xs font-medium border-b-2 cursor-pointer transition-colors ${
              activeTab === "layers"
                ? "border-cyan-400 text-cyan-300 bg-white/[0.02]"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Layers</span>
          </button>
          <button
            onClick={() => setActiveTab("catalog")}
            className={`flex items-center gap-1.5 px-2.5 py-2 text-xs font-medium border-b-2 cursor-pointer transition-colors ${
              activeTab === "catalog"
                ? "border-cyan-400 text-cyan-300 bg-white/[0.02]"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Search className="w-3.5 h-3.5" />
            <span>Catalog</span>
          </button>
          <button
            onClick={() => setActiveTab("assets")}
            className={`flex items-center gap-1.5 px-2.5 py-2 text-xs font-medium border-b-2 cursor-pointer transition-colors ${
              activeTab === "assets"
                ? "border-cyan-400 text-cyan-300 bg-white/[0.02]"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <HardDrive className="w-3.5 h-3.5" />
            <span>Assets</span>
            {assets.length > 0 && (
              <span className="text-[10px] font-mono px-1 rounded-full bg-cyan-950/80 text-cyan-300 border border-cyan-800/50">
                {assets.length}
              </span>
            )}
          </button>
          {!hideAoiTab && (
            <button
              onClick={() => setActiveTab("aois")}
              className={`flex items-center gap-1.5 px-2.5 py-2 text-xs font-medium border-b-2 cursor-pointer transition-colors ${
                activeTab === "aois"
                  ? "border-cyan-400 text-cyan-300 bg-white/[0.02]"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <Square className="w-3.5 h-3.5" />
              <span>AOIs</span>
            </button>
          )}
        </div>
        <button
          onClick={() => setIsCollapsed(true)}
          className="p-1 rounded-md text-slate-400 hover:text-slate-200 hover:bg-white/5 mb-1 cursor-pointer transition-colors"
          title="Collapse Rail"
        >
          <ChevronLeft className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-3.5 space-y-3.5">
        {/* Persistent Bulk & Folder Upload Action Bar */}
        <div className="bg-white/[0.02] border border-white/[0.08] hover:border-cyan-500/40 rounded-xl p-3 transition-all backdrop-blur-md">
          {/* File Picker */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".tif,.tiff,.geotiff,.cog,.geojson,.json"
            multiple
            className="hidden"
          />
          {/* Folder Picker */}
          <input
            type="file"
            ref={folderInputRef}
            onChange={handleFolderChange}
            {...({ webkitdirectory: "", directory: "" } as any)}
            multiple
            className="hidden"
          />

          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className="space-y-2.5"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                <FileUp className="w-3.5 h-3.5 text-cyan-400" />
                <span>Upload Imagery & Datasets</span>
              </span>
              <span className="text-[9px] font-mono text-cyan-400 uppercase bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-700/40">
                Up to 10 GB
              </span>
            </div>

            <p className="text-[10px] text-slate-400 leading-tight">
              Select individual GeoTIFF files or an entire folder of tiles. Bulk uploads are automatically merged into one unified mosaic layer.
            </p>

            {/* Action Buttons: Files vs Folder */}
            <div className="grid grid-cols-2 gap-2 pt-1">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 hover:border-cyan-400 text-cyan-300 text-xs font-medium cursor-pointer transition-all disabled:opacity-50"
              >
                <FileUp className="w-3.5 h-3.5 shrink-0" />
                <span>Select Files</span>
              </button>
              <button
                type="button"
                onClick={() => folderInputRef.current?.click()}
                disabled={isUploading}
                className="flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 hover:border-purple-400 text-purple-300 text-xs font-medium cursor-pointer transition-all disabled:opacity-50"
              >
                <FolderUp className="w-3.5 h-3.5 shrink-0" />
                <span>Select Folder</span>
              </button>
            </div>
          </div>

          {/* Active Upload Live Progress Meter */}
          {isUploading && (
            <div className="mt-3 pt-2.5 border-t border-white/[0.08] space-y-1.5">
              <div className="flex items-center justify-between text-[10px] font-mono">
                <span className="text-cyan-300 truncate max-w-[150px]">{currentFileName}</span>
                <span className="text-slate-400">{transferredInfo}</span>
              </div>
              <div className="w-full bg-white/[0.06] h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-cyan-400 h-full transition-all duration-300 shadow-[0_0_8px_rgba(6,182,212,0.8)]"
                  style={{ width: `${currentFilePercent}%` }}
                />
              </div>
              {totalBatchFiles > 1 && (
                <div className="flex items-center justify-between text-[9px] font-mono text-slate-400 pt-0.5">
                  <span>Tile {currentFileIndex} of {totalBatchFiles}</span>
                  <span>{batchPercent}% Overall</span>
                </div>
              )}
            </div>
          )}

          {uploadFeedback && !isUploading && (
            <div className="mt-2.5 p-2 rounded-lg bg-cyan-950/60 border border-cyan-700/50 text-cyan-200 text-xs flex items-center gap-2">
              <FileCheck className="w-3.5 h-3.5 shrink-0 text-cyan-400" />
              <span className="text-[10px] leading-tight font-mono">{uploadFeedback}</span>
            </div>
          )}
        </div>

        {/* TAB 1: LAYERS */}
        {activeTab === "layers" && (
          <div className="space-y-4">
            {/* 1. Base Map Selector */}
            <div className="p-3 bg-white/[0.02] border border-white/[0.08] rounded-xl space-y-2.5 backdrop-blur-md">
              <div className="flex items-center justify-between text-[10px] font-mono uppercase text-slate-400 font-medium">
                <span className="flex items-center gap-1.5">
                  <Palette className="w-3 h-3 text-cyan-400" />
                  <span>Base Map Canvas</span>
                </span>
                <span className="text-cyan-400 text-[9px] lowercase font-sans">
                  {BASE_MAP_OPTIONS.find((b) => b.id === baseMap)?.tag}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-1.5">
                {BASE_MAP_OPTIONS.map((opt) => {
                  const isActive = baseMap === opt.id
                  return (
                    <button
                      key={opt.id}
                      onClick={() => onSelectBaseMap?.(opt.id)}
                      className={`text-left p-2 rounded-lg border transition-all cursor-pointer ${
                        isActive
                          ? "bg-cyan-500/15 border-cyan-500/50 text-cyan-200 shadow-[0_0_10px_rgba(6,182,212,0.15)]"
                          : "bg-white/[0.02] border-white/[0.05] hover:bg-white/[0.05] text-slate-300"
                      }`}
                    >
                      <div className="text-[11px] font-semibold flex items-center justify-between">
                        <span>{opt.label}</span>
                        {isActive && <CheckCircle2 className="w-2.5 h-2.5 text-cyan-400" />}
                      </div>
                      <div className="text-[9px] text-slate-400 truncate mt-0.5">{opt.subtitle}</div>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* 2. Reference Overlays Configurator */}
            <div className="p-3 bg-white/[0.02] border border-white/[0.08] rounded-xl space-y-2.5 backdrop-blur-md">
              <div className="flex items-center justify-between text-[10px] font-mono uppercase text-slate-400 font-medium">
                <span className="flex items-center gap-1.5">
                  <MapIcon className="w-3 h-3 text-cyan-400" />
                  <span>Reference Overlays</span>
                </span>
              </div>

              {/* Labels & Boundaries Toggle + Opacity */}
              <div className="space-y-1.5 pt-1 border-t border-white/[0.04]">
                <div className="flex items-center justify-between text-xs">
                  <label className="flex items-center gap-2 cursor-pointer text-slate-200">
                    <input
                      type="checkbox"
                      checked={showLabels}
                      onChange={(e) => onToggleLabels?.(e.target.checked)}
                      className="accent-cyan-400 rounded cursor-pointer"
                    />
                    <span>Boundaries & Place Names</span>
                  </label>
                  <span className="font-mono text-[10px] text-slate-400">
                    {showLabels ? `${Math.round(labelsOpacity * 100)}%` : "Off"}
                  </span>
                </div>
                {showLabels && (
                  <input
                    type="range"
                    min="0.1"
                    max="1"
                    step="0.05"
                    value={labelsOpacity}
                    onChange={(e) => onChangeLabelsOpacity?.(parseFloat(e.target.value))}
                    className="w-full accent-cyan-400 h-1 bg-white/10 rounded-lg cursor-pointer"
                  />
                )}
              </div>

              {/* Graticule Grid Toggle */}
              <div className="flex items-center justify-between text-xs pt-1 border-t border-white/[0.04]">
                <label className="flex items-center gap-2 cursor-pointer text-slate-200">
                  <input
                    type="checkbox"
                    checked={showGraticule}
                    onChange={(e) => onToggleGraticule?.(e.target.checked)}
                    className="accent-cyan-400 rounded cursor-pointer"
                  />
                  <span>Lat/Lon Coordinate Graticule</span>
                </label>
                <span className="font-mono text-[10px] text-slate-400">{showGraticule ? "Active" : "Off"}</span>
              </div>
            </div>

            {/* 3. Research Satellite Rasters & Mosaics */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-[10px] font-mono uppercase text-slate-400 font-medium">
                <span className="flex items-center gap-1.5">
                  <Sliders className="w-3 h-3 text-cyan-400" />
                  <span>Active Map Layers ({loadedLayers.length})</span>
                </span>
                <div className="flex items-center gap-1">
                  {loadedLayers.length > 0 && onDeloadAllLayers && (
                    <button
                      onClick={onDeloadAllLayers}
                      className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono text-amber-300 bg-amber-950/40 hover:bg-amber-900/60 border border-amber-700/50 transition-all cursor-pointer"
                      title="Deload / Unload all overlays from map canvas"
                    >
                      <MinusCircle className="w-2.5 h-2.5" />
                      <span>Deload All</span>
                    </button>
                  )}
                  {deloadedLayers.length > 0 && onReloadAllLayers && (
                    <button
                      onClick={onReloadAllLayers}
                      className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono text-cyan-300 bg-cyan-950/40 hover:bg-cyan-900/60 border border-cyan-700/50 transition-all cursor-pointer"
                      title="Reload all overlays back onto map canvas"
                    >
                      <PlusCircle className="w-2.5 h-2.5" />
                      <span>Reload All</span>
                    </button>
                  )}
                </div>
              </div>

              {loadedLayers.map((layer) => {
                const isMosaic = Boolean(layer.isMosaic && layer.tiles && layer.tiles.length > 0)
                const isExpanded = Boolean(expandedMosaics[layer.id])
                const searchTerm = (mosaicTileSearch[layer.id] || "").toLowerCase()
                const visibleTiles = isMosaic
                  ? layer.tiles!.filter(
                      (t) => !searchTerm || t.filename.toLowerCase().includes(searchTerm) || t.title.toLowerCase().includes(searchTerm)
                    )
                  : []

                return (
                  <div
                    key={layer.id}
                    className={`rounded-xl border backdrop-blur-md transition-all overflow-hidden ${
                      layer.visible
                        ? "bg-white/[0.03] border-white/[0.1] shadow-sm"
                        : "bg-white/[0.01] border-white/[0.04] opacity-50"
                    }`}
                  >
                    <div className="p-3">
                      {/* Header with Modality Badge */}
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div className="flex items-start gap-2 min-w-0">
                          <button
                            onClick={() => onUpdateLayer(layer.id, { visible: !layer.visible })}
                            className={`p-1 mt-0.5 rounded-md cursor-pointer transition-colors ${
                              layer.visible ? "text-cyan-400 bg-cyan-950/40" : "text-slate-400 hover:text-slate-200"
                            }`}
                            title={layer.visible ? "Hide Layer" : "Show Layer"}
                          >
                            {layer.visible ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
                          </button>
                          <div className="min-w-0">
                            <div className="text-xs font-semibold text-slate-100 truncate">{layer.name}</div>
                            {/* EO Modality Badge */}
                            <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                              <span
                                className="text-[9px] font-mono px-1.5 py-0.5 rounded font-medium border"
                                style={{
                                  color: layer.modalityColor || "#06b6d4",
                                  backgroundColor: layer.modalityBgColor || "rgba(6, 182, 212, 0.12)",
                                  borderColor: (layer.modalityColor || "#06b6d4") + "40",
                                }}
                              >
                                {layer.modalityLabel || "Optical (True-Color RGB)"}
                              </span>
                              {isMosaic && (
                                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-700/40">
                                  {layer.tileCount} Scenes Combined
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Action Buttons: Fit Bounds, Deload, Delete */}
                        <div className="flex items-center gap-1 shrink-0">
                          {layer.bbox && (
                            <button
                              onClick={() => onFitBounds?.(layer.bbox!)}
                              className="p-1 rounded bg-white/[0.04] hover:bg-cyan-500/20 text-slate-400 hover:text-cyan-300 border border-white/[0.06] hover:border-cyan-500/30 transition-colors cursor-pointer"
                              title="Center Map on this Layer Extent"
                            >
                              <Crosshair className="w-3 h-3" />
                            </button>
                          )}
                          {onDeloadLayer && (
                            <button
                              onClick={() => onDeloadLayer(layer.id)}
                              className="p-1 rounded bg-amber-500/10 hover:bg-amber-500/25 text-amber-300/90 hover:text-amber-200 border border-amber-500/30 hover:border-amber-400 transition-colors cursor-pointer"
                              title="Deload overlay from map canvas"
                            >
                              <MinusCircle className="w-3 h-3" />
                            </button>
                          )}
                          {onDeleteLayer && (
                            <button
                              onClick={() => {
                                if (window.confirm(`Permanently delete layer "${layer.name}" and remove source files?`)) {
                                  onDeleteLayer(layer.id)
                                }
                              }}
                              className="p-1 rounded bg-rose-500/10 hover:bg-rose-500/25 text-rose-300/80 hover:text-rose-200 border border-rose-500/30 hover:border-rose-400 transition-colors cursor-pointer"
                              title="Delete layer permanently"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Unified Opacity Slider */}
                      {layer.visible && (
                        <div className="pt-2 border-t border-white/[0.06] space-y-1">
                          <div className="flex items-center justify-between text-[10px] text-slate-400">
                            <span>Unified Layer Opacity</span>
                            <span className="font-mono text-cyan-300 font-bold">{Math.round(layer.opacity * 100)}%</span>
                          </div>
                          <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.05"
                            value={layer.opacity}
                            onChange={(e) => onUpdateLayer(layer.id, { opacity: parseFloat(e.target.value) })}
                            className="w-full accent-cyan-400 h-1 bg-white/10 rounded-lg cursor-pointer"
                          />
                        </div>
                      )}

                      {/* If Mosaic: Accordion to Browse Individual Tiles */}
                      {isMosaic && (
                        <div className="mt-2.5 pt-2 border-t border-white/[0.04]">
                          <button
                            type="button"
                            onClick={() =>
                              setExpandedMosaics((prev) => ({ ...prev, [layer.id]: !prev[layer.id] }))
                            }
                            className="w-full flex items-center justify-between text-[10px] text-slate-400 hover:text-slate-200 font-mono py-1 px-1.5 rounded bg-white/[0.02] hover:bg-white/[0.05] cursor-pointer transition-colors"
                          >
                            <span>Inspect {layer.tileCount} Individual Tiles</span>
                            <ChevronDown
                              className={`w-3 h-3 transition-transform ${isExpanded ? "rotate-180 text-cyan-400" : ""}`}
                            />
                          </button>

                          {isExpanded && (
                            <div className="mt-2 space-y-1.5 pt-1">
                              {/* Search Tiles */}
                              <div className="relative">
                                <input
                                  type="text"
                                  placeholder="Search scenes (e.g. 0.tif)..."
                                  value={mosaicTileSearch[layer.id] || ""}
                                  onChange={(e) =>
                                    setMosaicTileSearch((prev) => ({ ...prev, [layer.id]: e.target.value }))
                                  }
                                  className="w-full bg-slate-900/80 border border-white/[0.08] text-slate-200 text-[10px] rounded px-2 py-1 pl-6 focus:outline-none focus:border-cyan-500/50"
                                />
                                <Search className="w-3 h-3 text-slate-500 absolute left-1.5 top-1.5" />
                              </div>

                              {/* Virtualized/Scrollable Tile Items */}
                              <div className="max-h-48 overflow-y-auto space-y-1 pr-1 font-mono text-[9px]">
                                {visibleTiles.slice(0, 50).map((tile) => (
                                  <div
                                    key={tile.id}
                                    className="p-1.5 rounded bg-black/40 border border-white/[0.03] flex items-center justify-between gap-1"
                                  >
                                    <div className="truncate text-slate-300 max-w-[170px]" title={tile.filename}>
                                      {tile.filename}
                                    </div>
                                    <div className="flex items-center gap-1 shrink-0">
                                      <span className="text-slate-500">{formatFileSize(tile.fileSize)}</span>
                                      {tile.bbox && (
                                        <button
                                          onClick={() => onFitBounds?.(tile.bbox!)}
                                          className="p-0.5 text-cyan-400 hover:text-cyan-200 cursor-pointer"
                                          title="Focus on this tile"
                                        >
                                          <Crosshair className="w-2.5 h-2.5" />
                                        </button>
                                      )}
                                    </div>
                                  </div>
                                ))}
                                {visibleTiles.length > 50 && (
                                  <div className="text-center text-slate-500 text-[9px] py-1">
                                    + {visibleTiles.length - 50} more tiles in mosaic
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}

              {loadedLayers.length === 0 && (
                <div className="text-center py-6 text-slate-400 text-xs px-2 bg-white/[0.02] rounded-xl border border-white/[0.05]">
                  {deloadedLayers.length > 0
                    ? "All overlays are currently deloaded from the map canvas. Click 'Reload' below to display them."
                    : "Upload GeoTIFF rasters above to populate dynamic spectral layer overlays and map them onto the globe."}
                </div>
              )}

              {/* Deloaded Overlays Section */}
              {deloadedLayers.length > 0 && (
                <div className="mt-4 pt-3 border-t border-white/[0.06] space-y-2">
                  <div className="flex items-center justify-between text-[10px] font-mono uppercase text-slate-400 font-medium">
                    <span className="flex items-center gap-1.5 text-amber-400/90">
                      <FolderX className="w-3 h-3" />
                      <span>Deloaded Overlays ({deloadedLayers.length})</span>
                    </span>
                    <span className="text-[9px] text-slate-500 font-sans">Off Map Canvas</span>
                  </div>

                  <div className="space-y-1.5">
                    {deloadedLayers.map((layer) => (
                      <div
                        key={layer.id}
                        className="p-2.5 rounded-xl border border-white/[0.06] bg-white/[0.015] hover:bg-white/[0.03] transition-all flex items-center justify-between gap-2"
                      >
                        <div className="min-w-0">
                          <div className="text-xs text-slate-300 font-medium truncate">{layer.name}</div>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <span className="text-[9px] font-mono text-slate-400">
                              {layer.isMosaic ? `${layer.tileCount} scenes` : "Single raster"}
                            </span>
                            <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-amber-950/50 text-amber-300 border border-amber-800/40">
                              Deloaded
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-1 shrink-0">
                          {onReloadLayer && (
                            <button
                              onClick={() => onReloadLayer(layer.id)}
                              className="flex items-center gap-1 px-2 py-1 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 text-[10px] font-mono border border-cyan-500/30 hover:border-cyan-400 transition-colors cursor-pointer"
                              title="Reload overlay back onto map canvas"
                            >
                              <PlusCircle className="w-3 h-3" />
                              <span>Reload</span>
                            </button>
                          )}
                          {onDeleteLayer && (
                            <button
                              onClick={() => {
                                if (window.confirm(`Delete deloaded layer "${layer.name}" permanently?`)) {
                                  onDeleteLayer(layer.id)
                                }
                              }}
                              className="p-1 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-300/80 hover:text-rose-200 border border-rose-500/30 hover:border-rose-400 transition-colors cursor-pointer"
                              title="Delete layer permanently"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 2: CATALOG SEARCH */}
        {activeTab === "catalog" && (
          <div className="space-y-3">
            <div className="p-3.5 bg-white/[0.03] border border-white/[0.08] rounded-xl space-y-3 backdrop-blur-md">
              <div className="text-xs font-semibold text-slate-200 flex items-center justify-between">
                <span>STAC Scene Discovery</span>
                <Filter className="w-3 h-3 text-cyan-400" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <span>Max Cloud Cover</span>
                  <span className="font-mono text-cyan-300">{cloudCoverMax}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={cloudCoverMax}
                  onChange={(e) => setCloudCoverMax(parseInt(e.target.value))}
                  className="w-full accent-cyan-400 h-1 bg-white/10 rounded-lg cursor-pointer"
                />
              </div>

              <button
                onClick={handleSearch}
                disabled={isSearchingCatalog}
                className="w-full flex items-center justify-center gap-2 py-2 px-3 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 text-xs font-medium rounded-lg border border-cyan-500/30 hover:border-cyan-400 transition-all cursor-pointer disabled:opacity-50"
              >
                {isSearchingCatalog ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Search className="w-3.5 h-3.5" />
                )}
                <span>{isSearchingCatalog ? "Querying STAC..." : "Query Sentinel & Landsat"}</span>
              </button>
            </div>

            {catalogScenes.length > 0 ? (
              <div className="space-y-2">
                <span className="text-[10px] font-mono uppercase text-slate-400">
                  Matched Scenes ({catalogScenes.length})
                </span>
                {catalogScenes.map((scene) => (
                  <div
                    key={scene.id}
                    className="p-3 bg-white/[0.02] border border-white/[0.06] rounded-xl hover:border-cyan-500/30 transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-mono text-[10px] text-cyan-300 font-bold truncate max-w-[190px]">
                          {scene.id}
                        </div>
                        <div className="text-[10px] text-slate-400 flex items-center gap-2 mt-0.5">
                          <span>{scene.datetime.split("T")[0]}</span>
                          <span className="flex items-center gap-0.5 text-slate-300">
                            <Cloud className="w-2.5 h-2.5 text-slate-400" />
                            {scene.cloud_cover}%
                          </span>
                        </div>
                      </div>
                      <span className="text-[9px] font-mono px-1 py-0.5 rounded bg-white/[0.05] text-slate-400">
                        {scene.resolution_m}m
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6 text-slate-400 text-xs px-2">
                Define an Area of Interest on the map and click Search to query intersecting public Copernicus satellite scenes.
              </div>
            )}
          </div>
        )}

        {/* TAB 3: ASSET INGESTION & REGISTRY */}
        {activeTab === "assets" && (
          <div className="space-y-3">
            {/* Filter by EO Modality */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[10px] font-mono uppercase text-slate-400">
                <span>Modality Filter</span>
                <span className="text-cyan-400">{filteredAssets.length} of {assets.length}</span>
              </div>
              <div className="grid grid-cols-3 gap-1 text-[10px] font-mono">
                {["ALL", "OPTICAL", "SAR", "DEM", "MULTISPECTRAL"].map((f) => (
                  <button
                    key={f}
                    onClick={() => {
                      setAssetFilter(f)
                      setAssetPage(1)
                    }}
                    className={`py-1 px-1.5 rounded text-center transition-colors cursor-pointer border ${
                      assetFilter === f
                        ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/50"
                        : "bg-white/[0.02] text-slate-400 border-white/[0.05] hover:text-slate-200"
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>

              {/* Search Bar */}
              <div className="relative mt-2">
                <input
                  type="text"
                  placeholder="Filter scenes by filename..."
                  value={assetSearchQuery}
                  onChange={(e) => {
                    setAssetSearchQuery(e.target.value)
                    setAssetPage(1)
                  }}
                  className="w-full bg-slate-900/80 border border-white/[0.08] text-slate-200 text-xs rounded-lg px-2.5 py-1.5 pl-7 focus:outline-none focus:border-cyan-500/50"
                />
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2 top-2" />
              </div>
            </div>

            {/* Registered Assets List */}
            <div className="space-y-2">
              {paginatedAssets.length > 0 ? (
                paginatedAssets.map((ast) => {
                  const meta = ast.metadata || {}
                  const v = ast.versions[0]
                  const modalityLabel = meta.modality_label || "Optical (True-Color RGB)"
                  const modalityColor = meta.modality_color || "#06b6d4"
                  const modalityBgColor = meta.modality_bg_color || "rgba(6, 182, 212, 0.12)"

                  return (
                    <div
                      key={ast.id}
                      className="p-3 bg-white/[0.03] border border-white/[0.08] rounded-xl space-y-2 backdrop-blur-md"
                    >
                      <div className="flex items-start justify-between gap-1.5">
                        <div className="min-w-0">
                          <span className="text-xs font-semibold text-slate-100 truncate block">
                            {meta.filename || ast.title}
                          </span>
                          {/* Modality Badge */}
                          <span
                            className="inline-block text-[9px] font-mono px-1.5 py-0.5 rounded font-medium border mt-1"
                            style={{
                              color: modalityColor,
                              backgroundColor: modalityBgColor,
                              borderColor: modalityColor + "40",
                            }}
                          >
                            {modalityLabel}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 shrink-0">
                          {meta.bbox && (
                            <button
                              onClick={() => onFitBounds?.(meta.bbox)}
                              className="p-1 rounded bg-white/[0.04] hover:bg-cyan-500/20 text-slate-400 hover:text-cyan-300 border border-white/[0.06] hover:border-cyan-500/30 transition-colors cursor-pointer"
                              title="Center Map on this Asset"
                            >
                              <Crosshair className="w-3 h-3" />
                            </button>
                          )}
                          {onDeleteAsset && (
                            <button
                              onClick={() => {
                                if (window.confirm(`Delete asset "${meta.filename || ast.title}"?`)) {
                                  onDeleteAsset(ast.id)
                                }
                              }}
                              className="p-1 rounded bg-white/[0.04] hover:bg-rose-500/20 text-slate-400 hover:text-rose-300 border border-white/[0.06] hover:border-rose-500/30 transition-colors cursor-pointer"
                              title="Delete this asset"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          )}
                          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-full bg-emerald-950/60 text-emerald-300 border border-emerald-700/50">
                            {ast.status}
                          </span>
                        </div>
                      </div>

                      <div className="text-[10px] font-mono text-slate-400 flex items-center justify-between">
                        <span className="truncate max-w-[140px]">{ast.collection_id}</span>
                        <span>{v ? formatFileSize(v.size_bytes) : "N/A"}</span>
                      </div>

                      {v && (
                        <div className="text-[9px] text-slate-400 pt-1.5 border-t border-white/[0.05] grid grid-cols-2 gap-1 font-mono">
                          <div>Bands: <span className="text-slate-200">{v.band_count}</span></div>
                          <div className="text-right">CRS: <span className="text-slate-200">{v.crs_code}</span></div>
                          <div>Dim: <span className="text-slate-200">{v.width}×{v.height}</span></div>
                          <div className="text-right">GSD: <span className="text-slate-200">{v.resolution_x?.toFixed(1)}m</span></div>
                        </div>
                      )}
                    </div>
                  )
                })
              ) : (
                <div className="text-center py-8 text-slate-400 text-xs px-3 bg-white/[0.01] rounded-xl border border-white/[0.04]">
                  <Inbox className="w-6 h-6 mx-auto mb-2 text-slate-600 opacity-60" />
                  <p className="font-medium text-slate-300">No Assets Matching Filter</p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Upload single or multiple GeoTIFF files using the upload bar above.
                  </p>
                </div>
              )}

              {/* Pagination Controls */}
              {totalAssetPages > 1 && (
                <div className="flex items-center justify-between pt-2 text-[10px] font-mono text-slate-400 border-t border-white/[0.06]">
                  <button
                    onClick={() => setAssetPage((p) => Math.max(1, p - 1))}
                    disabled={assetPage <= 1}
                    className="px-2 py-1 rounded bg-white/[0.05] hover:bg-white/[0.1] disabled:opacity-30 cursor-pointer"
                  >
                    Previous
                  </button>
                  <span>
                    Page {assetPage} of {totalAssetPages}
                  </span>
                  <button
                    onClick={() => setAssetPage((p) => Math.min(totalAssetPages, p + 1))}
                    disabled={assetPage >= totalAssetPages}
                    className="px-2 py-1 rounded bg-white/[0.05] hover:bg-white/[0.1] disabled:opacity-30 cursor-pointer"
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 4: AREA OF INTEREST (AOI) */}
        {activeTab === "aois" && (
          <div className="space-y-3">
            <div className="p-3.5 bg-white/[0.03] border border-white/[0.08] rounded-xl space-y-3 backdrop-blur-md">
              <span className="text-xs font-semibold text-slate-200 block">
                Define Boundary Extent
              </span>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Draw geometric boundaries on the globe to isolate raster extraction and zonal statistics.
              </p>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => onStartDrawAOI("box")}
                  className="py-2 px-3 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 text-xs font-medium border border-cyan-500/30 hover:border-cyan-400 transition-all cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <Square className="w-3.5 h-3.5" />
                  <span>Draw Bounding Box</span>
                </button>
                <button
                  onClick={() => onStartDrawAOI("polygon")}
                  className="py-2 px-3 rounded-lg bg-white/5 hover:bg-white/10 text-slate-200 text-xs font-medium border border-white/10 hover:border-white/20 transition-all cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <Maximize2 className="w-3.5 h-3.5" />
                  <span>Draw Polygon</span>
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase text-slate-400">
                  Registered Boundaries ({aois.length})
                </span>
                <div className="flex items-center gap-1.5">
                  {aois.length > 0 && onToggleAllAOIsVisibility && (
                    <button
                      type="button"
                      onClick={() => {
                        const allHidden = aois.every((a) => hiddenAoiIds.has(a.id))
                        onToggleAllAOIsVisibility(allHidden)
                      }}
                      className="text-[9px] font-mono text-cyan-400 hover:text-cyan-200 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/40 transition-colors cursor-pointer flex items-center gap-1"
                      title={aois.every((a) => hiddenAoiIds.has(a.id)) ? "Show all boundaries on map" : "Hide all boundaries from map"}
                    >
                      {aois.every((a) => hiddenAoiIds.has(a.id)) ? (
                        <>
                          <Eye className="w-2.5 h-2.5" />
                          <span>Show All</span>
                        </>
                      ) : (
                        <>
                          <EyeOff className="w-2.5 h-2.5" />
                          <span>Hide All</span>
                        </>
                      )}
                    </button>
                  )}
                  {activeAOI && (
                    <button
                      type="button"
                      onClick={() => onSelectAOI(null)}
                      className="text-[9px] font-mono text-slate-400 hover:text-rose-300 bg-white/[0.04] px-1.5 py-0.5 rounded border border-white/[0.08] transition-colors cursor-pointer flex items-center gap-1"
                      title="Clear active boundary selection"
                    >
                      <X className="w-2.5 h-2.5" />
                      <span>Deselect</span>
                    </button>
                  )}
                </div>
              </div>

              {aois.length > 0 ? (
                aois.map((aoi) => {
                  const isSelected = activeAOI?.id === aoi.id
                  const isHidden = hiddenAoiIds.has(aoi.id)
                  return (
                    <div
                      key={aoi.id}
                      className={`p-3 rounded-xl border backdrop-blur-md transition-all ${
                        isSelected
                          ? "bg-cyan-500/10 border-cyan-500/50 shadow-sm"
                          : isHidden
                          ? "bg-white/[0.01] border-white/[0.04] opacity-60"
                          : "bg-white/[0.02] border-white/[0.06] hover:bg-white/[0.04]"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 min-w-0">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              onToggleAOIVisibility?.(aoi.id)
                            }}
                            className={`p-1 rounded cursor-pointer transition-colors ${
                              isHidden
                                ? "text-slate-500 hover:text-slate-300 bg-white/[0.03]"
                                : "text-cyan-400 bg-cyan-950/50 hover:bg-cyan-900/50"
                            }`}
                            title={isHidden ? "Show polygon on map" : "Hide polygon from map"}
                          >
                            {isHidden ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                          </button>
                          <div
                            onClick={() => onSelectAOI(isSelected ? null : aoi)}
                            className="cursor-pointer min-w-0"
                            title="Click to toggle active target"
                          >
                            <span className="text-xs font-semibold text-slate-100 block truncate">
                              {aoi.name}
                            </span>
                            <div className="flex items-center gap-1.5 mt-0.5">
                              <span className="text-[9px] font-mono text-slate-400">
                                {aoi.geometry?.type || "Polygon"}
                              </span>
                              {isSelected ? (
                                <span className="text-[8px] font-mono px-1 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-800/60 uppercase">
                                  Target
                                </span>
                              ) : !isHidden ? (
                                <span className="text-[8px] font-mono px-1 rounded bg-white/[0.04] text-slate-400 border border-white/[0.06] uppercase">
                                  Visible
                                </span>
                              ) : (
                                <span className="text-[8px] font-mono px-1 rounded bg-white/[0.02] text-slate-500 uppercase">
                                  Hidden
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Actions: Zoom to bounds & Delete */}
                        <div className="flex items-center gap-1 shrink-0">
                          {aoi.bbox && aoi.bbox.length === 4 && (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation()
                                onFitBounds?.(aoi.bbox as [number, number, number, number])
                              }}
                              className="p-1 rounded bg-white/[0.04] hover:bg-cyan-500/20 text-slate-400 hover:text-cyan-300 transition-colors cursor-pointer"
                              title="Focus map on boundary"
                            >
                              <Maximize2 className="w-3 h-3" />
                            </button>
                          )}
                          {onDeleteAOI && (
                            <button
                              type="button"
                              onClick={async (e) => {
                                e.stopPropagation()
                                await onDeleteAOI(aoi.id)
                              }}
                              className="p-1 rounded bg-white/[0.04] hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition-colors cursor-pointer"
                              title="Delete boundary permanently"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })
              ) : (
                <div className="text-center py-6 text-slate-400 text-xs px-2">
                  No AOIs registered yet. Use the drawing buttons above to create boundary extents.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
