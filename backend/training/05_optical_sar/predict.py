"""
TRINETRA / SatQuery AI — Optical + SAR Predict CLI
Inference test on co-registered optical RGB and SAR radar backscatter imagery.
"""

import os
import sys
import argparse
from PIL import Image
import numpy as np
import torch

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from model import OpticalSARCrossAttentionNet

LAND_USE_CLASSES = [
    "Dense Urban Fabric", "Industrial Infrastructure", "Agricultural Crop Stand",
    "Broadleaf Forest Canopy", "Coniferous Woodland", "Natural Grassland / Shrub",
    "Inland Water Body", "Coastal / Marine", "Barren Soil / Rock", "Wetland / Marsh"
]

def predict_optical_sar(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if not os.path.exists(args.optical) or not os.path.exists(args.sar):
        raise FileNotFoundError("One or both input raster files not found.")

    print("============================================================")
    print("TRINETRA — Optical + SAR Cross-Modal Prediction")
    print(f"Optical:    {args.optical}")
    print(f"SAR Radar:  {args.sar}")
    print(f"Checkpoint: {args.checkpoint}")
    print("============================================================\n")

    # Load Optical
    opt_img = Image.open(args.optical).convert("RGB").resize((224, 224), Image.BILINEAR)
    opt_arr = np.transpose(np.array(opt_img, dtype=np.float32) / 255.0, (2, 0, 1))
    opt_tensor = torch.from_numpy(opt_arr).unsqueeze(0).to(device)

    # Load SAR
    sar_img = Image.open(args.sar).resize((224, 224), Image.BILINEAR)
    sar_arr = np.array(sar_img, dtype=np.float32)
    if sar_arr.ndim == 2:
        sar_arr = np.stack([sar_arr, sar_arr], axis=0) / 255.0
    elif sar_arr.ndim == 3:
        sar_arr = np.transpose(sar_arr, (2, 0, 1))[:2] / 255.0
    sar_tensor = torch.from_numpy(sar_arr).unsqueeze(0).to(device)

    model = OpticalSARCrossAttentionNet().to(device)
    weights = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(weights)
    model.eval()

    with torch.no_grad():
        logits = model(opt_tensor, sar_tensor)
        probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()

    top_idx = int(np.argmax(probs))
    conf = probs[top_idx] * 100.0

    print("PREDICTED CROSS-MODAL TERRAIN CLASSIFICATION:")
    print(f"  Primary Category: {LAND_USE_CLASSES[top_idx] if top_idx < len(LAND_USE_CLASSES) else f'Class {top_idx}'}")
    print(f"  Confidence:       {conf:.2f}%")
    print("\nTop 3 Probabilities:")
    top3 = np.argsort(-probs)[:3]
    for rank, idx in enumerate(top3, 1):
        cls_name = LAND_USE_CLASSES[idx] if idx < len(LAND_USE_CLASSES) else f"Class {idx}"
        print(f"  #{rank}: {cls_name:<30} ({probs[idx]*100:.1f}%)")
    print("============================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict land cover from co-registered Optical + SAR images.")
    parser.add_argument("--optical", type=str, required=True, help="Path to Optical image.")
    parser.add_argument("--sar", type=str, required=True, help="Path to SAR radar image.")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to trained model.")
    args = parser.parse_args()

    predict_optical_sar(args)
