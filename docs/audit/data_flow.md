# TRINETRA Data Flow Audit (Stage 1)

## 1. End-to-End Processing Pipeline

The following sequence illustrates the flow of data through TRINETRA from user submission to evidence presentation:

```
[ User Raster Upload: GeoTIFF / PNG / Array ]
                        │
                        ▼
            ┌───────────────────────┐
            │   Geospatial Ingest   │
            │  backend/geospatial/  │
            └───────────┬───────────┘
                        │
                        ├─► Extract CRS, Transform, Bounds, Nodata
                        ├─► Band metadata extraction (RGB / Multispectral / SAR)
                        ├─► Percentile-based radiometric normalization
                        │
                        ▼
            ┌───────────────────────┐
            │     Task Routing      │
            │ backend/app/main.py   │
            └───────────┬───────────┘
                        │
                        ├─► Query analysis (NLP / regex keywords)
                        ├─► Modality verification (Single, Bi-temporal, Optical+SAR, Hyperspectral)
                        │
                        ▼
            ┌───────────────────────┐
            │ Specialist Dispatcher │
            │  backend/services/    │
            └───────────┬───────────┘
                        │
       ┌────────────────┴────────────────┐
       ▼                                 ▼
┌───────────────────────────┐     ┌───────────────────────────┐
│ Neural Network Path       │     │ Heuristic Fallback Path   │
│ (if checkpoint verified)  │     │ (if checkpoint missing)   │
├───────────────────────────┤     ├───────────────────────────┤
│ 1. Verify model SHA-256   │     │ 1. Calculate radiometric  │
│ 2. Preprocess tensors     │     │    spectral indices       │
│ 3. Forward pass (eval)    │     │ 2. Statistical threshold  │
│ 4. Extract class logits   │     │ 3. Set fallback_used=True │
└─────────────┬─────────────┘     └─────────────┬─────────────┘
              │                                 │
              └────────────────┬────────────────┘
                               │
                               ▼
            ┌───────────────────────┐
            │ Evidence & Overlays   │
            │  backend/geospatial/  │
            └───────────┬───────────┘
                        │
                        ├─► Render difference heatmaps / cross-modal composites
                        ├─► Generate base64 visual overlays
                        │
                        ▼
            ┌───────────────────────┐
            │   LLM Synthesizer     │
            │  backend/services/    │
            └───────────┬───────────┘
                        │
                        ├─► Ground answer strictly in computed features & evidence
                        ├─► Attach empirical or uncalibrated confidence rating
                        │
                        ▼
            ┌───────────────────────┐
            │ Final Response Record │
            │      (JSON API)       │
            └───────────────────────┘
```

---

## 2. Experimental QML Data Flow

When QML is enabled for bi-temporal change analysis:

```
Real Satellite T1/T2 Rasters
       │
       ▼
Classical Feature Extraction (Deep Embeddings / Spectral Deltas)
       │
       ▼
StandardScaler + PCA (Fit strictly on training set)
       │
       ▼
4 to 8 Normalized Features (Hilbert Space Input Angles)
       │
       ▼
AngleEmbedding (Ry rotations on N qubits)
       │
       ▼
StronglyEntanglingLayers (Parameterized quantum rotations & CNOTs)
       │
       ▼
Pauli-Z Expectation Measurements [-1.0, 1.0]
       │
       ▼
Linear Classification Head (Softmax logits)
       │
       ▼
Agreement Analysis with Classical Specialist (Track concordances & discordances)
```

---

## 3. Data Integrity & Leakage Verification Points

1. **Preprocessing Isolation**:
   - Scalers and PCA transforms must never be fit on validation or test sets.
   - Spatial block splitting must be enforced for hyperspectral and change-detection benchmarks to avoid spatial autocorrelation leakage.
2. **Metadata Transparency**:
   - Every API output payload must record:
     - `engine`: exact model name or heuristic fallback
     - `fallback_used`: boolean
     - `fallback_reason`: description if fallback was invoked
     - `confidence`: empirical confidence score
     - `evidence`: verifiable visual overlays and data statistics
