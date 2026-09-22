# TRINETRA / SHANETRA EXPLORE PAGE — COMPLETE UI/UX SPECIFICATION & COMPONENT DIRECTORY
**System Designation**: TRINETRA Geospatial Exploration & Multi-Sensor Intelligence Workstation  
**Route**: `/explore`  
**Target Audience**: Senior Frontend & UI/UX Design AI / System Architects  
**Author**: DeepMind Antigravity Engineering System  

---

## 1. Executive Overview & Mission Purpose

The `/explore` page is the primary operational interface for **TRINETRA (Project SHANETRA)**—an advanced Earth Observation (EO), satellite telemetry, and multi-sensor intelligence workstation developed for defense, disaster management, spatial analytics, and critical infrastructure monitoring.

### Core Architectural Mandates
1. **Dual-Dimension Rendering Engine**: Supports both **2D Vector/Raster Mapping (MapLibre GL)** and **3D Photorealistic Geospatial Globe (CesiumJS WGS84 Ellipsoid)** with strict renderer lifecycle isolation (only one active WebGL canvas at a time to eliminate GPU memory leaks).
2. **Multi-Sensor Earth Observation**: Discovers, overlays, blends, and coregisters datasets across Optical (Sentinel-2, Landsat-8/9), Synthetic Aperture Radar (Sentinel-1 SAR VV/VH all-weather penetration), Hyperspectral, and Thermal sensors.
3. **Natural-Language AI Map Commands**: An air-gapped AI intent parser and command execution pipeline capable of camera flights, automatic Area of Interest (AOI) bounding, layer toggles, and temporal multi-sensor queries.
4. **Bi-Temporal Change Detection & Intelligence**: Split-screen swipe comparison, automated change detection, VQA (Visual Question Answering), semantic evidence fusion graphs, continuous AOI monitoring, and intelligence dossier generation.

---

## 2. Layout Geometry & Screen Real Estate

The workstation uses a high-density, dark tactical theme (`#080b11`, `#0b0f19`, `#121620`, with cyan `#00f0ff` / `#38bdf8` tactical accents) optimized for high-resolution command center displays:

```
+---------------------------------------------------------------------------------------------------------+
| [EXPLORE HEADER] (Height: 52px, Sticky Top, z-index: 40)                                                |
| [<- Workspace] [TRINETRA Logo] | [Natural Language Query Bar (AI/FastPath)] | [AI Status] [2D/3D] [Reset]|
+---------------------------------------------------------------------------------------------------------+
| [SIDEBAR TOGGLE] | [FLOATING AOI TOOLBAR] (Top Left, z-index: 20)                                      |
| (z: 30)          | [Box] [Polygon] [Clear] [Status Badge: Area km²]                                     |
|                  +--------------------------------------------------------------------------------------+
| [COLLAPSIBLE     |                                                                                      |
|  SIDEBAR]        |                                                                                      |
| (Width: 420px,   |                                                                                      |
|  z-index: 15,    |                           ACTIVE VIEWPORT                                            |
|  9 Functional    |             (3D Cesium Globe / 2D MapLibre Map / Split-View)                         |
|  Tabs)           |                                                                                      |
|                  |                                                                                      |
|                  |                                                 [COORDINATE & TELEMETRY HUD]         |
|                  |                                                 (Bottom Right, z-index: 20)          |
|                  |                                                 GEO: Lat, Lon, Alt, Zoom, Pitch, Hdg |
|                  +--------------------------------------------------------------------------------------+
|                  | [FLOATING TEMPORAL SCRUBBER & TIMELINE] (Bottom, z-index: 20, Conditionally Shown)  |
|                  | [Acquisition Timeline Track | Play/Pause | Step Prev | Step Next]                    |
+---------------------------------------------------------------------------------------------------------+
| [EXPLORE STATUS BAR] (Height: 28px, Fixed Bottom, z-index: 40)                                          |
| [Renderer Ready / WebGL Status] [GPU Accel]           |           [FPS: 60 | Init: 12ms] [Air-Gapped]   |
+---------------------------------------------------------------------------------------------------------+
```

---

## 3. Exhaustive Component Directory & Feature Inventory

---

### GROUP A: Top Navigation & Command Bar (`ExploreHeader.tsx`)
**File Path**: `frontend/components/explore/ExploreHeader.tsx`  
**Container Role**: Fixed command header providing workspace navigation, AI query parsing, dimension toggling, and global camera reset.

#### 1. Workspace Return Button (`Link: /analysis`)
- **Visuals**: Left arrow icon (`ArrowLeft`), text `"Workspace"`, border button (`btn-tactical-icon`).
- **Visibility**: Always visible (top-left).
- **Purpose**: Routes the analyst back to the tactical analysis page (`/analysis`).
- **Importance**: Smooth context switching between freeform Earth exploration and structured incident reporting.

#### 2. Brand Identifier & Module Badge
- **Visuals**: Glowing bold text `"TRI•NETRA"` followed by a cyan tactical pill badge `"SHANETRA EXPLORE"`.
- **Visibility**: Always visible.
- **Purpose**: Brand identity and current module indicator.

#### 3. AI Natural Language Query Bar (`QueryBar.tsx`)
- **File Path**: `frontend/components/explore/QueryBar.tsx`
- **Visibility**: Always visible in the center of the header.
- **Visual Elements**:
  - **Sparkles Icon**: AI indicator in input box.
  - **Text Input**: Placeholder: `"Ask TRINETRA... (e.g., 'Go to Nagpur', 'Show Sentinel-2', 'Reset')"`. Supports up to 500 characters. Submits on Enter key.
  - **Clear Button (`X`)**: Hidden when query is empty; visible when text is typed; clears input.
  - **Action Button (`Send` / `Cancel`)**:
    - In Idle mode: Cyan button labeled `"Send"` with `Send` icon. Disabled if input is blank.
    - In Loading mode: Amber button labeled `"Cancel"` with a spinning loader (`Loader2`). Cancels the in-flight HTTP request via `AbortController`.
- **Underlying Logic**:
  - Checks if query matches deterministic fast-paths (< 1ms execution) or passes to Unified AI Gateway.
  - Applies state patch (camera target, layer toggles, AOI bounding box) deterministically to the active globe/map.
- **Importance**: The centerpiece AI interaction for the entire Earth exploration interface.

#### 4. Contextual Query Suggestions (`QuerySuggestions.tsx`)
- **File Path**: `frontend/components/explore/QuerySuggestions.tsx`
- **Visibility**: **Dynamic / Conditional**. Renders below the query input when focused or active.
- **Visual Elements**:
  - Icon: `Sparkles` with `"TRY:"` label.
  - Suggestion Chips: Dynamic pills generated based on active layers:
    - If Sentinel-2 is off: `"Show Sentinel-2"`. If Sentinel-2 is on: `"Make Sentinel-2 50% transparent"`.
    - If boundaries are off: `"Show boundaries"`. If boundaries are on: `"Hide boundaries"`.
    - If radar is off: `"Show radar imagery"`.
    - Geopolitical defaults: `"Go to Nagpur"`, `"Zoom into Mumbai"`, `"Reset the globe"`.
- **Action**: Clicking any chip instantly populates the query input and triggers execution.
- **Importance**: Teaches the operator what natural-language commands are supported without reading manuals.

#### 5. Real-Time Command Activity HUD (`CommandActivity.tsx`)
- **File Path**: `frontend/components/explore/CommandActivity.tsx`
- **Visibility**: **Conditional (Hidden when status is `idle`)**. Pops down directly beneath the query bar when a command is executing or has completed.
- **Visual Elements**:
  - **Path Badge**:
    - `FAST PATH (0.0ms)`: Green/Cyan lightning badge (`Zap`) indicating sub-millisecond local rule execution.
    - `AI GATEWAY (1420ms)`: Blue/Purple clock badge (`Clock`) indicating LLM inference route.
  - **Close Button (`×`)**: Dismisses the HUD back to `idle`.
  - **Summary Text**: High-level feedback message (e.g., `"Centered map on New Delhi and delineated target region."`).
  - **Step-by-Step Execution List**:
    - Success steps (`CheckCircle2` green icon, e.g., `[FLY_TO] executed`, `[SET_AOI] executed`).
    - No-op steps (`CheckCircle2` grey icon, e.g., `[SHOW_LAYER] Layer already active`).
    - Failed steps (`XCircle` red icon, error reason).
    - Cancelled steps (`AlertTriangle` amber icon).
- **Importance**: Provides military-grade feedback and auditability of exactly what the AI did to the map state.

#### 6. AI Engine Telemetry Badge (`AIStatus.tsx`)
- **File Path**: `frontend/components/explore/AIStatus.tsx`
- **Visibility**: Always visible in the top-right header actions group.
- **Visual Elements**:
  - **Online State**: Glowing green pulse icon (`Sparkles`), text `"AI READY"`, model tag (e.g., `"llama3.2"`, `"gpt-4o-mini"`). Hover tooltip reveals active planner and router models.
  - **Offline State**: Amber warning icon (`AlertCircle`), text `"AI OFFLINE"`, tag `"FALLBACK"`. Tooltip explains that deterministic fast-paths remain 100% operational.
- **Behavior**: Polls `GET /api/v1/explore/ai/status` every 30 seconds.
- **Importance**: Transparently displays whether the local Ollama LLM / Cloud API is connected or running in air-gapped fallback mode.

#### 7. 2D / 3D Dimension Switcher (`ViewModeSwitcher.tsx`)
- **File Path**: `frontend/components/explore/ViewModeSwitcher.tsx`
- **Visibility**: Always visible in the header and duplicated inside the sidebar top section.
- **Visual Elements**: Two-button tactical toggle group (`role="radiogroup"`):
  - `2D Map` button (`Map` icon).
  - `3D Globe` button (`Globe` icon).
- **Behavior**: Dispatches `SET_VIEW_MODE` to `globeCommandBus`. Performs camera state transformation so coordinates and zoom are preserved across renderers.
- **Importance**: Switches between flat analytical projection and true curved 3D ellipsoidal terrain.

#### 8. Camera Reset Button (`RotateCcw`)
- **Visuals**: Circular reset arrow (`RotateCcw`), text `"Reset"`.
- **Visibility**: Always visible in top-right.
- **Behavior**: Dispatches `RESET_VIEW` to `globeCommandBus`. Restores camera to high-altitude overview over Central India (`21.1458° N, 79.0882° E`, nadir pitch `-90°`, zoom `4.8`).
- **Importance**: Immediate one-click escape when lost in extreme zooms or tilted camera orientations.

---

### GROUP B: Active Viewport & Floating Controls (`ExploreViewport.tsx`)
**File Path**: `frontend/components/explore/ExploreViewport.tsx`  
**Container Role**: Hosts the primary interactive map canvas along with floating contextual toolbars, HUDs, and overlays.

#### 1. Floating Sidebar Toggle Button (`PanelLeftClose` / `PanelLeftOpen`)
- **Visuals**: Floating button at top-left (`z-index: 20`).
- **Visibility**: Always visible.
- **Behavior**: Toggles `sidebarOpen` in `globeState`. Icon dynamically flips between `PanelLeftClose` (when expanded) and `PanelLeftOpen` (when collapsed).
- **Importance**: Maximizes screen space for full-viewport satellite inspection.

#### 2. Floating Area of Interest (AOI) Toolbar (`AOIToolbar.tsx`)
- **File Path**: `frontend/components/explore/AOIToolbar.tsx`
- **Visibility**: Always visible, floating at `top: 14px, left: 64px`.
- **Visual Elements**:
  - **AOI Title Badge**: Polygon icon with text `"AOI"`.
  - **Box Mode Button**: `rect` icon, text `"Box"`. Toggles rectangle drag-draw mode on the active map.
  - **Polygon Mode Button**: `polygon` icon, text `"Polygon"`. Toggles freeform multi-vertex polygon drawing.
  - **Clear Button (`Clear`)**: **Hidden when no AOI is active**. Appears in crimson red when an AOI exists. Clears bounding box and unloads region masks.
  - **Validation & Area Telemetry Badge**:
    - In validating state: Pulsing cyan dot with text `"Validating..."`.
    - If valid AOI: Emerald green dot displaying exact computed area (e.g., `"1,420 km²"`).
    - If invalid AOI: Crimson dot displaying `"Invalid AOI"`. Hover tooltip shows self-intersection or boundary errors.
    - If no AOI: Muted text `"No AOI"`.
- **Importance**: The gateway for bounding spatial operations—temporal search, change detection, and VQA all anchor to this active AOI.

#### 3. 3D Globe Engine Canvas (`GlobeView.tsx`)
- **File Path**: `frontend/components/explore/GlobeView.tsx`
- **Visibility**: Active when `viewMode === "3d"`.
- **Core Capabilities**:
  - **3D WGS84 Ellipsoid & Real Terrain**: ReEarth / Cesium terrain integration with atmospheric fog, horizon lighting, and ground clamping.
  - **Custom Post-Processing Sharpen Shader**: Custom GLSL fragment shader (`SHARPEN_SHADER`) applied to imagery to sharpen high-frequency satellite details and eliminate texture blur.
  - **Downward Perspective Geometry**: Enforces downward bird's-eye camera perspective (`pitch: -50.0°`) and calculates line-of-sight ground offset so targets center on screen without horizon glare.
  - **AOI Polygon & Glowing Boundary**: Renders active AOI with semi-transparent cyan fill (`#06b6d4`, alpha 0.22) and a 3.5px glowing cyan polyline border (`#22d3ee`, `clampToGround: true`).
  - **Navigation & Camera Gestures**:
    - Left Click + Drag: Rotate globe / Pan.
    - Right Click + Drag / Scroll: Zoom in & out.
    - Middle Click + Drag / Ctrl + Left Drag: Orbit, change heading and pitch.
- **Importance**: Primary 3D intelligence visualization canvas.

#### 4. 2D MapLibre Map Engine Canvas (`MapView.tsx`)
- **File Path**: `frontend/components/explore/MapView.tsx`
- **Visibility**: Active when `viewMode === "2d" && comparisonMode !== "split"`.
- **Core Capabilities**:
  - **Vector & Raster Tile Stacking**: High-speed tile rendering using MapLibre GL JS.
  - **Interactive Bounding Box Drag-Draw**: Click-and-drag rubberband rectangle creation.
  - **Interactive Multi-Point Polygon Drawing**: Sequential vertex placement with double-click close.
  - **Synchronized Camera Broadcasting**: Publishes pan/zoom coordinates to `cameraSyncBus`.
- **Importance**: Fast, lightweight flat cartographic projection ideal for precise 2D vector measurements.

#### 5. Dual-Observation Split-Screen Swipe Canvas (`SplitView.tsx`)
- **File Path**: `frontend/components/explore/SplitView.tsx`
- **Visibility**: **Conditional**. Active ONLY when `viewMode === "2d" && comparisonMode === "split"`.
- **Visual Elements**:
  - Two synchronized MapLibre viewports (`view-a` on left, `view-b` on right).
  - **Draggable Vertical Divider Bar**: A vertical tactical cyan line with a center grip handle (`↔`). Dragging left/right adjusts the split percentage (0% to 100%) in real time.
  - **Observation Badges**: Overlays `"BASE (A): [Date]"` on the left and `"COMPARE (B): [Date]"` on the right.
- **Importance**: Visual before/after inspection of battle damage, flood ingress, or construction progress.

#### 6. Floating Acquisition Timeline & Scrubber (`Timeline.tsx`)
- **File Path**: `frontend/components/explore/Timeline.tsx`
- **Visibility**: **Hidden / Conditional**. Returns `null` if `observations.length === 0`. Appears floating at `bottom: 40px, left: 16px, right: 16px` as soon as satellite acquisitions are loaded.
- **Visual Elements**:
  - Header: Clock icon, text `"Acquisition Timeline"`, badge showing `(N acquisitions)`.
  - **Playback Controller**:
    - **Step Previous (`|<`)**: Jumps to preceding observation in time.
    - **Play / Pause (`Play` / `Pause`)**: Toggles automatic sequential time-lapse playback across observations. When playing, turns amber with a `"Pause"` label.
    - **Step Next (`>|`)**: Jumps to subsequent observation in time.
  - **Horizontal Scrollable Track**:
    - Renders `<TimelineItem />` cards for every satellite pass ordered chronologically.
    - Auto-scrolls the active selected observation into the center of view.
    - Cards display date, satellite constellation icon (Sentinel-2, Landsat, SAR), cloud cover %, and resolution.
- **Importance**: Time-lapse scrubbing for multi-temporal surveillance and historical change observation.

#### 7. Real-Time Geospatial Coordinate & Telemetry HUD (`CoordinateHUD.tsx`)
- **File Path**: `frontend/components/explore/CoordinateHUD.tsx`
- **Visibility**: Always visible, positioned at `bottom: 12px, right: 12px` (`z-index: 20`).
- **Visual Elements**:
  - **Compass Needle (`Navigation`)**: Dynamically rotates based on current camera heading angle.
  - **GEO Tag**: Tactical cyan label.
  - **Latitude Readout**: High-precision decimal degrees with cardinal identifier (e.g., `28.6139° N`).
  - **Longitude Readout**: High-precision decimal degrees with cardinal identifier (e.g., `77.2090° E`).
  - **Altitude (ALT)**: Dynamically scales between meters (`m`) and kilometers (`km`) based on camera height (e.g., `ALT 14.6 km`).
  - **Zoom (Z)**: Zoom level to 1 decimal place (e.g., `Z 11.5`).
  - **3D Attitude (HDG / PIT)**: **Visible only in 3D Globe mode**. Displays Heading (e.g., `HDG 180°`) and Pitch (e.g., `PIT -50°`).
  - **Copy Coordinates Button**: Copy icon (`Copy`). Clicking copies `lat, lon` to system clipboard and morphs into a green checkmark (`Check`) for 1.8 seconds.
- **Importance**: Essential for tactical military grid referencing, cross-referencing artillery/recon coordinates, and reporting.

---

### GROUP C: Collapsible Operational Sidebar (`ExploreSidebar.tsx`)
**File Path**: `frontend/components/explore/ExploreSidebar.tsx`  
**Container Role**: Comprehensive 420px wide analytical drawer containing 9 distinct operational tabs.

```
Sidebar Top: [Dimension View Switcher] | [Operational Data Status]
Tabs Header: [Catalog] [Layers] [Temporal] [Compare] [Analysis] [Investigate] [Intel] [Workspace] [Points]
```

#### Top Section 1: Operational Data Status (`DataStatus.tsx`)
- **Visuals**: Displays active data provider connectivity (e.g., `"Copernicus STAC Live"`, `"Air-Gapped Local Cache"`), cached tiles count, and bandwidth usage.

---

#### TAB 1: Catalog Search & Discovery (`Catalog`)
- **Subcomponents**: `DataSourcePanel.tsx`, `CatalogResults.tsx`, `DatasetCard.tsx`
- **Purpose**: Search live and air-gapped STAC (SpatioTemporal Asset Catalog) repositories.
- **Controls & Buttons**:
  - **STAC Source Dropdown**: Copernicus Data Space, AWS Open Data, Local Air-Gapped STAC, ISRO Bhoonidhi.
  - **Text Search Bar**: Keyword search across satellite mission titles.
  - **Collection Checkboxes**: Sentinel-2 L2A (Optical), Sentinel-1 GRD (SAR Radar), Landsat-9 OLI, ISRO Cartosat.
  - **Max Cloud Cover Slider**: 0% to 100% threshold filter.
  - **Search Button (`Search`)**: Queries STAC catalog within current AOI / bounding box.
  - **Result Cards (`DatasetCard.tsx`)**:
    - Thumbnail preview.
    - Cloud cover badge, capture date, ground sampling distance (GSD).
    - `"Add to Map"` button: Instantly loads the raster as an active tile layer.
    - `"Inspect Metadata"` button: Opens technical JSON metadata drawer.

---

#### TAB 2: Active Layers & Basemaps (`Layers`)
- **Subcomponent**: `ActiveLayers.tsx`
- **Purpose**: Full raster stack management, basemap swapping, and custom tile integration.
- **Controls & Modals**:
  - **Basemap Preset Selector**: 4 visual cards:
    1. *Dark Tactical* (CartoDB Dark Matter).
    2. *Satellite Imagery* (Sentinel-2 Cloudless / ESRI World Imagery).
    3. *Topographic* (OpenTopoMap with elevation contours).
    4. *OpenStreetMap* (Standard street cartography).
  - **Action Button: `+ Add Custom Tile`**: Opens the **Custom Layer Modal** (`showAddModal`).
    - Form fields: Layer Name, Tile URL template (`https://.../{z}/{x}/{y}.png` or COG URL), Attribution, `"Use as Basemap"` checkbox.
    - Buttons: `"Add Layer"` and `"Cancel"`.
  - **Action Button: `Key / Credentials`**: Opens the **API Keys Configuration Modal** (`showKeysModal`).
    - Form fields: Cesium Ion Access Token input, Google Maps 3D Tiles API Key input.
    - Saved to browser `localStorage` for private persistence without server transmission.
  - **Active Layer Item Controls**:
    - **Visibility Toggle (`Eye` / `EyeOff`)**: Shows or hides layer without removing it.
    - **Opacity Slider**: Draggable range slider from 0% to 100%.
    - **Layer Type Badge**: Optical (cyan), SAR Radar (amber), Borders (purple), Elevation (emerald).
    - **Promote to Basemap Button**: Promotes custom imagery to the base layer.
    - **Delete Button (`Trash2`)**: Removes layer from the active stack.

---

#### TAB 3: Temporal Acquisitions (`Temporal`)
- **Subcomponents**: `TemporalToolbar.tsx`, `DateRangePicker.tsx`, `ObservationDetails.tsx`, `ObservationCard.tsx`
- **Purpose**: Query and inspect individual satellite passes over the active AOI across historical timelines.
- **Controls & Buttons**:
  - **Date Range Picker (`DateRangePicker.tsx`)**: Start Date and End Date inputs with quick presets (`Last 7 Days`, `Last 30 Days`, `Last 1 Year`).
  - **Sensor Filter Pills**: All, Optical Only, SAR Radar Only.
  - **Search Acquisitions Button**: Queries backend `/api/v1/explore/temporal/search`.
  - **Observation Cards List**: Cards showing satellite badge, capture timestamp, sun elevation, cloud cover. Clicking a card selects it as the active primary observation.
  - **Observation Details Pane (`ObservationDetails.tsx`)**: Deep dive into the selected pass: sensor geometry, orbit direction (Ascending/Descending), incidence angle, polarization (VV, VH, HH, HV).

---

#### TAB 4: Dual Observation Comparison (`Compare`)
- **Subcomponents**: `ComparisonPanel.tsx`, `ComparisonControls.tsx`
- **Purpose**: Side-by-side and split-swipe comparison of two distinct satellite passes.
- **Controls & Features**:
  - **Slot A (Base)**: Card displaying selected Observation A with timestamp and clear button (`✕`).
  - **Swap Button (`⇄`)**: Flips Observation A and Observation B.
  - **Slot B (Compare)**: Card displaying selected Observation B with timestamp and clear button (`✕`).
  - **Compatibility & Overlap Validator**:
    - Automatic spatial intersection verification (% overlap).
    - Temporal delta indicator (e.g., `Δ 14 days`).
    - Resolution warning badge if comparing mismatched GSDs (e.g., 10m Sentinel vs 30m Landsat).
  - **Comparison Mode Buttons**:
    1. `Split`: Enables vertical draggable swipe divider on the map.
    2. `Side by Side`: Opens two synchronized viewports.
    3. `Opacity`: Single map with cross-dissolve opacity slider blending A into B.
  - **Exit Compare Button**: Exits comparison mode and returns to standard single view.

---

#### TAB 5: EO Analytical Intelligence Engine (`Analysis`)
- **Subcomponents**: `AnalysisPanel.tsx`, `AnalysisModeBadge.tsx`, `AnalysisProgress.tsx`, `FindingsPanel.tsx`, `EvidencePanel.tsx`, `LimitationPanel.tsx`, `AnalysisArtifacts.tsx`, `ChangeStatistics.tsx`, `ChangeLegend.tsx`
- **Purpose**: Deep automated Earth Observation analytical models.
- **Analysis Modes**:
  1. `SINGLE_IMAGE`: Target counting, airfield/harbor inspection, VQA.
  2. `BI_TEMPORAL`: Optical or SAR difference change detection.
  3. `SAR_OPTICAL`: Deep fusion combining radar ground penetration with optical spectra.
- **Controls & Buttons**:
  - **Prompt Input Bar**: Query text for the analysis engine (e.g., `"Detect new construction between observations"`).
  - **Example Query Chips**: One-click quick prompts (`Urban Expansion`, `Flood Inundation`, `Airfield Inspection`).
  - **Run Button (`Play: Run Analysis`)**: Validates AOI and observation pairing, then dispatches execution.
  - **Cancel Button (`XCircle`)**: Aborts in-flight deep learning inference.
  - **Multi-Stage Progress Bar (`AnalysisProgress.tsx`)**: Telemetry progress through 5 pipeline stages: Ingestion $\rightarrow$ Calibration $\rightarrow$ Coregistration $\rightarrow$ Inference $\rightarrow$ Synthesis.
  - **Result Tabs**:
    - **Findings**: Cards for each detected feature with confidence score and click-to-focus on map.
    - **Narrative**: Markdown intelligence report generated by the vision-language model.
    - **Evidence**: Sensor-level proof points with signal-to-noise metrics.
    - **Artifacts**: Download buttons for GeoTIFF difference rasters, PNG masks, and GeoJSON vector contours.
    - **Limitations**: Sensor constraints, resolution barriers, cloud occlusion warnings.

---

#### TAB 6: Semantic EO Intelligence & Evidence Fusion (`Investigate`)
- **Subcomponents**: `InvestigationPanel.tsx`, `InvestigationComposer.tsx`, `FindingsDashboard.tsx`, `EvidenceCard.tsx`, `EvidenceGraph.tsx`, `InvestigationTimeline.tsx`, `ObjectTrackPanel.tsx`, `ProvenancePanel.tsx`, `AnalystNotes.tsx`, `InvestigationHistory.tsx`, `SemanticLegend.tsx`
- **Purpose**: Intelligence analyst workstation fusing multi-source evidence into hypothesis graphs and object track records.
- **Controls & Features**:
  - **Inquiry Composer (`InvestigationComposer.tsx`)**: Form to launch structured investigations with hypothesis testing templates.
  - **Evidence Fusion Graph (`EvidenceGraph.tsx`)**: Interactive node-link diagram mapping correlations between satellite sightings, RF emissions, radar signatures, and ground reports.
  - **Object Trajectory Tracker (`ObjectTrackPanel.tsx`)**: Tracks moving assets (e.g., naval vessels, aircraft convoys) across sequential passes with velocity vectors.
  - **Data Provenance Panel (`ProvenancePanel.tsx`)**: Cryptographic SHA-256 verification and sensor calibration lineage for court-admissible / military-grade evidence chains.
  - **Analyst Annotations (`AnalystNotes.tsx`)**: Rich text notepad with tagging (`#urgent`, `#basing`, `#coastal`) and export to briefing dossier.

---

#### TAB 7: Persistent Intelligence, Monitoring & Hotspots (`Intel`)
- **Subcomponents**: `IntelligenceWorkspace.tsx`, `IntelligenceDashboard.tsx`, `IntelligenceEventsFeed.tsx`, `EventDetailsCard.tsx`, `IntelligenceSearchWorkspace.tsx`, `AnomalyDiscoveryPanel.tsx`, `HotspotListPanel.tsx`, `MonitoringPanel.tsx`, `InvestigationTemplatesPanel.tsx`
- **Purpose**: 24/7 autonomous surveillance, automated anomaly alerts, and global semantic vector search.
- **Controls & Features**:
  - **Events Feed (`IntelligenceEventsFeed.tsx`)**: Live chronological stream of system-detected events (e.g., `"Unusual radar reflection spike at Galwan Sector"`).
  - **Event Card Actions (`EventDetailsCard.tsx`)**:
    - Lifecycle state transition: `Draft` $\rightarrow$ `Verified` $\rightarrow$ `Escalated` $\rightarrow$ `Closed`.
    - `Split Event` & `Merge Events` buttons.
    - `Focus on Map` button.
  - **Semantic Vector Search (`IntelligenceSearchWorkspace.tsx`)**: Natural-language similarity search finding identical visual/radar patterns across the globe (e.g., `"Find airbases with hardened aircraft shelters similar to this one"`).
  - **Anomaly Discovery Radar (`AnomalyDiscoveryPanel.tsx`)**: Statistical outlier detector highlighting standard deviation spikes in backscatter or thermal readings.
  - **Hotspot Clusters (`HotspotListPanel.tsx`)**: Thermal flare and wildfire clusters with one-click camera jump.
  - **Continuous Surveillance Monitors (`MonitoringPanel.tsx`)**: Active AOI monitors running cron checks on new satellite passes with alert thresholds.

---

#### TAB 8: Analyst Command Center & Dossier (`Workspace`)
- **Subcomponent**: `WorkspaceShell.tsx`
- **Purpose**: Multi-region tactical pinboard, dossier compilation, and briefing generation.
- **Controls & Features**:
  - Pinning evidence cards, observation snapshots, and analysis charts to a digital corkboard.
  - Export briefing dossier to PDF, JSON, and STAC ItemCollection.

---

#### TAB 9: Strategic Waypoint Bookmarks (`Points`)
- **Purpose**: Immediate tactical navigation bookmarks.
- **Controls**:
  - **Central India (Nagpur)**: Jumps to `21.1458° N, 79.0882° E`, Zoom 4.8.
  - **ISRO Headquarters (Bengaluru)**: Jumps to `12.9716° N, 77.5946° E`, Zoom 11.5.
  - **Mumbai Harbor (Naval Dockyard)**: Jumps to `18.9220° N, 72.8347° E`, Zoom 10.5.

---

### GROUP D: Operational Telemetry Status Bar (`ExploreStatusBar.tsx`)
**File Path**: `frontend/components/explore/ExploreStatusBar.tsx`  
**Container Role**: Fixed 28px bottom status bar providing real-time hardware, renderer, and air-gap security telemetry.

- **Visual Elements**:
  - **Renderer Status Dot**:
    - Green (`ready`): `"3D CESIUM READY"` or `"2D MAPLIBRE READY"`.
    - Amber pulsing (`loading`): `"INITIALIZING RENDERER..."`.
    - Red (`error`): `"RENDERER FAULT: [Reason]"`.
  - **GPU Acceleration Indicator (`Cpu`)**:
    - Green/Slate: `"GPU WEBGL ACCELERATED"`.
    - Red: `"GPU ACCELERATION DISABLED"` (indicates fallback to software rendering).
  - **Real-Time Performance Metrics (`Activity`)**:
    - `FPS: [Estimated FPS]` (e.g., `FPS: 60`).
    - `INIT: [Milliseconds]` (e.g., `INIT: 142ms`).
  - **Security Assurance Badge (`ShieldCheck`)**:
    - Emerald green text: `"SHANETRA CLIENT-FIRST"` (confirms air-gapped operations, zero telemetry leaks to foreign clouds).

---

## 4. Hidden, Conditional & Dynamic Features Matrix

| Feature / Element | Component | Default State | Trigger Condition to Reveal | Dismiss / Hide Condition |
| :--- | :--- | :--- | :--- | :--- |
| **Command Activity HUD** | `CommandActivity.tsx` | **Hidden** (`status === 'idle'`) | User submits query in QueryBar | Click `×` button or submit new query |
| **Query Suggestions Chips** | `QuerySuggestions.tsx` | **Hidden/Dynamic** | Query input focused or empty | User types query or selects chip |
| **Query Clear Button (`X`)** | `QueryBar.tsx` | **Hidden** | Text entered in Query input | Input text cleared or query submitted |
| **Floating Sidebar Button** | `ExploreViewport.tsx` | **Visible** | Always visible; icon toggles | Collapses sidebar from 420px to 0px |
| **AOI Clear Button** | `AOIToolbar.tsx` | **Hidden** | `activeAOI !== null` | Click `"Clear"` or execute `CLEAR_AOI` |
| **AOI Area Telemetry** | `AOIToolbar.tsx` | `"No AOI"` | AOI drawn or set via AI | Returns to `"No AOI"` on clear |
| **Temporal Scrubber Timeline** | `Timeline.tsx` | **Hidden** (`observations == 0`) | AOI search returns observations | AOI cleared or reset view |
| **Timeline Play/Pause** | `Timeline.tsx` | `"Play"` (Cyan) | Click Play button | Switches to `"Pause"` (Amber) while playing |
| **Split-Screen Swipe Divider** | `SplitView.tsx` | **Hidden** | `comparisonMode === 'split' && viewMode === '2d'` | Mode changed or Exit Compare clicked |
| **3D Attitude (HDG / PIT)** | `CoordinateHUD.tsx` | **Hidden in 2D** | Active only when `viewMode === '3d'` | Switches to 2D view |
| **Coordinate Copy Indicator** | `CoordinateHUD.tsx` | `Copy` icon | User clicks Copy button | Automatically resets from `Check` after 1.8s |
| **Add Custom Tile Modal** | `ActiveLayers.tsx` | **Hidden** (`showAddModal = false`) | Click `+ Add Custom Tile` button | Submit form or click Cancel |
| **Provider API Keys Modal** | `ActiveLayers.tsx` | **Hidden** (`showKeysModal = false`) | Click `Key / Credentials` button | Click Save or Close |
| **Analysis Progress Bar** | `AnalysisProgress.tsx`| **Hidden** | `isAnalyzing === true` | Analysis finishes or error thrown |
| **Analysis Artifacts Tab** | `AnalysisArtifacts.tsx`| **Hidden / Empty** | Analysis run completes successfully | Reset analysis or start new run |
| **Investigation Composer** | `InvestigationComposer` | **Hidden if open case** | Click `+ New Investigation` button | Submit inquiry or click Cancel |
| **Event Details Slide-In Card**| `EventDetailsCard.tsx` | **Hidden** (`selectedEvent == null`) | Click any event card in feed | Click close button on details card |

---

## 5. Architectural & Design Directives for the Next AI

When redesigning or upgrading the frontend for this page, the designing AI **MUST NOT** break or compromise the following constraints:

1. **Renderer Isolation Must Be Preserved**:
   - Never render `<GlobeView />` (Cesium) and `<MapView />` (MapLibre) in the DOM simultaneously. They share WebGL GPU context and will crash low-memory or browser instances if concurrent.
2. **Downward Perspective Angle (`-50.0°`)**:
   - In Cesium, a pitch of `0.0°` points horizontally at the sky and distant haze. Always enforce downward bird's-eye pitch between `-45°` and `-60°` for regional city targets.
3. **Keep Client-First Air-Gapped Security**:
   - Any credentials (Cesium token, Google API key) must live strictly in browser `localStorage`. Do not route them through third-party analytics.
4. **Preserve HUD Coordinate Precision**:
   - Military and EO analysts rely on 4-decimal precision coordinates (`0.0001°` $\approx$ 11 meters ground resolution). Do not truncate or round them to simple integers.
5. **Retain Keyboard Shortcuts & Accessibility**:
   - `Enter` key must trigger query submission; `Esc` should dismiss active draw modes and modals.
