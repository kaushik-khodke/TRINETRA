"""
SatQuery AI — Geospatial Normalizer & Remote Sensing Indices
Calculates NDVI, NDWI, VARI (for RGB), SAR radar backscatter dB scaling,
and differential change matrices.
"""

import numpy as np
from typing import Dict, Any, Tuple

class GeospatialNormalizer:
    
    @staticmethod
    def compute_ndvi(raster: np.ndarray) -> np.ndarray:
        """
        Computes vegetation index:
        - If 4+ bands: standard NDVI (NIR - Red) / (NIR + Red)
        - If 3 bands (RGB): Visible Atmospherically Resistant Index (VARI) = (Green - Red) / (Green + Red - Blue)
        """
        arr = raster.astype(np.float32)

        # 4+ bands (Multispectral with NIR at index 3 or 1)
        if arr.ndim == 3 and arr.shape[2] >= 4:
            red = arr[:, :, 0]
            nir = arr[:, :, 3]
            denom = nir + red
            denom[denom == 0] = 1e-6
            ndvi = (nir - red) / denom
            return np.clip(ndvi, -1.0, 1.0)

        # 3 bands (Standard True-Color RGB: Red=0, Green=1, Blue=2)
        if arr.ndim == 3 and arr.shape[2] == 3:
            red = arr[:, :, 0]
            green = arr[:, :, 1]
            blue = arr[:, :, 2]
            # VARI calculation
            denom = green + red - blue
            denom[np.abs(denom) < 1e-4] = 1e-4
            vari = (green - red) / denom
            return np.clip(vari, -1.0, 1.0)

        # Single band (SAR / Grayscale)
        band = arr if arr.ndim == 2 else arr[:, :, 0]
        norm = (band - np.min(band)) / (np.ptp(band) + 1e-6)
        return (norm * 0.6) - 0.2

    @staticmethod
    def compute_ndwi(raster: np.ndarray) -> np.ndarray:
        """
        Computes water index:
        - If 4+ bands: standard NDWI (Green - NIR) / (Green + NIR)
        - If 3 bands (RGB): Water Absorption Index = (Blue - Red) / (Blue + Red) weighted by darkness
        """
        arr = raster.astype(np.float32)

        if arr.ndim == 3 and arr.shape[2] >= 4:
            green = arr[:, :, 1]
            nir = arr[:, :, 3]
            denom = green + nir
            denom[denom == 0] = 1e-6
            ndwi = (green - nir) / denom
            return np.clip(ndwi, -1.0, 1.0)

        if arr.ndim == 3 and arr.shape[2] == 3:
            red = arr[:, :, 0]
            green = arr[:, :, 1]
            blue = arr[:, :, 2]
            # In clear/turbid water, Blue and Green reflect more than Red
            denom = blue + red
            denom[denom == 0] = 1e-6
            water_ratio = (blue - red) / denom
            # Water also has low overall brightness (absorption)
            brightness = (red + green + blue) / (3.0 * 255.0)
            ndwi_rgb = water_ratio * (1.0 - brightness)
            return np.clip(ndwi_rgb, -1.0, 1.0)

        band = arr if arr.ndim == 2 else arr[:, :, 0]
        norm = (band - np.min(band)) / (np.ptp(band) + 1e-6)
        return ((1.0 - norm) * 0.8) - 0.3

    @staticmethod
    def compute_sar_db(sar_raster: np.ndarray) -> np.ndarray:
        """Converts SAR digital numbers / amplitude into decibels (dB)."""
        data = sar_raster.astype(np.float32)
        if data.ndim == 3:
            data = data[:, :, 0]
        data_pos = np.maximum(data, 1e-5)
        db = 10.0 * np.log10(data_pos)
        return db

    @staticmethod
    def compute_spectral_breakdown(raster: np.ndarray) -> Dict[str, Any]:
        """
        Computes accurate land-cover percentages and spectral indices
        from the actual image pixels. Subsamples ultra-high-resolution rasters
        (e.g., 60MP Landsat/Sentinel) to maintain sub-second latency.
        """
        h, w = raster.shape[:2]
        max_dim = max(h, w)
        if max_dim > 1024:
            step = int(np.ceil(max_dim / 1024))
            sample = raster[::step, ::step]
        else:
            sample = raster

        arr = sample.astype(np.float32)
        ndvi = GeospatialNormalizer.compute_ndvi(sample)
        ndwi = GeospatialNormalizer.compute_ndwi(sample)

        # Structural high-frequency edges (built-up detection)
        if arr.ndim == 3:
            gray = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
        else:
            gray = arr if arr.ndim == 2 else arr[:, :, 0]

        grad_y, grad_x = np.gradient(gray)
        edge_mag = np.sqrt(grad_x**2 + grad_y**2)
        is_urban = edge_mag > 22.0

        # Feature masks
        is_water = ndwi > 0.12
        is_veg = (ndvi > 0.15) & (~is_water)

        total_pixels = float(gray.size)
        veg_pct = round(float(np.sum(is_veg)) / total_pixels * 100.0, 1)
        water_pct = round(float(np.sum(is_water)) / total_pixels * 100.0, 1)
        urban_pct = round(float(np.sum(is_urban & (~is_veg) & (~is_water))) / total_pixels * 100.0, 1)
        bare_pct = max(0.0, round(100.0 - (veg_pct + water_pct + urban_pct), 1))

        # Spatial quadrant breakdown
        mid_y, mid_x = gray.shape[0] // 2, gray.shape[1] // 2
        water_quads = {
            "Northwest": round(float(np.mean(is_water[:mid_y, :mid_x])) * 100.0, 1),
            "Northeast": round(float(np.mean(is_water[:mid_y, mid_x:])) * 100.0, 1),
            "Southwest": round(float(np.mean(is_water[mid_y:, :mid_x])) * 100.0, 1),
            "Southeast": round(float(np.mean(is_water[mid_y:, mid_x:])) * 100.0, 1),
        }
        veg_quads = {
            "Northwest": round(float(np.mean(is_veg[:mid_y, :mid_x])) * 100.0, 1),
            "Northeast": round(float(np.mean(is_veg[:mid_y, mid_x:])) * 100.0, 1),
            "Southwest": round(float(np.mean(is_veg[mid_y:, :mid_x])) * 100.0, 1),
            "Southeast": round(float(np.mean(is_veg[mid_y:, mid_x:])) * 100.0, 1),
        }
        urban_quads = {
            "Northwest": round(float(np.mean(is_urban[:mid_y, :mid_x])) * 100.0, 1),
            "Northeast": round(float(np.mean(is_urban[:mid_y, mid_x:])) * 100.0, 1),
            "Southwest": round(float(np.mean(is_urban[mid_y:, :mid_x])) * 100.0, 1),
            "Southeast": round(float(np.mean(is_urban[mid_y:, mid_x:])) * 100.0, 1),
        }

        top_water_sectors = [f"{k} ({v}%)" for k, v in sorted(water_quads.items(), key=lambda x: x[1], reverse=True) if v > 1.0]
        top_veg_sectors = [f"{k} ({v}%)" for k, v in sorted(veg_quads.items(), key=lambda x: x[1], reverse=True) if v > 5.0]
        top_urban_sectors = [f"{k} ({v}%)" for k, v in sorted(urban_quads.items(), key=lambda x: x[1], reverse=True) if v > 2.0]

        spatial_desc = (
            f"Water concentrated in: {', '.join(top_water_sectors) if top_water_sectors else 'None'}; "
            f"Vegetation concentrated in: {', '.join(top_veg_sectors) if top_veg_sectors else 'Sparse'}; "
            f"Built-up in: {', '.join(top_urban_sectors) if top_urban_sectors else 'Low'}"
        )

        return {
            "vegetation_cover_pct": veg_pct,
            "water_body_pct": water_pct,
            "built_up_density_pct": urban_pct,
            "bare_soil_pct": bare_pct,
            "mean_ndvi": round(float(np.mean(ndvi)), 3),
            "mean_ndwi": round(float(np.mean(ndwi)), 3),
            "spatial_distribution": spatial_desc,
            "quadrants": {
                "water": water_quads,
                "vegetation": veg_quads,
                "urban": urban_quads
            },
            "ndvi_map": ndvi,
            "ndwi_map": ndwi
        }

    @staticmethod
    def compute_bitemporal_change(arr_t1: np.ndarray, arr_t2: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Computes absolute differential magnitude and directional shifts between T1 and T2 observations.
        """
        h = min(arr_t1.shape[0], arr_t2.shape[0])
        w = min(arr_t1.shape[1], arr_t2.shape[1])

        max_dim = max(h, w)
        if max_dim > 1024:
            step = int(np.ceil(max_dim / 1024))
            arr_t1 = arr_t1[:h:step, :w:step]
            arr_t2 = arr_t2[:h:step, :w:step]
            h, w = arr_t1.shape[:2]

        t1 = arr_t1[:h, :w].astype(np.float32)
        t2 = arr_t2[:h, :w].astype(np.float32)

        if t1.ndim == 3:
            t1 = np.mean(t1[:, :, :3], axis=-1)
        if t2.ndim == 3:
            t2 = np.mean(t2[:, :, :3], axis=-1)

        t1_norm = (t1 - np.min(t1)) / (np.ptp(t1) + 1e-6)
        t2_norm = (t2 - np.min(t2)) / (np.ptp(t2) + 1e-6)

        diff = np.abs(t2_norm - t1_norm)
        mean_diff = float(np.mean(diff))
        max_diff = float(np.max(diff))
        changed_pixels_ratio = float(np.mean(diff > 0.22))

        # Spatial Quadrant Breakdown
        mid_y, mid_x = h // 2, w // 2
        q_nw = float(np.mean(diff[:mid_y, :mid_x] > 0.22))
        q_ne = float(np.mean(diff[:mid_y, mid_x:] > 0.22))
        q_sw = float(np.mean(diff[mid_y:, :mid_x] > 0.22))
        q_se = float(np.mean(diff[mid_y:, mid_x:] > 0.22))
        center = float(np.mean(diff[h//4:3*h//4, w//4:3*w//4] > 0.22))

        quadrants = {
            "Northwest": round(q_nw * 100.0, 1),
            "Northeast": round(q_ne * 100.0, 1),
            "Southwest": round(q_sw * 100.0, 1),
            "Southeast": round(q_se * 100.0, 1),
            "Central Corridor": round(center * 100.0, 1)
        }

        # Shift direction: brightened (construction/clearing) vs darkened
        shift = t2_norm - t1_norm
        brightened = float(np.mean(shift > 0.20))
        darkened = float(np.mean(shift < -0.20))
        trend = "expansion" if brightened >= darkened else "vegetation_or_moisture"

        sorted_sectors = sorted(quadrants.items(), key=lambda x: x[1], reverse=True)
        top_sectors = [f"{k} sector ({v}% altered)" for k, v in sorted_sectors if v > 1.0][:2]

        stats = {
            "mean_difference": round(mean_diff, 4),
            "max_difference": round(max_diff, 4),
            "changed_area_percentage": round(changed_pixels_ratio * 100.0, 2),
            "significant_change_detected": changed_pixels_ratio > 0.04,
            "quadrants": quadrants,
            "top_sectors": top_sectors,
            "trend": trend
        }
        return diff, stats
