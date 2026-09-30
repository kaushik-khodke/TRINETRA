"""
TRINETRA / Shanetra Geospatial Exploration Engine
Explore Test Fixture Generator
Generates small deterministic GeoTIFF fixtures with valid CRS, affine transforms, and realistic multispectral/SAR profiles.
"""

import os
import numpy as np
import rasterio
from rasterio.transform import from_bounds

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_fixtures():
    os.makedirs(FIXTURE_DIR, exist_ok=True)
    H, W = 256, 256

    # 1. Optical Sentinel-2 Nagpur Sample (4-band: Red, Green, Blue, NIR)
    # Bounds: [79.0, 21.0, 79.2, 21.2]
    opt_path = os.path.join(FIXTURE_DIR, "sentinel2_nagpur_truecolor.tif")
    opt_transform = from_bounds(79.0, 21.0, 79.2, 21.2, W, H)

    # Synthetic realistic landcover
    red = np.full((H, W), 70, dtype=np.uint8)
    green = np.full((H, W), 110, dtype=np.uint8)
    blue = np.full((H, W), 65, dtype=np.uint8)
    nir = np.full((H, W), 160, dtype=np.uint8)

    # Water reservoir
    y, x = np.ogrid[:H, :W]
    water_mask = ((x - 128) ** 2 + (y - 128) ** 2) < 45 ** 2
    red[water_mask] = 18
    green[water_mask] = 45
    blue[water_mask] = 115
    nir[water_mask] = 12

    # Urban grid
    red[40:80, 40:80] = 175
    green[40:80, 40:80] = 170
    blue[40:80, 40:80] = 165
    nir[40:80, 40:80] = 140

    with rasterio.open(
        opt_path,
        "w",
        driver="GTiff",
        height=H,
        width=W,
        count=4,
        dtype=rasterio.uint8,
        crs="EPSG:4326",
        transform=opt_transform,
    ) as dst:
        dst.write(red, 1)
        dst.write(green, 2)
        dst.write(blue, 3)
        dst.write(nir, 4)
        dst.set_band_description(1, "B04-Red")
        dst.set_band_description(2, "B03-Green")
        dst.set_band_description(3, "B02-Blue")
        dst.set_band_description(4, "B08-NIR")

    print(f"Generated: {opt_path}")

    # 2. SAR Mumbai Sample (1-band: Intensity / Backscatter dB)
    # Bounds: [72.8, 18.9, 73.0, 19.1]
    sar_path = os.path.join(FIXTURE_DIR, "sentinel1_mumbai_sar.tif")
    sar_transform = from_bounds(72.8, 18.9, 73.0, 19.1, W, H)

    # Ocean / Land boundary
    sar_arr = np.full((H, W), 80, dtype=np.uint8)
    # Ocean on left (low backscatter / dark)
    sar_arr[:, :100] = 25
    # High double-bounce urban scatter
    sar_arr[80:160, 120:200] = 210

    with rasterio.open(
        sar_path,
        "w",
        driver="GTiff",
        height=H,
        width=W,
        count=1,
        dtype=rasterio.uint8,
        crs="EPSG:4326",
        transform=sar_transform,
    ) as dst:
        dst.write(sar_arr, 1)
        dst.set_band_description(1, "VV-Intensity")

    print(f"Generated: {sar_path}")


if __name__ == "__main__":
    generate_fixtures()
