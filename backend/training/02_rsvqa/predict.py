"""
TRINETRA / SatQuery AI — RS-VQA Predict CLI
Inference test on a real satellite image with natural language question.
"""

import os
import sys
import json
import argparse
from PIL import Image
import numpy as np
import torch

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from models.tokenizer import tokenize_sequence
from model import RSVqaFusionNetwork, load_vqa_model

def tokenize_query(text: str, max_len: int = 16) -> torch.Tensor:
    ids = tokenize_sequence(text, max_length=max_len, vocab_size=5000, offset=100)
    return torch.tensor([ids], dtype=torch.long)

def predict_vqa(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if not os.path.exists(args.image):
        raise FileNotFoundError(f"Image '{args.image}' not found.")

    vocab_file = args.vocab or os.path.join(os.path.dirname(__file__), "manifests", "rsvqa_vocab.json")
    if not os.path.exists(vocab_file):
        raise FileNotFoundError(f"Vocab file '{vocab_file}' not found.")

    with open(vocab_file, "r", encoding="utf-8") as f:
        vocab_data = json.load(f)
        idx2ans = {int(k): v for k, v in vocab_data["idx2ans"].items()}

    print("============================================================")
    print("TRINETRA — RS-VQA Single Sample Prediction")
    print(f"Image:      {args.image}")
    print(f"Question:   \"{args.question}\"")
    print(f"Checkpoint: {args.checkpoint}")
    print("============================================================\n")

    # Load and preprocess image
    img = Image.open(args.image).convert("RGB").resize((224, 224), Image.BILINEAR)
    arr = np.array(img, dtype=np.float32) / 255.0
    arr = np.transpose(arr, (2, 0, 1))
    img_tensor = torch.from_numpy(arr).unsqueeze(0).to(device)

    # Tokenize question
    token_tensor = tokenize_query(args.question).to(device)

    # Model
    model = load_vqa_model(args.checkpoint, device=device)
    model.eval()

    with torch.no_grad():
        logits = model(img_tensor, token_tensor)
        probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()

    top3_indices = np.argsort(-probs)[:3]

    print("PREDICTED ANSWERS:")
    for rank, idx in enumerate(top3_indices, 1):
        ans_str = idx2ans.get(idx, f"Class {idx}")
        conf = probs[idx] * 100.0
        print(f"  #{rank}: {ans_str:<25} (Confidence: {conf:.2f}%)")
    print("============================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Answer question about a satellite image.")
    parser.add_argument("--image", type=str, required=True, help="Path to real satellite image.")
    parser.add_argument("--question", type=str, required=True, help="Natural language query.")
    default_ckpt = os.path.join(os.path.dirname(__file__), "..", "..", "models", "checkpoints", "rs_vqa_model", "model.pt")
    if not os.path.exists(default_ckpt):
        default_ckpt = os.path.join(os.path.dirname(__file__), "runs", "run_balanced", "best_model.pt")
    default_vocab = os.path.join(os.path.dirname(__file__), "manifests", "rsvqa_vocab.json")

    parser.add_argument("--checkpoint", type=str, default=default_ckpt, help=f"Path to trained model (default: {default_ckpt}).")
    parser.add_argument("--vocab", type=str, default=default_vocab, help="Path to vocabulary JSON.")
    args = parser.parse_args()

    predict_vqa(args)
