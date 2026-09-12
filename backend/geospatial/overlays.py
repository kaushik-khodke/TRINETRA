"""
SatQuery AI — Visual Evidence Overlay Engine
Generates bounding box overlays, segmentation masks, change heatmaps,
and optical–SAR fusion composites for frontend and report presentation.
"""

import io
import base64
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.cm as cm
from typing import List, Dict, Any, Optional

class EvidenceOverlayEngine:

    @staticmethod
    def render_bounding_boxes(
        base_img: Image.Image,
        boxes: List[Dict[str, Any]],
        color: str = "#10B981",  # Tactical Emerald
        label_prefix: str = "TARGET"
    ) -> Image.Image:
        """
        Draws tactical aerospace bounding boxes with coordinates and confidence badges.
        Box format expected: [ymin, xmin, ymax, xmax] in normalized (0..1) or pixel coordinates.
        """
        img = base_img.copy().convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        w, h = img.size

        for i, box_info in enumerate(boxes):
            coords = box_info.get("bbox", [0.1, 0.1, 0.4, 0.4])
            score = box_info.get("score", 0.90)
            label = box_info.get("label", f"{label_prefix} #{i+1}")

            # Normalize if needed
            if all(0.0 <= c <= 1.0 for c in coords):
                ymin, xmin, ymax, xmax = coords
                x1, y1, x2, y2 = int(xmin * w), int(ymin * h), int(xmax * w), int(ymax * h)
            else:
                x1, y1, x2, y2 = [int(c) for c in coords]

            # Ensure bounds
            x1, x2 = max(0, min(x1, x2)), min(w - 1, max(x1, x2))
            y1, y2 = max(0, min(y1, y2)), min(h - 1, max(y1, y2))

            # Semi-transparent fill
            draw.rectangle([x1, y1, x2, y2], fill=(16, 185, 129, 45), outline=(16, 185, 129, 230), width=2)

            # Tactical corner markers
            corner_len = min(15, (x2 - x1) // 3, (y2 - y1) // 3)
            # Top-left
            draw.line([(x1, y1), (x1 + corner_len, y1)], fill=(16, 185, 129, 255), width=3)
            draw.line([(x1, y1), (x1, y1 + corner_len)], fill=(16, 185, 129, 255), width=3)
            # Top-right
            draw.line([(x2, y1), (x2 - corner_len, y1)], fill=(16, 185, 129, 255), width=3)
            draw.line([(x2, y1), (x2, y1 + corner_len)], fill=(16, 185, 129, 255), width=3)
            # Bottom-left
            draw.line([(x1, y2), (x1 + corner_len, y2)], fill=(16, 185, 129, 255), width=3)
            draw.line([(x1, y2), (x1, y2 - corner_len)], fill=(16, 185, 129, 255), width=3)
            # Bottom-right
            draw.line([(x2, y2), (x2 - corner_len, y2)], fill=(16, 185, 129, 255), width=3)
            draw.line([(x2, y2), (x2, y2 - corner_len)], fill=(16, 185, 129, 255), width=3)

            # Label badge
            badge_text = f"{label.upper()} [{int(score * 100)}%]"
            badge_y = max(0, y1 - 20)
            badge_w = len(badge_text) * 7 + 10
            draw.rectangle([x1, badge_y, x1 + badge_w, badge_y + 18], fill=(9, 13, 16, 230), outline=(16, 185, 129, 200))
            draw.text((x1 + 4, badge_y + 2), badge_text, fill=(240, 246, 252, 255))

        composed = Image.alpha_composite(img, overlay)
        return composed.convert("RGB")

    @staticmethod
    def render_change_heatmap(
        base_img: Image.Image,
        diff_matrix: np.ndarray,
        threshold: float = 0.25
    ) -> Image.Image:
        """
        Renders an Amber/Solar-Gold change overlay on top of the base image.
        """
        w, h = base_img.size
        # Resize diff_matrix to match image
        diff_resized = Image.fromarray((diff_matrix * 255).astype(np.uint8)).resize((w, h), Image.Resampling.BILINEAR)
        diff_arr = np.array(diff_resized) / 255.0

        # Mask regions above threshold
        change_mask = diff_arr > threshold

        # Colormap for change (Solar Amber -> Coral)
        try:
            import matplotlib.pyplot as plt
            cmap = plt.get_cmap("YlOrRd")
        except Exception:
            cmap = cm.get_cmap("YlOrRd")
        colored_change = (cmap(diff_arr)[:, :, :3] * 255).astype(np.uint8)

        base_rgba = base_img.convert("RGBA")
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        overlay_arr = np.array(overlay)

        # Apply colored change to pixels with change
        overlay_arr[change_mask, 0] = colored_change[change_mask, 0]
        overlay_arr[change_mask, 1] = colored_change[change_mask, 1]
        overlay_arr[change_mask, 2] = colored_change[change_mask, 2]
        overlay_arr[change_mask, 3] = (np.clip(diff_arr[change_mask] * 180, 70, 210)).astype(np.uint8)

        overlay_img = Image.fromarray(overlay_arr, mode="RGBA")
        composed = Image.alpha_composite(base_rgba, overlay_img)
        return composed.convert("RGB")

    @staticmethod
    def render_optical_sar_composite(
        optical_img: Image.Image,
        sar_img: Image.Image
    ) -> Image.Image:
        """
        Synthesizes a cross-modal composite fusing Optical spectral hues with SAR structural radar backscatter.
        """
        w, h = optical_img.size
        sar_resized = sar_img.resize((w, h), Image.Resampling.BILINEAR).convert("L")
        opt_arr = np.array(optical_img).astype(np.float32)
        sar_arr = np.array(sar_resized).astype(np.float32) / 255.0

        # Structural high-frequency injection: blend SAR texture with Optical spectral channels
        fused = np.zeros_like(opt_arr)
        for c in range(3):
            fused[:, :, c] = opt_arr[:, :, c] * 0.65 + (sar_arr * 255.0) * 0.35

        fused = np.clip(fused, 0, 255).astype(np.uint8)
        return Image.fromarray(fused)

    @staticmethod
    def to_base64(img: Image.Image) -> str:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"
