"""
TRINETRA — Tactical Visual Evidence Overlay Engine
Renders high-precision aerospace bounding boxes, point markers, polygon segmentations,
spectral plots, change heatmaps, and optical–SAR fusion composites with anti-collision labeling.
"""

import io
import base64
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from typing import List, Dict, Any, Optional, Tuple

class EvidenceOverlayEngine:

    # Distinct tactical aerospace palette
    TACTICAL_PALETTE = [
        {"stroke": (16, 185, 129, 240),  "fill": (16, 185, 129, 35),  "hex": "#10B981"},  # R01: Emerald
        {"stroke": (6, 182, 212, 240),   "fill": (6, 182, 212, 35),   "hex": "#06B6D4"},  # R02: Cyan
        {"stroke": (245, 158, 11, 240),  "fill": (245, 158, 11, 35),  "hex": "#F59E0B"},  # R03: Amber
        {"stroke": (139, 92, 246, 240),  "fill": (139, 92, 246, 35),  "hex": "#8B5CF6"},  # R04: Violet
        {"stroke": (244, 63, 94, 240),   "fill": (244, 63, 94, 35),   "hex": "#F43F5E"},  # R05: Rose
        {"stroke": (59, 130, 246, 240),  "fill": (59, 130, 246, 35),  "hex": "#3B82F6"}   # R06: Blue
    ]

    @classmethod
    def render_bounding_boxes(
        cls,
        base_img: Image.Image,
        boxes: List[Dict[str, Any]],
        color: Optional[str] = None,
        label_prefix: str = "TARGET"
    ) -> Image.Image:
        """
        Draws tactical aerospace bounding boxes with coordinates, stable IDs, confidence,
        physical area, and automatic collision-avoiding badge placement.
        """
        img = base_img.copy().convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        w, h = img.size

        # Track placed badge rectangles for collision detection [x1, y1, x2, y2]
        occupied_badge_rects: List[Tuple[int, int, int, int]] = []

        def rects_overlap(r1, r2):
            return not (r1[2] < r2[0] or r1[0] > r2[2] or r1[3] < r2[1] or r1[1] > r2[3])

        for i, box_info in enumerate(boxes):
            coords = box_info.get("bbox", [0.1, 0.1, 0.4, 0.4])
            score = box_info.get("score", 0.90)
            reg_id = box_info.get("id") or (f"R0{i+1}" if i < 9 else f"R{i+1}")
            raw_label = box_info.get("label", f"{label_prefix} #{i+1}")
            # Simplify label
            clean_label = raw_label.replace("Target: ", "").replace("Identified ", "")
            area_m2 = box_info.get("physical_area_m2")

            # Format area text
            area_str = ""
            if area_m2 and area_m2 > 10000:
                area_str = f" | {round(area_m2 / 10000.0, 1)} ha"
            elif area_m2:
                area_str = f" | {int(area_m2)} m²"
            elif box_info.get("pixel_area"):
                area_str = f" | {box_info['pixel_area']} px"

            # Color style selection
            palette = cls.TACTICAL_PALETTE[i % len(cls.TACTICAL_PALETTE)]
            stroke_color = palette["stroke"]
            fill_color = palette["fill"]

            # Normalize coordinates
            if all(0.0 <= c <= 1.0 for c in coords):
                ymin, xmin, ymax, xmax = coords
                x1, y1, x2, y2 = int(xmin * w), int(ymin * h), int(xmax * w), int(ymax * h)
            else:
                x1, y1, x2, y2 = [int(c) for c in coords]

            x1, x2 = max(0, min(x1, x2)), min(w - 1, max(x1, x2))
            y1, y2 = max(0, min(y1, y2)), min(h - 1, max(y1, y2))

            # Semi-transparent fill and bounding rectangle
            draw.rectangle([x1, y1, x2, y2], fill=fill_color, outline=stroke_color, width=2)

            # Tactical corner brackets (3px width)
            c_len = max(8, min(18, (x2 - x1) // 4, (y2 - y1) // 4))
            draw.line([(x1, y1), (x1 + c_len, y1)], fill=stroke_color, width=3)
            draw.line([(x1, y1), (x1, y1 + c_len)], fill=stroke_color, width=3)
            draw.line([(x2, y1), (x2 - c_len, y1)], fill=stroke_color, width=3)
            draw.line([(x2, y1), (x2, y1 + c_len)], fill=stroke_color, width=3)
            draw.line([(x1, y2), (x1 + c_len, y2)], fill=stroke_color, width=3)
            draw.line([(x1, y2), (x1, y2 - c_len)], fill=stroke_color, width=3)
            draw.line([(x2, y2), (x2 - c_len, y2)], fill=stroke_color, width=3)
            draw.line([(x2, y2), (x2, y2 - c_len)], fill=stroke_color, width=3)

            # Center target crosshair if box is sufficiently large
            if (x2 - x1) > 40 and (y2 - y1) > 40:
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                draw.line([(cx - 4, cy), (cx + 4, cy)], fill=(255, 255, 255, 120), width=1)
                draw.line([(cx, cy - 4), (cx, cy + 4)], fill=(255, 255, 255, 120), width=1)

            # Tactical badge text: "R01 WATER BODY [94%] 12.8 ha"
            badge_text = f"{reg_id} {clean_label.upper()} [{int(score * 100)}%]{area_str}"
            badge_w = len(badge_text) * 7 + 12
            badge_h = 20

            # Candidate badge placements:
            # 1. Above top-left (standard)
            # 2. Inside top-left (if near top of image)
            # 3. Below bottom-left
            # 4. Right of box with leader line
            candidates = [
                (x1, y1 - badge_h - 2),          # above
                (x1 + 4, y1 + 4),               # inside top
                (x1, y2 + 4),                   # below
                (x2 + 8, y1)                    # right
            ]

            chosen_x, chosen_y = candidates[0]
            leader_needed = False

            for cx, cy in candidates:
                # Keep badge inside image bounds
                bx1 = max(2, min(w - badge_w - 2, cx))
                by1 = max(2, min(h - badge_h - 2, cy))
                test_rect = (bx1, by1, bx1 + badge_w, by1 + badge_h)

                # Check if it collides with previously placed badges
                collides = any(rects_overlap(test_rect, occ) for occ in occupied_badge_rects)
                if not collides and by1 >= 2 and by1 + badge_h <= h - 2:
                    chosen_x, chosen_y = bx1, by1
                    if cx == x2 + 8:
                        leader_needed = True
                    break
            else:
                # If all standard candidates collide, place with offset leader line
                chosen_x = max(2, min(w - badge_w - 2, x1 + (i * 20)))
                chosen_y = max(2, min(h - badge_h - 2, y1 - badge_h - 4 - (i * 22)))
                leader_needed = True

            bx1, by1 = chosen_x, chosen_y
            bx2, by2 = bx1 + badge_w, by1 + badge_h
            occupied_badge_rects.append((bx1, by1, bx2, by2))

            # Draw leader line if displaced
            if leader_needed:
                draw.line([(bx1, (by1 + by2) // 2), (x1, y1)], fill=stroke_color, width=1)

            # Draw badge background
            draw.rectangle([bx1, by1, bx2, by2], fill=(9, 13, 16, 230), outline=stroke_color, width=1)
            # Small colored ID indicator strip on the left of badge
            draw.rectangle([bx1, by1, bx1 + 4, by2], fill=stroke_color)
            draw.text((bx1 + 8, by1 + 3), badge_text, fill=(240, 246, 252, 255))

        composed = Image.alpha_composite(img, overlay)
        return composed.convert("RGB")

    @classmethod
    def render_point_markers(
        cls,
        base_img: Image.Image,
        points: List[Dict[str, Any]]
    ) -> Image.Image:
        """Draws pinpoint target crosshairs and concentric locator rings."""
        img = base_img.copy().convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        w, h = img.size

        for i, pt in enumerate(points):
            coords = pt.get("point") or pt.get("centroid_norm") or {"x": 0.5, "y": 0.5}
            xc = int(coords["x"] * w) if coords["x"] <= 1.0 else int(coords["x"])
            yc = int(coords["y"] * h) if coords["y"] <= 1.0 else int(coords["y"])
            label = pt.get("label", f"PT #{i+1}")
            reg_id = pt.get("id", f"P0{i+1}")
            palette = cls.TACTICAL_PALETTE[i % len(cls.TACTICAL_PALETTE)]
            stroke = palette["stroke"]

            # Concentric targeting rings
            draw.ellipse([xc - 8, yc - 8, xc + 8, yc + 8], outline=stroke, width=2)
            draw.ellipse([xc - 16, yc - 16, xc + 16, yc + 16], outline=(stroke[0], stroke[1], stroke[2], 120), width=1)
            # Center reticle
            draw.line([(xc - 22, yc), (xc + 22, yc)], fill=stroke, width=1)
            draw.line([(xc, yc - 22), (xc, yc + 22)], fill=stroke, width=1)

            # Badge callout
            badge_text = f"{reg_id} {label.upper()}"
            bx = min(w - 120, xc + 12)
            by = max(4, yc - 22)
            draw.rectangle([bx, by, bx + len(badge_text) * 7 + 8, by + 18], fill=(9, 13, 16, 230), outline=stroke)
            draw.text((bx + 4, by + 2), badge_text, fill=(240, 246, 252, 255))

        composed = Image.alpha_composite(img, overlay)
        return composed.convert("RGB")

    @classmethod
    def render_polygon_regions(
        cls,
        base_img: Image.Image,
        polygons: List[Dict[str, Any]]
    ) -> Image.Image:
        """Renders polygon boundary outlines and semi-transparent region fills."""
        img = base_img.copy().convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        w, h = img.size

        for i, poly in enumerate(polygons):
            coords = poly.get("polygon_coords") or []
            if len(coords) < 3:
                continue
            pixel_pts = [(int(c[0] * w), int(c[1] * h)) for c in coords]
            palette = cls.TACTICAL_PALETTE[i % len(cls.TACTICAL_PALETTE)]

            draw.polygon(pixel_pts, fill=palette["fill"], outline=palette["stroke"])

        composed = Image.alpha_composite(img, overlay)
        return composed.convert("RGB")

    @staticmethod
    def render_spectral_plot_overlay(
        wavelengths: List[float],
        mean_curve: List[float],
        std_curve: Optional[List[float]] = None,
        title: str = "Spectral Reflectance Profile"
    ) -> str:
        """Generates a base64 encoded PNG of the spectral reflectance signature curve."""
        fig, ax = plt.subplots(figsize=(6, 3.2), dpi=120, facecolor="#090D10")
        ax.set_facecolor("#0F172A")

        wl = np.array(wavelengths)
        mean = np.array(mean_curve)

        ax.plot(wl, mean, color="#10B981", linewidth=2.0, label="Mean Reflectance")
        if std_curve and len(std_curve) == len(wl):
            std = np.array(std_curve)
            ax.fill_between(wl, mean - std, mean + std, color="#10B981", alpha=0.25, label="±1σ Variance")

        ax.set_title(title, color="#E2E8F0", fontsize=11, fontweight="bold", pad=10)
        ax.set_xlabel("Wavelength (nm)", color="#94A3B8", fontsize=9)
        ax.set_ylabel("Reflectance", color="#94A3B8", fontsize=9)
        ax.tick_params(colors="#94A3B8", labelsize=8)
        ax.grid(True, linestyle="--", alpha=0.2, color="#64748B")
        for spine in ax.spines.values():
            spine.set_color("#334155")

        ax.legend(facecolor="#1E293B", edgecolor="#334155", labelcolor="#F1F5F9", fontsize=8)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"

    @staticmethod
    def render_change_heatmap(
        base_img: Image.Image,
        diff_matrix: np.ndarray,
        threshold: float = 0.25
    ) -> Image.Image:
        """Renders an Amber/Solar-Gold change overlay on top of the base image."""
        w, h = base_img.size
        diff_resized = Image.fromarray((diff_matrix * 255).astype(np.uint8)).resize((w, h), Image.Resampling.BILINEAR)
        diff_arr = np.array(diff_resized) / 255.0

        change_mask = diff_arr > threshold
        try:
            cmap = plt.get_cmap("YlOrRd")
        except Exception:
            cmap = cm.get_cmap("YlOrRd")
        colored_change = (cmap(diff_arr)[:, :, :3] * 255).astype(np.uint8)

        base_rgba = base_img.convert("RGBA")
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        overlay_arr = np.array(overlay)

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
        """Synthesizes a cross-modal composite fusing Optical spectral hues with SAR structural radar backscatter."""
        w, h = optical_img.size
        sar_resized = sar_img.resize((w, h), Image.Resampling.BILINEAR).convert("L")
        opt_arr = np.array(optical_img).astype(np.float32)
        sar_arr = np.array(sar_resized).astype(np.float32) / 255.0

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
