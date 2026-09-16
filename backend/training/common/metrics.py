"""
TRINETRA / SatQuery AI — Standardized Evaluation Metrics Library
Computes real benchmark metrics: mAP, Micro/Macro F1, Top-1/Top-5 Acc, IoU, and Recall@k.
"""

from typing import Dict, Any, List, Tuple, Optional
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


def binary_change_mask_metrics(
    y_pred_masks: np.ndarray,
    y_true_masks: np.ndarray,
    threshold: float = 0.5,
    compute_object_metrics: bool = True
) -> Dict[str, Any]:
    """
    Computes rigorous dense binary change detection evaluation metrics.
    Governed by Stage 4 Change Detection Protocol. Zero synthetic data.

    Args:
        y_pred_masks: Predicted probability map or binary mask (values in [0, 1]).
                      Shapes supported: (H, W), (N, H, W), or (N, 1, H, W).
        y_true_masks: Ground truth binary mask with values in {0, 1}.
                      Same shape or broadcastable to y_pred_masks.
        threshold: Decision threshold for binarization (default: 0.5).
        compute_object_metrics: Whether to run connected-component object-level analysis.

    Returns:
        Dictionary containing pixel-level metrics, confusion matrix, rates, and object metrics.
    """
    eps = 1e-8
    pred_arr = np.squeeze(np.asarray(y_pred_masks))
    true_arr = np.squeeze(np.asarray(y_true_masks))

    if pred_arr.shape != true_arr.shape:
        raise ValueError(
            f"Shape mismatch in change mask evaluation: pred {pred_arr.shape} vs true {true_arr.shape}"
        )

    # Binarize
    pred_bin = (pred_arr >= threshold).astype(np.uint8)
    true_bin = (true_arr >= 0.5).astype(np.uint8)

    # Pixel-level Confusion Matrix
    tp = int(np.sum((pred_bin == 1) & (true_bin == 1)))
    fp = int(np.sum((pred_bin == 1) & (true_bin == 0)))
    tn = int(np.sum((pred_bin == 0) & (true_bin == 0)))
    fn = int(np.sum((pred_bin == 0) & (true_bin == 1)))
    total_pixels = int(true_bin.size)

    # Rates and Scores
    precision = float(tp / (tp + fp + eps))
    recall = float(tp / (tp + fn + eps))
    f1 = float(2 * (precision * recall) / (precision + recall + eps))
    iou = float(tp / (tp + fp + fn + eps))
    accuracy = float((tp + tn) / (total_pixels + eps))
    fpr = float(fp / (fp + tn + eps))
    fnr = float(fn / (fn + tp + eps))

    results: Dict[str, Any] = {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "iou": round(iou, 4),
        "accuracy": round(accuracy, 4),
        "confusion_matrix": {
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn
        },
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "total_pixels": total_pixels,
        "changed_pixels_gt": tp + fn,
        "changed_pixels_pred": tp + fp,
        "change_fraction_gt": round(float((tp + fn) / (total_pixels + eps)), 4),
        "change_fraction_pred": round(float((tp + fp) / (total_pixels + eps)), 4),
        "threshold": threshold,
    }

    if compute_object_metrics:
        try:
            import scipy.ndimage as ndi

            # Standardize to a list of 2D image pairs
            if pred_bin.ndim == 2:
                pairs = [(pred_bin, true_bin)]
            elif pred_bin.ndim == 3:
                pairs = [(pred_bin[i], true_bin[i]) for i in range(pred_bin.shape[0])]
            else:
                pairs = []

            total_gt_objects = 0
            detected_gt_objects = 0
            total_pred_objects = 0
            valid_pred_objects = 0

            structure = np.ones((3, 3), dtype=np.uint8)

            for p_slice, t_slice in pairs:
                labeled_gt, num_gt = ndi.label(t_slice, structure=structure)
                labeled_pred, num_pred = ndi.label(p_slice, structure=structure)

                total_gt_objects += num_gt
                total_pred_objects += num_pred

                # Evaluate GT recovery
                for obj_id in range(1, num_gt + 1):
                    obj_mask = (labeled_gt == obj_id)
                    if np.any(p_slice[obj_mask] == 1):
                        detected_gt_objects += 1

                # Evaluate Pred validity (false alarm detection)
                for pred_id in range(1, num_pred + 1):
                    pred_mask = (labeled_pred == pred_id)
                    if np.any(t_slice[pred_mask] == 1):
                        valid_pred_objects += 1

            missed_gt_objects = total_gt_objects - detected_gt_objects
            false_alarm_objects = total_pred_objects - valid_pred_objects

            obj_rec = float(detected_gt_objects / (total_gt_objects + eps)) if total_gt_objects > 0 else 1.0
            obj_prec = float(valid_pred_objects / (total_pred_objects + eps)) if total_pred_objects > 0 else (1.0 if total_pred_objects == 0 else 0.0)
            obj_f1 = float(2 * (obj_prec * obj_rec) / (obj_prec + obj_rec + eps))

            results["object_metrics"] = {
                "gt_object_count": total_gt_objects,
                "pred_object_count": total_pred_objects,
                "detected_objects": detected_gt_objects,
                "missed_objects": missed_gt_objects,
                "false_alarm_objects": false_alarm_objects,
                "object_precision": round(obj_prec, 4),
                "object_recall": round(obj_rec, 4),
                "object_f1": round(obj_f1, 4),
            }
        except Exception as e:
            results["object_metrics"] = {"error": f"Object metric computation failed: {str(e)}"}

    return results


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


def hyperspectral_metrics(
    y_pred: Any,
    y_true: Any,
    num_classes: Optional[int] = None,
    ignore_index: Optional[int] = None,
    class_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Computes standard Hyperspectral Remote Sensing classification metrics:
    - Overall Accuracy (OA)
    - Average Accuracy (AA, mean per-class recall)
    - Cohen's Kappa Coefficient (kappa)
    - Macro F1 and per-class Precision, Recall, F1, and Support
    - Confusion Matrix

    Supports tensor or numpy inputs. Automatically handles ignore_index (e.g. background 0).
    """
    # Convert inputs to numpy
    if isinstance(y_pred, torch.Tensor):
        if y_pred.ndim > 1 and y_pred.shape[-1] > 1 and not (y_pred.ndim == 2 and y_pred.shape[1] == 1):
            # Logits or probability distributions -> take argmax
            y_pred = torch.argmax(y_pred, dim=-1)
        y_pred = y_pred.detach().cpu().numpy()
    elif isinstance(y_pred, np.ndarray):
        if y_pred.ndim > 1 and y_pred.shape[-1] > 1 and not (y_pred.ndim == 2 and y_pred.shape[1] == 1):
            y_pred = np.argmax(y_pred, axis=-1)

    if isinstance(y_true, torch.Tensor):
        y_true = y_true.detach().cpu().numpy()

    y_pred = np.asarray(y_pred).ravel().astype(np.int64)
    y_true = np.asarray(y_true).ravel().astype(np.int64)

    if len(y_pred) != len(y_true):
        raise ValueError(f"Shape mismatch: y_pred has {len(y_pred)} elements, y_true has {len(y_true)}")

    # Filter ignore_index (e.g. unclassified background pixels)
    if ignore_index is not None:
        valid_mask = (y_true != ignore_index)
        y_pred = y_pred[valid_mask]
        y_true = y_true[valid_mask]

    n_samples = len(y_true)
    if n_samples == 0:
        return {
            "overall_accuracy": 0.0,
            "oa_percent": 0.0,
            "average_accuracy": 0.0,
            "aa_percent": 0.0,
            "kappa_coefficient": 0.0,
            "macro_f1": 0.0,
            "num_classes": 0,
            "total_samples": 0,
            "per_class": {},
            "confusion_matrix": []
        }

    # Determine number of classes
    if num_classes is None:
        max_cls = max(int(np.max(y_true)), int(np.max(y_pred)))
        k = max_cls + 1
    else:
        k = int(num_classes)

    # Build Confusion Matrix C of shape (k, k): rows = true, cols = pred
    conf_mat = np.zeros((k, k), dtype=np.int64)
    # Clip indices to prevent out of bounds
    valid_range_mask = (y_true >= 0) & (y_true < k) & (y_pred >= 0) & (y_pred < k)
    y_true_valid = y_true[valid_range_mask]
    y_pred_valid = y_pred[valid_range_mask]

    for t, p in zip(y_true_valid, y_pred_valid):
        conf_mat[t, p] += 1

    # Overall Accuracy (OA)
    total_correct = int(np.trace(conf_mat))
    oa = float(total_correct / n_samples)

    # Cohen's Kappa Coefficient
    row_sums = conf_mat.sum(axis=1)  # Ground truth sums per class
    col_sums = conf_mat.sum(axis=0)  # Prediction sums per class
    p_e = float(np.sum(row_sums.astype(np.float64) * col_sums.astype(np.float64)) / (n_samples ** 2))

    if abs(1.0 - p_e) < 1e-12:
        kappa = 1.0 if oa == 1.0 else 0.0
    else:
        kappa = float((oa - p_e) / (1.0 - p_e))
    kappa = max(-1.0, min(1.0, kappa))

    # Per-class metrics
    eps = 1e-8
    per_class_recalls = []
    per_class_f1s = []
    per_class_dict = {}

    for c in range(k):
        c_name = class_names[c] if (class_names is not None and c < len(class_names)) else f"class_{c}"
        tp = int(conf_mat[c, c])
        support = int(row_sums[c])
        pred_c = int(col_sums[c])

        recall = float(tp / (support + eps)) if support > 0 else 0.0
        precision = float(tp / (pred_c + eps)) if pred_c > 0 else 0.0
        f1 = float(2 * (precision * recall) / (precision + recall + eps)) if (precision + recall) > 0 else 0.0

        if support > 0:
            per_class_recalls.append(recall)
            per_class_f1s.append(f1)

        per_class_dict[c_name] = {
            "class_index": c,
            "accuracy": round(recall, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": support
        }

    # Average Accuracy (AA) = mean of per-class accuracies/recalls for observed classes
    aa = float(np.mean(per_class_recalls)) if per_class_recalls else 0.0
    macro_f1 = float(np.mean(per_class_f1s)) if per_class_f1s else 0.0

    return {
        "overall_accuracy": round(oa, 4),
        "oa_percent": round(oa * 100.0, 2),
        "average_accuracy": round(aa, 4),
        "aa_percent": round(aa * 100.0, 2),
        "kappa_coefficient": round(kappa, 4),
        "macro_f1": round(macro_f1, 4),
        "num_classes": k,
        "total_samples": n_samples,
        "evaluated_classes": len(per_class_recalls),
        "per_class": per_class_dict,
        "confusion_matrix": conf_mat.tolist()
    }

