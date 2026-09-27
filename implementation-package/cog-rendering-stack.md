# Frontend Cloud-Optimized GeoTIFF Rendering Stack

## Recommended stack

| Concern | Choice |
|---|---|
| Web framework | React + TypeScript |
| Map renderer | MapLibre GL JS |
| COG source adapter | `@geomatico/maplibre-cog-protocol` |
| Browser GeoTIFF decoding | `geotiff.js` |
| Local application state | Zustand |
| Server/cache state | TanStack Query |
| Runtime response validation | Zod |
| Heavy processing | GDAL/rasterio in containerized workers |
| Server tile fallback | TiTiler |
| Raster format | Cloud-Optimized GeoTIFF |
| Vector overlays | MapLibre vector sources; PMTiles where useful |
| Charts | Observable Plot or Apache ECharts |

## Rendering path

```text
MapLibre GL JS
  → COG protocol source
  → HTTP Range request
  → COG overview/tile
  → geotiff.js decode
  → WebGL texture/shader
  → color ramp + opacity + legend
```

## Client-side COG use

Use browser range reads for user-owned COGs, interactive inspection, and a moderate number of visible layers. The backend must issue short-lived signed URLs and configure CORS plus `Accept-Ranges: bytes`.

Use TiTiler/server-side tiles for complex band expressions, repeated shared views, unreliable remote sources, large temporal stacks, or strict policies that should not expose source URLs.

## Large-raster rules

- Never load an entire raster for map display.
- Require internal tiling and overviews.
- Request only visible windows.
- Cancel stale viewport requests.
- Limit concurrent range requests per layer.
- Cache immutable asset-version tiles.
- Use server-side statistics for large histograms and summaries.
- Keep scientific numeric rasters separate from display derivatives.
- Record nodata, scale, offset, band names, units, data type, and overview levels.

## COG creation

For continuous data:

```bash
gdal_translate input.tif output.cog.tif \
  -of COG \
  -co COMPRESS=DEFLATE \
  -co BIGTIFF=IF_SAFER \
  -co BLOCKSIZE=512 \
  -co OVERVIEWS=IGNORE_EXISTING \
  -co RESAMPLING=AVERAGE
```

For categorical data, use nearest-neighbor or mode. Do not average class labels. For scientific float outputs, preserve precision, nodata, scale, and offset.

## Frontend layer model

```ts
export type RasterLayerConfig = {
  assetVersionId: string;
  sourceUrl: string;
  kind: 'continuous' | 'categorical' | 'rgb';
  bands: number[];
  nodata?: number;
  min?: number;
  max?: number;
  colorRamp?: string[];
  opacity: number;
  resampling: 'nearest' | 'bilinear' | 'average';
};
```

The backend should calculate safe defaults. The UI should expose them when they affect interpretation.

## Glassmorphism UI guidance

Use glassmorphism only for utility panels over the map:

- Deep navy/graphite base.
- Translucent navy panels.
- `backdrop-filter: blur(16px)`.
- 1px low-contrast borders.
- Teal/cyan active state.
- Amber warnings.
- Coral failures.
- No purple or cyberpunk neon.
- Provide a solid-surface accessibility mode.

```css
.glass-panel {
  background: rgba(14, 31, 48, 0.72);
  border: 1px solid rgba(179, 225, 231, 0.14);
  border-radius: 14px;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.24);
  backdrop-filter: blur(16px);
}
```
