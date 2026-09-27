"""
TRINETRA Analysis Engine — Connected Component Region Extraction & Vectorization
Extracts discrete spatial clusters from binary change masks, filters noise (< min_pixels),
and vectorizes them into valid GeoJSON polygons.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from analysis_engine.evidence.models import ChangeRegionEvidence

try:
    from scipy.ndimage import label, find_objects
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


class ChangeRegionExtractor:
    @staticmethod
    def extract_regions(
        change_mask: np.ndarray,
        bounds_wgs84: List[float],
        pixel_size_meters: float = 10.0,
        min_pixels: int = 20,
        confidence_map: Optional[np.ndarray] = None,
    ) -> List[ChangeRegionEvidence]:
        """
        Extracts vectorized ChangeRegionEvidence polygons from the binary change mask.
        """
        H, W = change_mask.shape[:2]
        min_lon, min_lat, max_lon, max_lat = bounds_wgs84

        lon_step = (max_lon - min_lon) / W if W > 0 else 0.0001
        lat_step = (max_lat - min_lat) / H if H > 0 else 0.0001
        pixel_area_m2 = pixel_size_meters * pixel_size_meters

        regions: List[ChangeRegionEvidence] = []

        if HAS_SCIPY:
            labeled_arr, num_features = label(change_mask)
            slices = find_objects(labeled_arr)

            for idx, slc in enumerate(slices):
                if slc is None:
                    continue

                region_mask = (labeled_arr[slc] == (idx + 1))
                pixel_count = int(np.sum(region_mask))
                if pixel_count < min_pixels:
                    continue

                y_slice, x_slice = slc
                y0, y1 = y_slice.start, y_slice.stop
                x0, x1 = x_slice.start, x_slice.stop

                # Spatial bounds for this component
                r_min_lon = min_lon + (x0 * lon_step)
                r_max_lon = min_lon + (x1 * lon_step)
                # Note: y=0 is top (max_lat), y=H is bottom (min_lat)
                r_max_lat = max_lat - (y0 * lat_step)
                r_min_lat = max_lat - (y1 * lat_step)

                c_lon = (r_min_lon + r_max_lon) / 2.0
                c_lat = (r_min_lat + r_max_lat) / 2.0

                area_m2 = round(pixel_count * pixel_area_m2, 2)
                area_ha = round(area_m2 / 10000.0, 3)

                conf = 0.85
                if confidence_map is not None:
                    conf = float(np.mean(confidence_map[y0:y1, x0:x1][region_mask]))

                # Create closed polygon geometry
                polygon_coords = [
                    [
                        [r_min_lon, r_min_lat],
                        [r_max_lon, r_min_lat],
                        [r_max_lon, r_max_lat],
                        [r_min_lon, r_max_lat],
                        [r_min_lon, r_min_lat],
                    ]
                ]

                region_id = f"E_CHG{len(regions)+1:02d}"
                regions.append(
                    ChangeRegionEvidence(
                        id=region_id,
                        label=f"Change Cluster #{len(regions)+1}",
                        area_m2=area_m2,
                        area_ha=area_ha,
                        pixel_count=pixel_count,
                        centroid=[round(c_lon, 6), round(c_lat, 6)],
                        bbox=[round(r_min_lon, 6), round(r_min_lat, 6), round(r_max_lon, 6), round(r_max_lat, 6)],
                        geometry={"type": "Polygon", "coordinates": polygon_coords},
                        confidence=round(conf, 4),
                        change_score=round(min(1.0, pixel_count / (min_pixels * 5)), 3),
                    )
                )
        else:
            # Fallback when scipy is unavailable: single bounding box
            pixel_count = int(np.sum(change_mask))
            if pixel_count >= min_pixels:
                area_m2 = round(pixel_count * pixel_area_m2, 2)
                polygon_coords = [
                    [
                        [min_lon, min_lat],
                        [max_lon, min_lat],
                        [max_lon, max_lat],
                        [min_lon, max_lat],
                        [min_lon, min_lat],
                    ]
                ]
                regions.append(
                    ChangeRegionEvidence(
                        id="E_CHG01",
                        label="Change Cluster #01",
                        area_m2=area_m2,
                        area_ha=round(area_m2 / 10000.0, 3),
                        pixel_count=pixel_count,
                        centroid=[round((min_lon + max_lon) / 2.0, 6), round((min_lat + max_lat) / 2.0, 6)],
                        bbox=[min_lon, min_lat, max_lon, max_lat],
                        geometry={"type": "Polygon", "coordinates": polygon_coords},
                        confidence=0.85,
                        change_score=0.8,
                    )
                )

        return regions
