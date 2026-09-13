"""
TRINETRA / SatQuery AI — Text-Guided Grounding Predict CLI
Localizes remote-sensing features from natural language queries and renders bounding box overlay.
"""

import os
import sys
import argparse
from PIL import Image, ImageDraw
import numpy as np
import torch

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from model import RSGroundingDetector

def tokenize_query(text: str, max_len: int = 12) -> torch.Tensor:
    words = text.lower().replace(".", "").replace(",", "").split()
    ids = []
    for w in words[:max_len]:
        ids.append(abs(hash(w)) % 3900 + 100)
    while len(ids) < max_len:
        ids.append(0)
    return torch.tensor([ids], dtype=torch.long)

def predict_grounding(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if not os.path.exists(args.image):
        raise FileNotFoundError(f"Image '{args.image}' not found.")

    print("============================================================")
    print("TRINETRA — Region Grounding Prediction")
    print(f"Image:      {args.image}")
    print(f"Query:      \"{args.query}\"")
    print(f"Checkpoint: {args.checkpoint}")
    print("============================================================\n")

    # Load image
    orig_img = Image.open(args.image).convert("RGB")
    orig_w, orig_h = orig_img.size

    resized = orig_img.resize((256, 256), Image.BILINEAR)
    arr = np.array(resized, dtype=np.float32) / 255.0
    arr = np.transpose(arr, (2, 0, 1))
    img_tensor = torch.from_numpy(arr).unsqueeze(0).to(device)

    token_tensor = tokenize_query(args.query).to(device)

    model = RSGroundingDetector().to(device)
    weights = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(weights, strict=False)
    model.eval()

    with torch.no_grad():
        box = model(img_tensor, token_tensor)[0].cpu().numpy()

    # Normalized [ymin, xmin, ymax, xmax]
    ymin, xmin, ymax, xmax = float(box[0]), float(box[1]), float(box[2]), float(box[3])
    abs_box = [int(xmin * orig_w), int(ymin * orig_h), int(xmax * orig_w), int(ymax * orig_h)]

    print(f"LOCALIZED REGION:")
    print(f"  Normalized Box: [ymin={ymin:.3f}, xmin={xmin:.3f}, ymax={ymax:.3f}, xmax={xmax:.3f}]")
    print(f"  Pixel Coordinates ({orig_w}x{orig_h}): [X1={abs_box[0]}, Y1={abs_box[1]}, X2={abs_box[2]}, Y2={abs_box[3]}]")

    out_path = args.output_image or os.path.splitext(args.image)[0] + "_grounded.png"
    draw = ImageDraw.Draw(orig_img)
    draw.rectangle([abs_box[0], abs_box[1], abs_box[2], abs_box[3]], outline="#10B981", width=4)
    orig_img.save(out_path)
    print(f"[RENDERED] Bounding box visual overlay saved to: {out_path}")
    print("============================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Localize bounding box from text query on satellite image.")
    parser.add_argument("--image", type=str, required=True, help="Path to input satellite image.")
    parser.add_argument("--query", type=str, required=True, help="Referring text phrase.")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to trained model.")
    parser.add_argument("--output_image", type=str, default=None, help="Path to save annotated output.")
    args = parser.parse_args()

    predict_grounding(args)
