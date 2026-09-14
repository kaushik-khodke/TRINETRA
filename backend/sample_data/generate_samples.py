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

    # 5. Hyperspectral 200-Band Cube (.mat)
    create_hsi_sample()

    # 6. Non-Remote-Sensing Domain Rejection Benchmark Samples
    create_rejection_samples()

    print("[OK] All sample datasets (Optical, SAR, Change, Fusion, HSI, Rejections) generated successfully.")

def create_hsi_sample():
    """Generates authentic 200-band calibrated HSI cube (.mat) with realistic vegetation and water spectral signatures."""
    import scipy.io as sio
    H, W, B = 64, 64, 200
    wavelengths = np.linspace(400.0, 2400.0, B, dtype=np.float32)

    # Vegetation spectral signature: chlorophyll dip at 670nm, red edge at 700-800nm, water dips at 960/1400/1900nm
    veg_curve = np.zeros(B, dtype=np.float32)
    for i, wl in enumerate(wavelengths):
        if wl < 500:
            v = 0.05 + 0.02 * np.sin((wl - 400) / 100 * np.pi)
        elif wl < 640:
            v = 0.08 + 0.04 * np.sin((wl - 500) / 140 * np.pi)
        elif wl < 700:
            # Strong Chlorophyll Red Absorption Dip centered at 670nm
            v = 0.03 + 0.06 * ((wl - 670) / 30) ** 2
        elif wl < 850:
            # Steep vegetation red edge rise
            v = 0.09 + 0.41 * (wl - 700) / 150
        else:
            v = 0.50
            if abs(wl - 960) < 60:
                v -= 0.15 * (1.0 - abs(wl - 960) / 60)
            if abs(wl - 1400) < 80:
                v -= 0.30 * (1.0 - abs(wl - 1400) / 80)
            if abs(wl - 1900) < 80:
                v -= 0.25 * (1.0 - abs(wl - 1900) / 80)
        veg_curve[i] = max(0.01, float(v))

    cube = np.zeros((H, W, B), dtype=np.float32)
    for y in range(H):
        for x in range(W):
            noise = np.random.normal(0, 0.015, B).astype(np.float32)
            cube[y, x, :] = np.clip(veg_curve + noise, 0.0, 1.0)

    # Add a water body patch
    for y in range(40, 60):
        for x in range(40, 60):
            water_curve = np.clip(0.15 * np.exp(-(wavelengths - 450) / 300), 0.01, 0.3)
            cube[y, x, :] = water_curve + np.random.normal(0, 0.005, B).astype(np.float32)

    # Add small high-contrast anomaly target
    cube[10:14, 10:14, :] = 0.85

    mat_data = {
        "indian_pines_corrected": cube,
        "wavelengths": wavelengths
    }
    sio.savemat(os.path.join(SAMPLE_DIR, "sample_hsi.mat"), mat_data)

def create_rejection_samples():
    """Generates non-satellite domain rejection benchmark images."""
    # 1. Document / printed paper scan (white page with black text lines)
    doc = np.full((300, 300, 3), 240, dtype=np.uint8)
    for row in range(40, 260, 20):
        doc[row:row+3, 40:260] = 30
    Image.fromarray(doc).save(os.path.join(SAMPLE_DIR, "sample_document_reject.png"))

    # 2. Horizon / ground-level photograph with sky
    horizon = np.zeros((256, 256, 3), dtype=np.uint8)
    horizon[:90, :, 0] = 130
    horizon[:90, :, 1] = 175
    horizon[:90, :, 2] = 245
    horizon[90:, :, 0] = 100
    horizon[90:, :, 1] = 80
    horizon[90:, :, 2] = 60
    Image.fromarray(horizon).save(os.path.join(SAMPLE_DIR, "sample_horizon_reject.png"))

    # 3. Portrait / selfie with human skin tone
    portrait = np.full((256, 256, 3), 50, dtype=np.uint8)
    portrait[60:190, 70:185, 0] = 210
    portrait[60:190, 70:185, 1] = 150
    portrait[60:190, 70:185, 2] = 115
    Image.fromarray(portrait).save(os.path.join(SAMPLE_DIR, "sample_portrait_reject.png"))

if __name__ == "__main__":
    create_samples()
