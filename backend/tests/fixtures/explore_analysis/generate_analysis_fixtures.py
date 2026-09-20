"""
TRINETRA Analysis Engine — Test Fixtures Generator
Generates small, compact GeoTIFF fixtures for unit and integration testing.
"""

import os
import json
import numpy as np
import rasterio
from rasterio.transform import from_bounds

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_analysis_fixtures():
    os.makedirs(FIXTURE_DIR, exist_ok=True)
    H, W = 128, 128
    bounds = [79.0, 21.0, 79.1, 21.1]
    transform = from_bounds(*bounds, W, H)

    # 1. Optical A (Baseline T1)
    opt_a_path = os.path.join(FIXTURE_DIR, "optical_a.tif")
    r_a = np.full((H, W), 70, dtype=np.uint8)
    g_a = np.full((H, W), 110, dtype=np.uint8)
    b_a = np.full((H, W), 65, dtype=np.uint8)

    # Water pond in center
    y, x = np.ogrid[:H, :W]
    water_mask = ((x - 64) ** 2 + (y - 64) ** 2) < 20 ** 2
    r_a[water_mask] = 20
    g_a[water_mask] = 50
    b_a[water_mask] = 120

    with rasterio.open(
        opt_a_path, "w", driver="GTiff", height=H, width=W, count=3,
        dtype=rasterio.uint8, crs="EPSG:4326", transform=transform
    ) as dst:
        dst.write(r_a, 1)
        dst.write(g_a, 2)
        dst.write(b_a, 3)

    # 2. Optical B (Changed T2) - Built-up expansion in top quadrant
    opt_b_path = os.path.join(FIXTURE_DIR, "optical_b.tif")
    r_b = r_a.copy()
    g_b = g_a.copy()
    b_b = b_a.copy()

    # Expand urban surface in [15:45, 15:45]
    r_b[15:45, 15:45] = 180
    g_b[15:45, 15:45] = 175
    b_b[15:45, 15:45] = 170

    with rasterio.open(
        opt_b_path, "w", driver="GTiff", height=H, width=W, count=3,
        dtype=rasterio.uint8, crs="EPSG:4326", transform=transform
    ) as dst:
        dst.write(r_b, 1)
        dst.write(g_b, 2)
        dst.write(b_b, 3)

    # 3. SAR A (Sentinel-1 VV backscatter float32 in dB)
    sar_path = os.path.join(FIXTURE_DIR, "sar_a.tif")
    sar_db = np.full((H, W), -12.0, dtype=np.float32)
    # Low backscatter on water
    sar_db[water_mask] = -22.0
    # High backscatter on urban
    sar_db[15:45, 15:45] = -5.0

    with rasterio.open(
        sar_path, "w", driver="GTiff", height=H, width=W, count=1,
        dtype=rasterio.float32, crs="EPSG:4326", transform=transform
    ) as dst:
        dst.write(sar_db, 1)

    # 4. Nodata Scene
    nodata_path = os.path.join(FIXTURE_DIR, "nodata_scene.tif")
    nd_arr = np.full((H, W), 100, dtype=np.int16)
    nd_arr[:40, :] = -9999

    with rasterio.open(
        nodata_path, "w", driver="GTiff", height=H, width=W, count=1,
        dtype=rasterio.int16, crs="EPSG:4326", transform=transform, nodata=-9999
    ) as dst:
        dst.write(nd_arr, 1)

    # 5. Metadata manifest
    meta_path = os.path.join(FIXTURE_DIR, "metadata.json")
    metadata = {
        "fixtures": {
            "optical_a": {"file": "optical_a.tif", "crs": "EPSG:4326", "modality": "optical", "bounds": bounds},
            "optical_b": {"file": "optical_b.tif", "crs": "EPSG:4326", "modality": "optical", "bounds": bounds},
            "sar_a": {"file": "sar_a.tif", "crs": "EPSG:4326", "modality": "sar", "bounds": bounds},
            "nodata_scene": {"file": "nodata_scene.tif", "crs": "EPSG:4326", "nodata": -9999, "bounds": bounds},
        }
    }
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print("[OK] Generated Analysis Test Fixtures successfully.")


if __name__ == "__main__":
    generate_analysis_fixtures()
