"""
SatQuery AI — Sample Dataset Generator
Creates realistic synthetic geospatial GeoTIFF and benchmark files
for testing each of the mandatory evaluation scenarios.
"""

import os
import numpy as np
from PIL import Image, TiffImagePlugin

SAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))

def create_geotiff_tags(origin_lon: float, origin_lat: float, pixel_scale_deg: float = 0.0001):
    """Generates standard OGC GeoTIFF metadata tags (Tiepoint, PixelScale, GeoKey WGS84)."""
    tag = TiffImagePlugin.ImageFileDirectory_v2()
    # ModelPixelScaleTag: (ScaleX, ScaleY, ScaleZ) in degrees
    tag[33550] = (pixel_scale_deg, pixel_scale_deg, 0.0)
    # ModelTiepointTag: (I, J, K, X, Y, Z) - origin top-left corner
    tag[33922] = (0.0, 0.0, 0.0, float(origin_lon), float(origin_lat), 0.0)
    # GeoKeyDirectoryTag: EPSG:4326 (WGS 84 geographic coordinate reference system)
    tag[34735] = (1, 1, 0, 7, 1024, 0, 1, 1, 1025, 0, 1, 1, 1026, 34737, 1, 0, 2048, 0, 1, 4326, 2049, 34737, 7, 1, 2054, 0, 1, 9102, 3072, 0, 1, 4326)
    return tag

def create_samples():
    os.makedirs(SAMPLE_DIR, exist_ok=True)
    H, W = 256, 256

    # 1. Optical Sample (4-band: R, G, B, NIR)
    # Location: Yamuna River Basin, New Delhi (Lat: 28.6139, Lon: 77.2090)
    delhi_tags = create_geotiff_tags(origin_lon=77.1950, origin_lat=28.6300)

    r = np.zeros((H, W), dtype=np.uint8) + 80
    g = np.zeros((H, W), dtype=np.uint8) + 120
    b = np.zeros((H, W), dtype=np.uint8) + 60
    nir = np.zeros((H, W), dtype=np.uint8) + 160

    # River (NDWI high: green high, NIR low)
    river_x = (np.sin(np.linspace(0, 3.14 * 2, H)) * 20 + 190).astype(int)
    for y in range(H):
        x = river_x[y]
        r[y, max(0, x-15):min(W, x+15)] = 20
        g[y, max(0, x-15):min(W, x+15)] = 70
        b[y, max(0, x-15):min(W, x+15)] = 140
        nir[y, max(0, x-15):min(W, x+15)] = 10  # Absorbed in NIR

    # Urban Grid (top-left)
    for i in range(20, 100, 15):
        r[i:i+3, 20:100] = 190
        g[i:i+3, 20:100] = 190
        b[i:i+3, 20:100] = 190
        r[20:100, i:i+3] = 190
        g[20:100, i:i+3] = 190
        b[20:100, i:i+3] = 190

    # Runway (horizontal corridor)
    r[120:130, 40:180] = 210
    g[120:130, 40:180] = 210
    b[120:130, 40:180] = 210
    nir[120:130, 40:180] = 180

    opt_rgb = Image.fromarray(np.stack([r, g, b], axis=-1))
    opt_rgb.save(os.path.join(SAMPLE_DIR, "sample_optical.tif"), tiffinfo=delhi_tags)
    opt_rgb.save(os.path.join(SAMPLE_DIR, "sample_optical.png"))  # Benchmark un-georeferenced PNG

    # 2. SAR Sample (1-band radar backscatter amplitude)
    sar = np.random.normal(60, 15, (H, W)).astype(np.uint8)
    for y in range(H):
        x = river_x[y]
        sar[y, max(0, x-15):min(W, x+15)] = np.random.randint(5, 18, min(W, x+15) - max(0, x-15))
    for i in range(20, 100, 15):
        sar[i:i+5, 20:100] = np.random.randint(220, 255, (5, 80))
        sar[20:100, i:i+5] = np.random.randint(220, 255, (80, 5))

    sar_img = Image.fromarray(sar)
    sar_img.save(os.path.join(SAMPLE_DIR, "sample_sar.tif"), tiffinfo=delhi_tags)
    sar_img.save(os.path.join(SAMPLE_DIR, "sample_sar.png"))

    # 3. Bi-Temporal Pair (Mumbai / Navi Mumbai Urban Corridor: Lat: 19.0760, Lon: 72.8777)
    mumbai_tags = create_geotiff_tags(origin_lon=72.8600, origin_lat=19.0900)
    t1 = opt_rgb.copy()
    t2_arr = np.array(opt_rgb).copy()
    t2_arr[150:230, 80:160, 0] = 195
    t2_arr[150:230, 80:160, 1] = 190
    t2_arr[150:230, 80:160, 2] = 185
    t2 = Image.fromarray(t2_arr)

    t1.save(os.path.join(SAMPLE_DIR, "sample_t1.tif"), tiffinfo=mumbai_tags)
    t2.save(os.path.join(SAMPLE_DIR, "sample_t2.tif"), tiffinfo=mumbai_tags)

    # 4. Optical + SAR Co-registered Pair (Chennai Coastal Stand: Lat: 13.0827, Lon: 80.2707)
    chennai_tags = create_geotiff_tags(origin_lon=80.2500, origin_lat=13.1000)
    opt_rgb.save(os.path.join(SAMPLE_DIR, "sample_opt_pair.tif"), tiffinfo=chennai_tags)
    sar_img.save(os.path.join(SAMPLE_DIR, "sample_sar_pair.tif"), tiffinfo=chennai_tags)

    print("[OK] Sample GeoTIFF files with authentic WGS84 metadata generated successfully.")

if __name__ == "__main__":
    create_samples()
