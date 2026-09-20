"""
TRINETRA Analysis Engine — Grounding Specialist Adapter
Adapts the existing RSGroundingSpecialist to the Explore Analysis Engine.
Extracts grounded bounding boxes and polygons into standardized GroundingEvidence.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from services.grounding.grounding_service import RSGroundingSpecialist
from analysis_engine.evidence.models import GroundingEvidence


class GroundingSpecialistAdapter:
    def __init__(self):
        self.specialist = RSGroundingSpecialist()

    def locate_features(
        self,
        image_arr: np.ndarray,
        meta: Dict[str, Any],
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[GroundingEvidence]:
        """
        Executes text-guided spatial localization and normalizes detections into GroundingEvidence.
        """
        params = parameters or {}
        raw_res = self.specialist.execute(
            image_arr=image_arr,
            meta=meta,
            query=query,
            parameters=params,
        )

        detections: List[GroundingEvidence] = []
        raw_regions = raw_res.get("regions", [])

        for idx, r in enumerate(raw_regions):
            bbox = r.get("bbox", [0.0, 0.0, 1.0, 1.0])
            conf = float(r.get("confidence", 0.85))
            label_text = r.get("label", f"Detected Feature #{idx+1}")

            # Format normalized polygon
            ymin, xmin, ymax, xmax = bbox
            geom = {
                "type": "Polygon",
                "coordinates": [
                    [
                        [xmin, ymin],
                        [xmax, ymin],
                        [xmax, ymax],
                        [xmin, ymax],
                        [xmin, ymin],
                    ]
                ],
            }

            detections.append(
                GroundingEvidence(
                    id=f"E_GRD{idx+1:02d}",
                    label=label_text,
                    bbox=bbox,
                    geometry=geom,
                    confidence=round(conf, 4),
                    source_model="RSGroundingSpecialist",
                )
            )

        return detections
