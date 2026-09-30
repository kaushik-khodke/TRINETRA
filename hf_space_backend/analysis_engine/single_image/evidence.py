"""
TRINETRA Analysis Engine — Single-Image Evidence Normalizer
Transforms raw specialist outputs into standardized EvidencePack components.
"""

from typing import Dict, Any, List
import numpy as np
from analysis_engine.evidence.models import SpectralEvidence, GroundingEvidence


class SingleImageEvidenceNormalizer:
    @staticmethod
    def extract_spectral_evidence(
        image_arr: np.ndarray,
    ) -> List[SpectralEvidence]:
        """
        Computes standard spectral evidence metrics (e.g. mean reflectance, brightness).
        """
        evidence_list = []

        if image_arr.ndim == 3 and image_arr.shape[2] >= 3:
            r = float(np.mean(image_arr[:, :, 0]))
            g = float(np.mean(image_arr[:, :, 1]))
            b = float(np.mean(image_arr[:, :, 2]))

            evidence_list.append(
                SpectralEvidence(
                    id="E_SPEC01",
                    index_name="Mean RGB Radiance",
                    mean_value_a=round((r + g + b) / 3.0, 3),
                    interpretation="Average visible spectrum surface brightness",
                )
            )

        return evidence_list
