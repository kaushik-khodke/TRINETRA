# TRINETRA 3D Earth Globe Integration Specification

**Product**: SatQuery AI (SIH 2026 Problem Statement 26167)  
**Geospatial Visualization Engine**: TRINETRA (CesiumJS 3D Photorealistic Earth Globe)  
**Status**: Integrated & Verified  
**Date**: September 2026  

---

## 1. Architectural Strategy & Decision

SatQuery AI and TRINETRA are maintained as **two independently runnable, loosely coupled web applications**:

* **Project A (SatQuery AI Main Product)**:
  * **Frontend**: Next.js 14 (React, TypeScript, Lucide Icons, Glassmorphism UI) running on port `3000`.
  * **Backend**: FastAPI (Python 3.12, Uvicorn, Algorithmic CV & Multimodal Reasoning, Local Ollama LLM) running on port `8000`.
* **Project B (TRINETRA / STATNETRA 3D Earth Engine)**:
  * **Frontend**: Vite SPA + CesiumJS `1.124.0` (Photorealistic 3D Earth, Space-to-Ground Camera Dynamics, Map Engine, Satellite Orbits, Seismic Feeds) running on port `4173`.

### Why Decoupled Integration Outperformed Merging or Iframes

| Evaluation Vector | Option A: Monolithic Merge | Option C: Iframe Embedding | **Option B/E: Decoupled URL Contract (Selected)** |
| :--- | :--- | :--- | :--- |
| **Tech Stack Isolation** | **Failed**: Cesium bundler conflicts with Next.js SSR/Webpack/Turbopack. | High isolation. | **Complete Isolation**: Next.js and Vite remain standalone. |
| **Node Modules** | **High Risk**: Conflicting Cesium and React 18 dependencies, ballooning size. | Separate modules. | **Independent Modules**: Zero dependency contamination. |
| **Security & Headers** | N/A | **Blocked**: TRINETRA enforces `X-Frame-Options: DENY` and CSP `frame-ancestors 'none'`. | **Compliant**: Clean new-tab window navigation (`noopener,noreferrer`). |
| **WebGL Performance** | Reduced GPU scheduling efficiency. | Throttled inside iframe canvas. | **Full Native GPU**: Dedicated WebGL 2.0 context with hardware acceleration. |
| **User Experience** | Cluttered UI; globe fighting with workspace panels. | Constrained view box. | **Full Immersion**: Space-to-ground camera descent, 3D tiles, and full tactical HUD. |
| **Failure Isolation** | WebGL crash kills entire analysis session. | Partial isolation. | **Total Fault Isolation**: Neither app can crash the other. |

---

## 2. Location Data Flow

```text
       [ User Uploads Satellite Imagery ]
                     │
                     ▼
  [ OGC GeoTIFF Reader (ModelTiepoint & ModelPixelScale) ]
         │                                       │
   (Valid CRS Metadata)                  (Un-georeferenced)
         │                                       │
         ▼                                       ▼
  Derive Exact WGS-84 Center            has_geographic_location: false
  & Bounding Box (No Mocking)           (Do NOT fabricate coordinates)
         │                                       │
         ▼                                       ▼
 [ Backend Agent & Model Execution ]      [ Backend Response Payload ]
         │                                       │
         ▼                                       ▼
  geographic_location Object              geographic_location: {
  { lat, lng, height, bounds, crs }          has_location: false,
         │                                   lat: null, lng: null
         │                                }
         ▼                                       │
  SatQuery AI Frontend Result View               ▼
         │                               "View on Globe" Disabled
         ▼                               Explains: "Non-geospatial image"
  "View on Globe (TRINETRA)"
  Button Appears
         │
         │ (User clicks action)
         ▼
  buildTrinetraUrl(geo, targetName)
  window.open(url, "_blank")
         │
         ▼
  TRINETRA /explore Route Loads
         │
         ▼
  ShareLinkManager parses search params (?lat=...&lng=...&height=...)
  Validates: -90 <= lat <= 90 and -180 <= lng <= 180
         │
         ▼
  1. 3D Earth Globe initializes in space
  2. Tactical Entity added: Cyan marker "⦿ Delhi NCR [SatQuery AI Target]"
  3. Image Footprint added: Subtle cyan bounding box on terrain
  4. Cesium Camera flies smoothly from orbit down to target location
  5. Globe-to-Map photoreal transition engages automatically
```

---

## 3. Location Contract Specification

### Target Endpoint
* Route: `/explore` (or `/` with query parameters)
* Protocol: `GET`

### Query Parameter Schema

| Parameter | Type | Required | Range / Format | Description |
| :--- | :--- | :--- | :--- | :--- |
| `lat` | `float` | **Yes** | `[-90.0, 90.0]` | WGS-84 latitude of scene center. |
| `lng` / `lon` | `float` | **Yes** | `[-180.0, 180.0]` | WGS-84 longitude of scene center. |
| `height` / `alt`| `integer` | No | `[100, 25000000]` | Camera altitude above ellipsoid in meters (default: `5000`). |
| `zoom` | `integer` | No | `[1, 20]` | Optional zoom level (maps dynamically to camera altitude if height omitted). |
| `source` | `string` | No | Alphanumeric | Originating service (e.g. `satquery`). |
| `name` / `label`| `string` | No | String | Display name for the tactical pin (e.g. `sample_optical.tif` or `Delhi NCR`). |
| `bbox` | `string` | No | `minLon,minLat,maxLon,maxLat` | Geographic bounding box coordinates for image footprint rectangle. |
| `imageId` | `string` | No | String | Unique raster identifier. |
| `modality` | `string` | No | `OPTICAL`, `SAR`, etc. | Sensor modality. |
| `date` | `string` | No | `YYYY-MM-DD` | Acquisition date of the evidence scene. |

### Example Contract URL
```http
http://localhost:4173/explore?lat=28.61720&lng=77.20780&height=5000&source=satquery&name=Delhi+NCR&bbox=77.1950,28.6044,77.2206,28.6300
```

---

## 4. OGC GeoTIFF Georeferencing Extraction

In remote-sensing workflows, raster coordinates are embedded within standard TIFF directory tags:
1. **ModelPixelScaleTag (`33550`)**: Contains `[scale_x, scale_y, scale_z]` specifying geographic degrees/meters per pixel.
2. **ModelTiepointTag (`33922`)**: Maps pixel `(i, j, k)` to world coordinate `(x, y, z)`.
3. **GeoKeyDirectoryTag (`34735`)**: Declares the Coordinate Reference System (CRS), typically WGS-84 Geographic (`EPSG:4326`) or Projected UTM.

`backend/geospatial/reader.py` extracts these native tags via Pillow without external heavy GDAL binaries. 
Center coordinates are calculated via:
$$\text{center\_lat} = \frac{\min(\text{lat}) + \max(\text{lat})}{2}, \quad \text{center\_lng} = \frac{\min(\text{lng}) + \max(\text{lng})}{2}$$

### Strict Handling of Un-georeferenced Images
When an image (such as standard PNG, JPEG, or un-referenced TIFF) does not contain valid tiepoints or geokeys:
* `has_geographic_location` is strictly set to `False`.
* `lat`, `lng`, and `bounds` are `None`.
* **Zero fabricated coordinates**: SatQuery AI never invents mock coordinates.
* The frontend UI disables the button and displays:  
  *`Georeferencing Unavailable (Non-geospatial image)`*.

---

## 5. Security & Input Sanitization

* **Range Verification**: Coordinates outside `[-90, 90]` or `[-180, 180]` are rejected before camera manipulation.
* **Type Safety**: Parameters are parsed with `Number.isFinite()`; non-numeric inputs like `lat=hello` fail gracefully without application errors.
* **XSS Prevention**: Labels are rendered exclusively via Cesium's canvas-backed text renderer and React JSX escaping; raw HTML injection is prevented.
* **No Secret Leakage**: No internal filesystem paths, auth tokens, or API keys are placed in URL parameters.
* **Secure Navigation**: External window opening uses `rel="noopener,noreferrer"`.

---

## 6. Local Development & Deployment Configuration

### Running Locally

```bash
# 1. Start FastAPI Backend (Port 8000)
cd backend
python run_backend.py

# 2. Start SatQuery AI Frontend (Port 3000)
cd frontend
npm run dev

# 3. Start TRINETRA 3D Earth Globe (Port 4173)
cd shatnetra
npm run dev
```

### Environment Configuration

In `frontend/.env.local`:
```bash
# Development
NEXT_PUBLIC_TRINETRA_URL=http://localhost:4173

# Production
# NEXT_PUBLIC_TRINETRA_URL=https://globe.satquery.ai
```

---

## 7. Future Extensibility Roadmap

The integration interface is engineered to support incremental advanced geospatial overlays:
1. **Change Map Shaders**: Overlaying differential raster heatmaps from bi-temporal comparisons.
2. **Grounding Bounding Polygons**: Projecting AI-detected bounding boxes directly onto 3D Cesium terrain.
3. **Multi-temporal Image Footprints**: Visualizing the spatial overlap of optical and SAR satellite paths.
4. **Interactive Evidence Inspecting**: Clicking the target marker on the globe to inspect the SatQuery reasoning telemetry.
