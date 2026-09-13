"""
TRINETRA / SatQuery AI — BigEarthNet-S2 Predict CLI
Inference test on a real Sentinel-2 satellite raster patch.
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

from dataset import CORINE_19_CLASSES
from model import BigEarthNetAdaptedResNet

def predict_patch(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if not os.path.exists(args.image):
        raise FileNotFoundError(f"Image patch '{args.image}' not found.")

    print("============================================================")
    print("TRINETRA — BigEarthNet-S2 Single Patch Prediction")
    print(f"Image:      {args.image}")
    print(f"Checkpoint: {args.checkpoint}")
    print("============================================================\n")

    # Load image
    img = Image.open(args.image)
    img_resized = img.resize((120, 120), Image.BILINEAR)
    arr = np.array(img_resized, dtype=np.float32)

    if arr.ndim == 2:
        arr = np.expand_dims(arr, axis=0)
    elif arr.ndim == 3:
        arr = np.transpose(arr, (2, 0, 1))

    # Pad or slice to args.bands
    if arr.shape[0] < args.bands:
        pad = np.zeros((args.bands - arr.shape[0], 120, 120), dtype=np.float32)
        arr = np.concatenate([arr, pad], axis=0)
    arr = arr[:args.bands] / 10000.0

    tensor = torch.from_numpy(arr).unsqueeze(0).to(device)

    # Load model
    model = BigEarthNetAdaptedResNet(in_channels=args.bands, num_classes=19, pretrained=False).to(device)
    weights = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(weights)
    model.eval()

    with torch.no_grad():
        logits = model(tensor)
        probs = torch.sigmoid(logits)[0].cpu().numpy()

    print("DETECTED LAND-COVER CLASSES (Confidence >= 0.35):")
    detected = False
    for idx, prob in enumerate(probs):
        if prob >= args.threshold:
            detected = True
            print(f"  [+] {CORINE_19_CLASSES[idx]:<45} : {prob * 100:.1f}%")

    if not detected:
        top_idx = int(np.argmax(probs))
        print(f"  [-] Top category below threshold: {CORINE_19_CLASSES[top_idx]} ({probs[top_idx]*100:.1f}%)")
    print("============================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict land cover on a real Sentinel-2 patch.")
    parser.add_argument("--image", type=str, required=True, help="Path to real .tif or .png satellite patch.")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to trained model checkpoint.")
    parser.add_argument("--bands", type=int, default=4, help="Number of bands (4 for RGB-NIR, 12 for multispectral).")
    parser.add_argument("--threshold", type=float, default=0.35, help="Confidence threshold for multi-label display.")
    args = parser.parse_args()

    predict_patch(args)
