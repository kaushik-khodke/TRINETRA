"""
TRINETRA — Multi-Region Spatial Detector & Filter Engine
Extracts connected components, applies Non-Maximum Suppression (NMS),
filters by spatial constraints and rankings, and generates GeoJSON geometries.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from scipy import ndimage
from services.grounding.spatial_interpreter import SpatialQueryIntent

class RegionDetector:
    """Multi-region connected-component extractor and spatial constraint engine."""

    @staticmethod
    def compute_iou(boxA: List[float], boxB: List[float]) -> float:
        """Calculates Intersection-over-Union between two normalized [ymin, xmin, ymax, xmax] boxes."""
        yA = max(boxA[0], boxB[0])
        xA = max(boxA[1], boxB[1])
        yB = min(boxA[2], boxB[2])
        xB = min(boxA[3], boxB[3])

        inter_area = max(0.0, yB - yA) * max(0.0, xB - xA)
        boxA_area = max(1e-6, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
        boxB_area = max(1e-6, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

        iou = inter_area / float(boxA_area + boxB_area - inter_area)
        return float(iou)

    @staticmethod
    def apply_nms(boxes: List[Dict[str, Any]], iou_threshold: float = 0.40) -> List[Dict[str, Any]]:
        """Non-Maximum Suppression to eliminate duplicate or overlapping candidate regions."""
        if not boxes:
            return []

        # Sort boxes descending by score
        sorted_boxes = sorted(boxes, key=lambda b: b.get("score", 0.0), reverse=True)
        selected: List[Dict[str, Any]] = []

        for candidate in sorted_boxes:
            suppress = False
            cand_bbox = candidate["bbox"]
            for existing in selected:
                exist_bbox = existing["bbox"]
                if RegionDetector.compute_iou(cand_bbox, exist_bbox) > iou_threshold:
                    suppress = True
                    break
            if not suppress:
                selected.append(candidate)

        return selected

    @staticmethod
    def determine_relative_location(yc: float, xc: float) -> str:
        """Translates normalized centroid coordinates (0..1) into military/analyst spatial quadrants."""
        v_pos = "North" if yc < 0.38 else ("South" if yc > 0.62 else "Central")
        h_pos = "West" if xc < 0.38 else ("East" if xc > 0.62 else "Central")

        if v_pos == "Central" and h_pos == "Central":
            return "Center of image"
        if v_pos == "Central":
            return f"{h_pos}ern corridor"
        if h_pos == "Central":
            return f"{v_pos}ern sector"
        return f"{v_pos}-{h_pos} quadrant"

    @classmethod
    def extract_regions_from_mask(
        cls,
        binary_mask: np.ndarray,
        h: int,
        w: int,
        label: str,
        meta: Optional[Dict[str, Any]] = None,
        intent: Optional[SpatialQueryIntent] = None,
        min_pixel_ratio: float = 0.0015  # min 0.15% of total pixels to filter tiny noise
    ) -> List[Dict[str, Any]]:
        """
        Extracts multiple connected components from a binary mask,
        applies spatial constraint filtering, NMS, ranking, and formats structured regions.
        """
        if not np.any(binary_mask):
            return []

        # 1. Connected components labeling
        labeled_arr, num_features = ndimage.label(binary_mask)
        if num_features == 0:
            return []

        slices = ndimage.find_objects(labeled_arr)
        total_pixels = h * w
        min_pixels = int(total_pixels * min_pixel_ratio)

        # Ground sampling distance & geo-referencing from meta
        meta = meta or {}
        bounds = meta.get("bounds")  # (min_lon, min_lat, max_lon, max_lat)
        has_geo = meta.get("has_geographic_location", False) or bool(bounds)

        # Estimate pixel resolution in meters
        pixel_res_m = 10.0  # default 10m Sentinel-2 resolution
        if bounds and len(bounds) == 4:
            min_lon, min_lat, max_lon, max_lat = bounds
            # Rough degree to meter approximation
            lat_m = abs(max_lat - min_lat) * 111320.0
            lon_m = abs(max_lon - min_lon) * (111320.0 * np.cos(np.radians((min_lat + max_lat) / 2.0)))
            if h > 0 and w > 0 and lat_m > 0 and lon_m > 0:
                pixel_res_m = float((lat_m / h + lon_m / w) / 2.0)

        raw_regions: List[Dict[str, Any]] = []

        for idx, slc in enumerate(slices):
            if slc is None:
                continue

            component_mask = (labeled_arr[slc] == (idx + 1))
            pixel_area = int(np.sum(component_mask))
            if pixel_area < min_pixels and (not intent or intent.geometry != "point"):
                continue

            y_slice, x_slice = slc
            ymin = float(y_slice.start / h)
            ymax = float(y_slice.stop / h)
            xmin = float(x_slice.start / w)
            xmax = float(x_slice.stop / w)

            # Padding
            pad_y = 0.01
            pad_x = 0.01
            ymin_n = round(max(0.01, ymin - pad_y), 3)
            xmin_n = round(max(0.01, xmin - pad_x), 3)
            ymax_n = round(min(0.99, ymax + pad_y), 3)
            xmax_n = round(min(0.99, xmax + pad_x), 3)

            # Centroid
            cy_local, cx_local = ndimage.center_of_mass(component_mask)
            yc = float((y_slice.start + cy_local) / h)
            xc = float((x_slice.start + cx_local) / w)

            # Geographic coordinates if available
            geo_centroid = {"lat": None, "lng": None}
            if has_geo and bounds and len(bounds) == 4:
                min_lon, min_lat, max_lon, max_lat = bounds
                geo_lat = round(max_lat - yc * (max_lat - min_lat), 6)
                geo_lng = round(min_lon + xc * (max_lon - min_lon), 6)
                geo_centroid = {"lat": geo_lat, "lng": geo_lng}

            # Physical area
            physical_area_m2 = round(pixel_area * (pixel_res_m ** 2), 1) if has_geo else None

            # Polygon contour vertices (downsampled bounding contour)
            # Sample bounding polygon: [top-left, top-right, bottom-right, bottom-left, top-left]
            polygon_coords = [
                [xmin_n, ymin_n],
                [xmax_n, ymin_n],
                [xmax_n, ymax_n],
                [xmin_n, ymax_n],
                [xmin_n, ymin_n]
            ]

            # Confidence score calculation: density and size
            box_area = max(1e-5, (ymax_n - ymin_n) * (xmax_n - xmin_n))
            density = min(1.0, pixel_area / (box_area * total_pixels))
            score = round(min(0.97, max(0.72, 0.70 + 0.20 * density + 0.05 * min(1.0, pixel_area / (total_pixels * 0.1)))), 2)

            relative_loc = cls.determine_relative_location(yc, xc)

            raw_regions.append({
                "label": label,
                "geometry_type": intent.geometry if intent else "bbox",
                "bbox": [ymin_n, xmin_n, ymax_n, xmax_n],
                "score": score,
                "centroid": geo_centroid,
                "centroid_norm": {"y": round(yc, 3), "x": round(xc, 3)},
                "pixel_area": pixel_area,
                "physical_area_m2": physical_area_m2,
                "relative_location": relative_loc,
                "polygon_coords": polygon_coords,
                "evidence": []
            })

        # 2. Filter by Spatial Directional Constraint (if present in intent)
        filtered_by_space = raw_regions
        if intent and intent.region_constraint:
            c = intent.region_constraint
            filtered_by_space = []
            for r in raw_regions:
                cn = r["centroid_norm"]
                yc, xc = cn["y"], cn["x"]
                matches = False
                if c == "north": matches = (yc <= 0.55)
                elif c == "south": matches = (yc >= 0.45)
                elif c == "east": matches = (xc >= 0.45)
                elif c == "west": matches = (xc <= 0.55)
                elif c == "northwest": matches = (yc <= 0.55 and xc <= 0.55)
                elif c == "northeast": matches = (yc <= 0.55 and xc >= 0.45)
                elif c == "southwest": matches = (yc >= 0.45 and xc <= 0.55)
                elif c == "southeast": matches = (yc >= 0.45 and xc >= 0.45)
                elif c == "center": matches = (0.2 <= yc <= 0.8 and 0.2 <= xc <= 0.8)
                elif c == "boundary": matches = (yc < 0.25 or yc > 0.75 or xc < 0.25 or xc > 0.75)
                else: matches = True

                if matches:
                    filtered_by_space.append(r)

        # 3. Apply Non-Maximum Suppression (NMS)
        nms_regions = cls.apply_nms(filtered_by_space, iou_threshold=0.38)

        # 4. Apply Ranking or Count Filtering
        if intent and intent.ranking == "largest":
            nms_regions = sorted(nms_regions, key=lambda r: r["pixel_area"], reverse=True)[:1]
        elif intent and intent.ranking == "smallest":
            nms_regions = sorted(nms_regions, key=lambda r: r["pixel_area"])[:1]
        elif intent and intent.count == "single":
            nms_regions = sorted(nms_regions, key=lambda r: r["score"], reverse=True)[:1]
        elif intent and intent.count == "all":
            # Keep up to 10 distinct prominent regions
            nms_regions = sorted(nms_regions, key=lambda r: r["pixel_area"], reverse=True)[:10]
        else:
            # Default: Keep up to 4 prominent regions
            nms_regions = sorted(nms_regions, key=lambda r: r["score"], reverse=True)[:4]

        # 5. Assign Stable Region IDs (R01, R02, etc.)
        final_regions: List[Dict[str, Any]] = []
        for i, reg in enumerate(nms_regions):
            reg_id = f"R0{i+1}" if i < 9 else f"R{i+1}"
            reg["id"] = reg_id
            final_regions.append(reg)

        return final_regions
