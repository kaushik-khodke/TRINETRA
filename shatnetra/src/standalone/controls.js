import { StyleManager } from '../ui.js';
import { flyToAustin } from '../camera.js';

/** Construct the existing controls and camera presentation. */
export function createStandaloneControls({
  scene: { viewer, mapStackController },
  loaderStatus,
  defer,
}) {
  // Initialize the style manager (post-processing, HUD, locations, share links)
  const styleManager = new StyleManager(viewer, { mapStackController });
  defer(() => styleManager.orbitController.stop());
  defer(() => styleManager.hud.destroy());
  defer(() => styleManager.dispose());
  // The previous multi-canvas weather compositor remains disabled.
  const weatherEffects = null;
  const cockpitCloudEffects = null;

  // If no share link state, do default fly-to Austin
  if (!styleManager.hasShareState) {
    loaderStatus.textContent = 'Flying to Austin, TX...';
    defer(flyToAustin(viewer));
  } else {
    loaderStatus.textContent = 'Restoring shared view...';
  }

  return { styleManager, weatherEffects, cockpitCloudEffects };
}
