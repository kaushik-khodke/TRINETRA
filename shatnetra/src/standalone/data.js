import { DataLayerManager } from '../data/manager.js';
import earthquakesLayer from '../data/earthquakes.js';
import satellitesLayer from '../data/satellites.js';
import { LAYER_STATE_REGISTRY } from '../data/layerState.js';

/** Register the standalone layer catalog before allowing state restoration. */
export function createStandaloneData({
  scene: { viewer },
  controls: { styleManager },
  allowQaRegistration,
  defer,
}) {
  // Initialize data layer manager
  const dataManager = new DataLayerManager(viewer, {
    allowQaRegistration,
  });
  defer(async () => {
    await dataManager.destroyAll();
    if (dataManager.layers.size)
      throw new Error(
        `Data layers could not be destroyed: ${[...dataManager.layers.keys()].join(', ')}`,
      );
  });
  dataManager.register(earthquakesLayer);
  dataManager.register(satellitesLayer);
  // Restoration starts only after the complete production registry is sealed.
  dataManager.finalizeRegistrations(LAYER_STATE_REGISTRY);
  if (allowQaRegistration) {
    window.__gevQaRegisterLayer = (targetManager, layerModule) => {
      if (targetManager !== dataManager)
        throw new Error('QA layer manager mismatch');
      return dataManager.registerForQa(layerModule);
    };
    window.__gevQaUnregisterLayer = (targetManager, layerId) => {
      if (targetManager !== dataManager)
        throw new Error('QA layer manager mismatch');
      return dataManager.unregisterForQa(layerId);
    };
    const register = window.__gevQaRegisterLayer;
    const unregister = window.__gevQaUnregisterLayer;
    defer(() => {
      if (window.__gevQaRegisterLayer === register)
        delete window.__gevQaRegisterLayer;
      if (window.__gevQaUnregisterLayer === unregister)
        delete window.__gevQaUnregisterLayer;
    });
  }
  dataManager.buildTogglePanel(document.getElementById('data-toggles'));
  styleManager.attachDataManager(dataManager);

  return { dataManager };
}
