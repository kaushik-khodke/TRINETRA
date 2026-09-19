"""
TRINETRA / SatQuery AI — Bi-Temporal Change Predict CLI
Inference test comparing two satellite observations and rendering differential change map.
Supports BitemporalInteractionTransformer (BIT), SiameseUNetBaseline, and SiameseChangeDiffNet.
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

from model import (
    SiameseUNetBaseline,
    BitemporalInteractionTransformer,
    create_change_model,
    SiameseChangeDiffNet
)

CHANGE_LABELS = {
    0: "Unchanged (Stable Baseline)",
    1: "Expansion / New Development (Increased Built-up / Vegetation)",
    2: "Reduction / Receded (Loss / Demolition / Vegetation Clearance)"
}

def predict_change(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if not os.path.exists(args.image_t1) or not os.path.exists(args.image_t2):
        raise FileNotFoundError("One or both input temporal images not found.")
    if not os.path.exists(args.checkpoint):
        raise FileNotFoundError(f"Checkpoint not found: {args.checkpoint}")

    print("============================================================")
    print("TRINETRA — Bi-Temporal Change Prediction")
    print(f"Observation T1: {args.image_t1}")
    print(f"Observation T2: {args.image_t2}")
    print(f"Checkpoint:     {args.checkpoint}")
    print(f"Hardware:       {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
    print("============================================================\n")

    weights = torch.load(args.checkpoint, map_location=device)
    keys = list(weights.keys())

    # Architecture auto-detection
    arch = args.model.lower() if args.model else "auto"
    if arch == "auto":
        cfg_path = os.path.join(os.path.dirname(args.checkpoint), "config.json")
        if os.path.exists(cfg_path):
            try:
                import json
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    arch = cfg.get("model_architecture", "auto")
            except Exception:
                pass

    if arch in ["bit", "transformer"] or any("tokenizer" in k or "t1_layers" in k for k in keys):
        model = BitemporalInteractionTransformer().to(device)
        is_dense = True
        arch_name = "BitemporalInteractionTransformer (BIT)"
    elif arch in ["baseline", "siamese_unet"] or any("enc1.conv" in k for k in keys):
        model = SiameseUNetBaseline().to(device)
        is_dense = True
        arch_name = "SiameseUNetBaseline"
    else:
        model = SiameseChangeDiffNet().to(device)
        is_dense = False
        arch_name = "SiameseChangeDiffNet (Legacy 1D)"

    model.load_state_dict(weights)
    model.eval()
    print(f"[MODEL] Loaded architecture: {arch_name}")

    img_size = args.image_size
    def load_img(path):
        img = Image.open(path).convert("RGB").resize((img_size, img_size), Image.BILINEAR)
        arr = np.array(img, dtype=np.float32) / 255.0
        return np.transpose(arr, (2, 0, 1))

    t1_tensor = torch.from_numpy(load_img(args.image_t1)).unsqueeze(0).to(device)
    t2_tensor = torch.from_numpy(load_img(args.image_t2)).unsqueeze(0).to(device)

    out_file = args.output_image or "change_prediction.png"

    if is_dense:
        with torch.no_grad():
            logits = model(t1_tensor, t2_tensor)
            prob_map = torch.sigmoid(logits).squeeze().cpu().numpy()
            binary_mask = (prob_map >= args.threshold).astype(np.uint8) * 255
            change_pct = float(np.mean(prob_map >= args.threshold) * 100)

        print(f"\nPREDICTED TEMPORAL CHANGE METRICS:")
        print(f"  Change Detected:        {'YES' if change_pct > 0.5 else 'NO'}")
        print(f"  Changed Area Ratio:     {change_pct:.2f}% of scene area")
        print(f"  Mean Change Confidence: {float(prob_map.mean())*100:.2f}%")
        print(f"  Peak Change Confidence: {float(prob_map.max())*100:.2f}%")

        # 4-panel visual composite: [T1 | T2 | Solar Amber Heatmap | Binary Change Mask]
        orig_t1 = Image.open(args.image_t1).convert("RGB").resize((img_size, img_size))
        orig_t2 = Image.open(args.image_t2).convert("RGB").resize((img_size, img_size))

        heat_r = (prob_map * 255).astype(np.uint8)
        heat_g = (prob_map * 160).astype(np.uint8)
        heat_b = np.zeros_like(heat_r)
        heatmap_img = Image.fromarray(np.stack([heat_r, heat_g, heat_b], axis=-1))

        mask_r = binary_mask
        mask_g = np.zeros_like(binary_mask)
        mask_b = np.zeros_like(binary_mask)
        mask_img = Image.fromarray(np.stack([mask_r, mask_g, mask_b], axis=-1))

        composite = Image.new("RGB", (img_size * 4, img_size))
        composite.paste(orig_t1, (0, 0))
        composite.paste(orig_t2, (img_size, 0))
        composite.paste(heatmap_img, (img_size * 2, 0))
        composite.paste(mask_img, (img_size * 3, 0))
        composite.save(out_file)
        print(f"\n[SAVED] Bi-temporal composite [T1 | T2 | Amber Heatmap | Binary Mask] -> {out_file}")
    else:
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

        img1 = Image.open(args.image_t1).convert("RGB").resize((img_size, img_size))
        img2 = Image.open(args.image_t2).convert("RGB").resize((img_size, img_size))
        composite = Image.new("RGB", (img_size * 2, img_size))
        composite.paste(img1, (0, 0))
        composite.paste(img2, (img_size, 0))
        composite.save(out_file)
        print(f"[SAVED] Bi-temporal visual composite written to: {out_file}")

    print("============================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict temporal shift between two satellite dates.")
    parser.add_argument("--image_t1", type=str, required=True, help="Path to pre-change image.")
    parser.add_argument("--image_t2", type=str, required=True, help="Path to post-change image.")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to trained model.")
    parser.add_argument("--model", type=str, default="auto", choices=["auto", "bit", "baseline", "legacy"], help="Architecture")
    parser.add_argument("--image_size", type=int, default=224, help="Input resolution")
    parser.add_argument("--threshold", type=float, default=0.5, help="Binary change probability threshold")
    parser.add_argument("--output_image", type=str, default=None)
    args = parser.parse_args()

    predict_change(args)
