"""
SatQuery AI — Sample Dataset Generator
Creates realistic synthetic geospatial GeoTIFF and benchmark files
for testing each of the mandatory evaluation scenarios.
"""

import os
import numpy as np
from PIL import Image

SAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))

def create_samples():
    os.makedirs(SAMPLE_DIR, exist_ok=True)
    H, W = 256, 256

    # 1. Optical Sample (4-band: R, G, B, NIR)
    # Features: River on the right, urban grid top-left, vegetation bottom-left, runway center
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
    opt_rgb.save(os.path.join(SAMPLE_DIR, "sample_optical.tif"))
    opt_rgb.save(os.path.join(SAMPLE_DIR, "sample_optical.png"))

    # 2. SAR Sample (1-band radar backscatter amplitude)
    # Urban = bright double-bounce, Water = dark specular, Runway = moderate/smooth
    sar = np.random.normal(60, 15, (H, W)).astype(np.uint8)
    # Water river is specular / very dark
    for y in range(H):
        x = river_x[y]
        sar[y, max(0, x-15):min(W, x+15)] = np.random.randint(5, 18, min(W, x+15) - max(0, x-15))
    # Urban corner reflectors / double-bounce (bright)
    for i in range(20, 100, 15):
        sar[i:i+5, 20:100] = np.random.randint(220, 255, (5, 80))
        sar[20:100, i:i+5] = np.random.randint(220, 255, (80, 5))

    sar_img = Image.fromarray(sar)
    sar_img.save(os.path.join(SAMPLE_DIR, "sample_sar.tif"))
    sar_img.save(os.path.join(SAMPLE_DIR, "sample_sar.png"))

    # 3. Bi-Temporal Pair (T1 baseline vs T2 with new urban sprawl & building expansion)
    t1 = opt_rgb.copy()
    t2_arr = np.array(opt_rgb).copy()
    # New urban expansion in bottom-right quadrant
    t2_arr[150:230, 80:160, 0] = 195
    t2_arr[150:230, 80:160, 1] = 190
    t2_arr[150:230, 80:160, 2] = 185
    t2 = Image.fromarray(t2_arr)

    t1.save(os.path.join(SAMPLE_DIR, "sample_t1.tif"))
    t2.save(os.path.join(SAMPLE_DIR, "sample_t2.tif"))

    # 4. Optical + SAR Co-registered Pair
    opt_rgb.save(os.path.join(SAMPLE_DIR, "sample_opt_pair.tif"))
    sar_img.save(os.path.join(SAMPLE_DIR, "sample_sar_pair.tif"))

    print("[OK] Sample geospatial test files generated successfully in sample_data/.")

if __name__ == "__main__":
    create_samples()
