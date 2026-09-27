/**
 * TRINETRA / Shanetra Explore Architecture
 * Layer Adapter
 * Phase 2: Converts backend layer models and datasets into renderer-neutral ExploreLayerDefinitions.
 */

import { ExploreDataset, ExploreLayerDefinition } from "./types"

export class LayerAdapter {
  static fromDataset(dataset: ExploreDataset, tileTemplate?: string): ExploreLayerDefinition {
    const assetKey = Object.keys(dataset.assets)[0]
    const assetId = assetKey ? dataset.assets[assetKey].id : dataset.id

    return {
      id: `layer-${assetId}`,
      label: dataset.title || `Observation ${dataset.id.slice(0, 12)}`,
      category: "imagery",
      rendererSupport: ["2d", "3d"],
      sourceType: "raster",
      tileTemplate: tileTemplate || `/api/v1/explore/tiles/layer-${assetId}/{z}/{x}/{y}.png`,
      minZoom: 0,
      maxZoom: 20,
      defaultVisible: true,
      userControllable: true,
      aiControllable: true,
      expensive: false,
      opacity: 1.0,
      attribution: `TRINETRA / ${dataset.provider.toUpperCase()} (${dataset.collection || "EO"})`,
      assetId: assetId,
    }
  }
}
