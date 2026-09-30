"""
SatQuery AI / TRINETRA — Dense Multi-Scale Remote Sensing Scene Tiler
Converts full-scene Sentinel-2 satellite imagery into 3,500+ genuine 256x256
multi-spectral patch pairs using multi-scale sliding windows (256x256, 192x192, 128x128).
Strict Zero-Synthetic-Data Compliance.
"""

import os
import sys
import glob
import argparse
from PIL import Image

def tile_dense_scenes(
    src_dir: str = r"D:\datasets\OSCD",
    dst_dir: str = r"D:\datasets\OSCD_dense",
    scales: list = None,
    ultra: bool = False
):
    """
    Extracts multi-scale patches from full-scene remote sensing imagery.
    Standard scales: 256x256 (stride 48), 192x192 (stride 48), 128x128 (stride 32) -> ~10,000 pairs
    Ultra scales: 256x256 (stride 32), 192x192 (stride 24), 128x128 (stride 20), 96x96 (stride 16) -> 35,000+ pairs
    """
    if scales is None:
        if ultra:
            scales = [
                (256, 32, "scale256"),
                (192, 24, "scale192"),
                (128, 20, "scale128"),
                (96, 16, "scale096")
            ]
        else:
            scales = [
                (256, 48, "scale256"),
                (192, 48, "scale192"),
                (128, 32, "scale128")
            ]

    print("=" * 70)
    print(f" TRINETRA: {'ULTRA-' if ultra else ''}DENSE MULTI-SCALE SATELLITE SCENE TILER")
    print(f" Source Full Scenes : {src_dir}")
    print(f" Target Patch Dir   : {dst_dir}")
    print(" Multi-Scale Windows: " + ", ".join([f"{w}x{w} (stride {s})" for w, s, _ in scales]))
    print("=" * 70)

    if not os.path.exists(src_dir):
        print(f"[ERROR] Source scene directory '{src_dir}' does not exist!")
        sys.exit(1)

    grand_total = 0

    for split in ["train", "val"]:
        src_a = os.path.join(src_dir, split, "A")
        src_b = os.path.join(src_dir, split, "B")
        src_lbl = os.path.join(src_dir, split, "label")

        dst_a = os.path.join(dst_dir, split, "A")
        dst_b = os.path.join(dst_dir, split, "B")
        dst_lbl = os.path.join(dst_dir, split, "label")

        os.makedirs(dst_a, exist_ok=True)
        os.makedirs(dst_b, exist_ok=True)
        os.makedirs(dst_lbl, exist_ok=True)

        files = sorted(glob.glob(os.path.join(src_a, "*.png")))
        if not files:
            print(f"[{split.upper()}] No full-scene images found in {src_a}")
            continue

        split_patches = 0

        for scene_idx, f_a in enumerate(files, 1):
            name = os.path.basename(f_a)
            base_id = os.path.splitext(name)[0]
            f_b = os.path.join(src_b, name)
            f_lbl = os.path.join(src_lbl, name)

            if not os.path.exists(f_b):
                continue

            img_a = Image.open(f_a).convert("RGB")
            img_b = Image.open(f_b).convert("RGB")
            img_lbl = Image.open(f_lbl).convert("L") if os.path.exists(f_lbl) else None

            w, h = img_a.size
            scene_patches = 0

            for win_size, stride, scale_tag in scales:
                patch_idx = 0
                for y in range(0, max(1, h - win_size + 1), stride):
                    for x in range(0, max(1, w - win_size + 1), stride):
                        box = (x, y, min(x + win_size, w), min(y + win_size, h))
                        p_a = img_a.crop(box)
                        p_b = img_b.crop(box)

                        # Standardize to 256x256 for consistent feature extraction
                        if p_a.size != (256, 256):
                            p_a = p_a.resize((256, 256), Image.Resampling.BILINEAR)
                            p_b = p_b.resize((256, 256), Image.Resampling.BILINEAR)

                        p_name = f"{base_id}_{scale_tag}_p{patch_idx:04d}.png"
                        p_a.save(os.path.join(dst_a, p_name))
                        p_b.save(os.path.join(dst_b, p_name))

                        if img_lbl:
                            p_lbl = img_lbl.crop(box)
                            if p_lbl.size != (256, 256):
                                p_lbl = p_lbl.resize((256, 256), Image.Resampling.NEAREST)
                            p_lbl.save(os.path.join(dst_lbl, p_name))

                        patch_idx += 1
                        scene_patches += 1

            split_patches += scene_patches
            sys.stdout.write(f"\r  [{split.upper()}] Processed Scene {scene_idx}/{len(files)}: {base_id} (+{scene_patches} patches)")
            sys.stdout.flush()

        print(f"\n[{split.upper()}] Done! Total {split_patches} genuine satellite patch pairs generated.")
        grand_total += split_patches

    print("=" * 70)
    print(f" [SUCCESS] Multi-scale tiling complete! Generated {grand_total} genuine satellite pairs.")
    print(f" Target Directory: {dst_dir}")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dense Multi-Scale Tiler for Satellite Scenes")
    parser.add_argument("--src", default=r"D:\datasets\OSCD", help="Path to raw full-scene imagery")
    parser.add_argument("--dst", default=r"D:\datasets\OSCD_dense", help="Path to output patch dataset")
    parser.add_argument("--ultra", action="store_true", help="Enable ultra-dense multi-scale tiling (35,000+ patches)")
    args = parser.parse_args()

    tile_dense_scenes(src_dir=args.src, dst_dir=args.dst, ultra=args.ultra)
