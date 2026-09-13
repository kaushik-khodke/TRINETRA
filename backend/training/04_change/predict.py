"""
TRINETRA / SatQuery AI — Bi-Temporal Change Predict CLI
Inference test comparing two satellite observations and rendering differential heatmap.
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

from model import SiameseChangeDiffNet

CHANGE_LABELS = {
    0: "Unchanged (Stable Baseline)",
    1: "Expansion / New Development (Increased Built-up / Vegetation)",
    2: "Reduction / Receded (Loss / Demolition / Vegetation Clearance)"
}

def predict_change(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if not os.path.exists(args.image_t1) or not os.path.exists(args.image_t2):
        raise FileNotFoundError("One or both input temporal images not found.")

    print("============================================================")
    print("TRINETRA — Bi-Temporal Change Prediction")
    print(f"Observation T1: {args.image_t1}")
    print(f"Observation T2: {args.image_t2}")
    print(f"Checkpoint:     {args.checkpoint}")
    print("============================================================\n")

    def load_img(path):
        img = Image.open(path).convert("RGB").resize((224, 224), Image.BILINEAR)
        arr = np.array(img, dtype=np.float32) / 255.0
        return np.transpose(arr, (2, 0, 1))

    t1_tensor = torch.from_numpy(load_img(args.image_t1)).unsqueeze(0).to(device)
    t2_tensor = torch.from_numpy(load_img(args.image_t2)).unsqueeze(0).to(device)

    model = SiameseChangeDiffNet().to(device)
    weights = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(weights)
    model.eval()

    with torch.no_grad():
        logits, diff = model(t1_tensor, t2_tensor)
        probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()
        pred_class = int(np.argmax(probs))
        diff_energy = float(torch.mean(diff).item())

    print(f"PREDICTED TEMPORAL STATUS:")
    print(f"  Classification:      {CHANGE_LABELS.get(pred_class, 'Unknown')}")
    print(f"  Confidence:          {probs[pred_class]*100:.2f}%")
    print(f"  Differential Energy: {diff_energy:.4f}")
    print(f"  Class Probabilities: Unchanged: {probs[0]*100:.1f}% | Expansion: {probs[1]*100:.1f}% | Reduction: {probs[2]*100:.1f}%")

    out_file = args.output_image or "change_comparison.png"
    img1 = Image.open(args.image_t1).convert("RGB").resize((224, 224))
    img2 = Image.open(args.image_t2).convert("RGB").resize((224, 224))
    composite = Image.new("RGB", (448, 224))
    composite.paste(img1, (0, 0))
    composite.paste(img2, (224, 0))
    composite.save(out_file)
    print(f"[SAVED] Bi-temporal visual composite written to: {out_file}")
    print("============================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict temporal shift between two satellite dates.")
    parser.add_argument("--image_t1", type=str, required=True, help="Path to pre-change image.")
    parser.add_argument("--image_t2", type=str, required=True, help="Path to post-change image.")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to trained model.")
    parser.add_argument("--output_image", type=str, default=None)
    args = parser.parse_args()

    predict_change(args)
