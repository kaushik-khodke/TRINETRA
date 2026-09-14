"""
TRINETRA / SatQuery AI — Standardized Evaluation Metrics Library
Computes real benchmark metrics: mAP, Micro/Macro F1, Top-1/Top-5 Acc, IoU, and Recall@k.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import torch

def calculate_iou(box1: np.ndarray, box2: np.ndarray) -> float:
    """
    Computes Intersection over Union (IoU) for two bounding boxes.
    Format: [ymin, xmin, ymax, xmax] or [xmin, ymin, xmax, ymax].
    """
    # Robustly sort coordinates so min < max for both predicted and target boxes
    y1_min, y1_max = min(float(box1[0]), float(box1[2])), max(float(box1[0]), float(box1[2]))
    x1_min, x1_max = min(float(box1[1]), float(box1[3])), max(float(box1[1]), float(box1[3]))
    y2_min, y2_max = min(float(box2[0]), float(box2[2])), max(float(box2[0]), float(box2[2]))
    x2_min, x2_max = min(float(box2[1]), float(box2[3])), max(float(box2[1]), float(box2[3]))

    inter_ymin = max(y1_min, y2_min)
    inter_xmin = max(x1_min, x2_min)
    inter_ymax = min(y1_max, y2_max)
    inter_xmax = min(x1_max, x2_max)

    inter_w = max(0.0, inter_xmax - inter_xmin)
    inter_h = max(0.0, inter_ymax - inter_ymin)
    inter_area = inter_w * inter_h

    area1 = max(0.0, x1_max - x1_min) * max(0.0, y1_max - y1_min)
    area2 = max(0.0, x2_max - x2_min) * max(0.0, y2_max - y2_min)
    union_area = area1 + area2 - inter_area

    if union_area <= 1e-8:
        return 0.0
    return float(inter_area / union_area)

def multilabel_metrics(y_probs: np.ndarray, y_true: np.ndarray, threshold: float = 0.5) -> Dict[str, Any]:
    """
    Computes standard multi-label land-cover classification metrics.
    - mAP (Mean Average Precision across classes)
    - Micro F1, Macro F1
    - Micro Precision, Micro Recall
    """
    eps = 1e-8
    num_classes = y_true.shape[1]
    y_pred = (y_probs >= threshold).astype(float)

    # Per-class Average Precision (AP)
    per_class_ap = []
    for c in range(num_classes):
        target_c = y_true[:, c]
        scores_c = y_probs[:, c]
        if target_c.sum() == 0:
            continue
        # Sort scores descending
        order = np.argsort(-scores_c)
        sorted_targets = target_c[order]
        tp_cumsum = np.cumsum(sorted_targets)
        ranks = np.arange(1, len(sorted_targets) + 1)
        precisions = tp_cumsum / ranks
        ap = float(np.sum(precisions * sorted_targets) / (target_c.sum() + eps))
        per_class_ap.append(ap)

    mean_ap = float(np.mean(per_class_ap)) if per_class_ap else 0.0

    # Micro metrics
    tp_micro = np.sum((y_pred == 1) & (y_true == 1))
    fp_micro = np.sum((y_pred == 1) & (y_true == 0))
    fn_micro = np.sum((y_pred == 0) & (y_true == 1))

    prec_micro = float(tp_micro / (tp_micro + fp_micro + eps))
    rec_micro = float(tp_micro / (tp_micro + fn_micro + eps))
    f1_micro = float(2 * (prec_micro * rec_micro) / (prec_micro + rec_micro + eps))

    # Macro F1
    f1_per_class = []
    for c in range(num_classes):
        tp_c = np.sum((y_pred[:, c] == 1) & (y_true[:, c] == 1))
        fp_c = np.sum((y_pred[:, c] == 1) & (y_true[:, c] == 0))
        fn_c = np.sum((y_pred[:, c] == 0) & (y_true[:, c] == 1))
        p = tp_c / (tp_c + fp_c + eps)
        r = tp_c / (tp_c + fn_c + eps)
        f = 2 * (p * r) / (p + r + eps)
        f1_per_class.append(f)
    f1_macro = float(np.mean(f1_per_class))

    return {
        "mAP": round(mean_ap, 4),
        "micro_f1": round(f1_micro, 4),
        "macro_f1": round(f1_macro, 4),
        "micro_precision": round(prec_micro, 4),
        "micro_recall": round(rec_micro, 4),
        "evaluated_classes": len(per_class_ap)
    }

def vqa_metrics(logits: np.ndarray, targets: np.ndarray) -> Dict[str, Any]:
    """Computes Top-1 and Top-5 VQA classification accuracy."""
    preds_top1 = np.argmax(logits, axis=1)
    top1_acc = float(np.mean(preds_top1 == targets)) * 100.0

    k = min(5, logits.shape[1])
    top5_indices = np.argpartition(-logits, kth=k-1, axis=1)[:, :k]
    top5_correct = [targets[i] in top5_indices[i] for i in range(len(targets))]
    top5_acc = float(np.mean(top5_correct)) * 100.0

    return {
        "top1_accuracy_pct": round(top1_acc, 2),
        "top5_accuracy_pct": round(top5_acc, 2),
        "num_samples": len(targets)
    }

def grounding_metrics(pred_boxes: np.ndarray, gt_boxes: np.ndarray) -> Dict[str, Any]:
    """
    Computes referring expression grounding metrics:
    - Mean IoU (mIoU)
    - Median IoU
    - Recall@0.50 (percentage of samples with IoU >= 0.50)
    - Recall@0.75 (percentage of samples with IoU >= 0.75)
    - Failure count (IoU < 0.10)
    """
    n = len(pred_boxes)
    ious = []
    for i in range(n):
        iou = calculate_iou(pred_boxes[i], gt_boxes[i])
        ious.append(iou)

    ious_arr = np.array(ious)
    mean_iou = float(np.mean(ious_arr))
    median_iou = float(np.median(ious_arr))
    rec_50 = float(np.mean(ious_arr >= 0.50)) * 100.0
    rec_75 = float(np.mean(ious_arr >= 0.75)) * 100.0
    failures = int(np.sum(ious_arr < 0.10))

    return {
        "mean_iou": round(mean_iou, 4),
        "median_iou": round(median_iou, 4),
        "recall_at_0.50_pct": round(rec_50, 2),
        "recall_at_0.75_pct": round(rec_75, 2),
        "failure_count": failures,
        "total_samples": n
    }

def change_metrics(y_pred_classes: np.ndarray, y_true_classes: np.ndarray) -> Dict[str, Any]:
    """Computes multi-class change metrics (Accuracy, Macro F1, Per-class accuracy)."""
    eps = 1e-8
    acc = float(np.mean(y_pred_classes == y_true_classes)) * 100.0
    unique_classes = np.unique(y_true_classes)

    f1s = []
    per_class = {}
    for c in unique_classes:
        tp = np.sum((y_pred_classes == c) & (y_true_classes == c))
        fp = np.sum((y_pred_classes == c) & (y_true_classes != c))
        fn = np.sum((y_pred_classes != c) & (y_true_classes == c))
        p = tp / (tp + fp + eps)
        r = tp / (tp + fn + eps)
        f = 2 * (p * r) / (p + r + eps)
        f1s.append(f)
        per_class[f"class_{int(c)}_acc"] = round(float(tp / (tp + fn + eps)) * 100.0, 2)

    macro_f1 = float(np.mean(f1s)) if f1s else 0.0
    return {
        "accuracy_pct": round(acc, 2),
        "macro_f1": round(macro_f1, 4),
        "per_class_accuracy": per_class,
        "total_samples": len(y_true_classes)
    }

def fusion_metrics(opt_acc: float, sar_acc: float, fused_acc: float) -> Dict[str, Any]:
    """Computes cross-modal fusion evaluation comparison."""
    delta_opt = fused_acc - opt_acc
    delta_sar = fused_acc - sar_acc
    return {
        "optical_only_accuracy": round(opt_acc, 2),
        "sar_only_accuracy": round(sar_acc, 2),
        "optical_sar_fused_accuracy": round(fused_acc, 2),
        "fusion_delta_vs_optical": round(delta_opt, 2),
        "fusion_delta_vs_sar": round(delta_sar, 2),
        "fusion_outperforms_both": bool(delta_opt > 0 and delta_sar > 0)
    }
