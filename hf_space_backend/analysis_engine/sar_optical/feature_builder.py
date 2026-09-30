"""
TRINETRA Analysis Engine — Cross-Modal Feature Builder
Extracts complementary spectral (optical) and microwave backscatter (SAR) features.
"""

from typing import Dict, Any, Tuple
import numpy as np


class CrossModalFeatureBuilder:
    @staticmethod
    def extract_features(
        opt_arr: np.ndarray,
        sar_db: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Extracts multi-modal indicators:
        - Optical: Water (low red/NIR, high green), Vegetation (high NIR/red)
        - SAR: Inundated / specular water (low backscatter < -18 dB), Built-up / structures (high backscatter > -8 dB)
        """
        # Optical analysis
        # If multi-channel [R, G, B, (NIR)]
        if opt_arr.ndim == 3 and opt_arr.shape[2] >= 3:
            red = opt_arr[:, :, 0].astype(np.float32)
            green = opt_arr[:, :, 1].astype(np.float32)
            blue = opt_arr[:, :, 2].astype(np.float32)
            # Pseudo NDWI (Green - NIR or Green - Red)
            denom = (green + red) + 1e-6
            ndwi_proxy = (green - red) / denom
            opt_water_ratio = float(np.mean(ndwi_proxy > 0.05))
        else:
            opt_water_ratio = float(np.mean(opt_arr < 0.1))

        # SAR radar backscatter analysis
        # Radar specular reflection on smooth water creates very low backscatter (< -18 dB)
        sar_water_ratio = float(np.mean(sar_db < -18.0))
        # Urban double-bounce dihedral scattering creates very high backscatter (> -8 dB)
        sar_urban_ratio = float(np.mean(sar_db > -8.0))

        # Cross-modal agreement score
        # Agreement is high when both sensors agree on water extent or optical confirms SAR findings
        water_diff = abs(opt_water_ratio - sar_water_ratio)
        agreement_score = round(max(0.1, 1.0 - (water_diff * 1.5)), 3)

        return {
            "optical_water_ratio": round(opt_water_ratio, 4),
            "sar_water_ratio": round(sar_water_ratio, 4),
            "sar_urban_ratio": round(sar_urban_ratio, 4),
            "mean_backscatter_db": round(float(np.mean(sar_db)), 2),
            "cross_modal_agreement": agreement_score,
        }
