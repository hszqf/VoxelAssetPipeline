#!/usr/bin/env python3
"""Normalize noisy AI Side/Front/Top source sheets without changing design intent."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import statistics
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from voxel_asset_pipeline.model import write_png
    from voxel_asset_pipeline.render import draw_line, draw_text, fill_rect, stroke_rect
    from voxel_asset_pipeline.source_sheet_check import Frame, detect_grid_frames, luminance, parse_frame, read_png_rgba, saturation
else:
    from .model import write_png
    from .render import draw_line, draw_text, fill_rect, stroke_rect
    from .source_sheet_check import Frame, detect_grid_frames, luminance, parse_frame, read_png_rgba, saturation

RGBA = tuple[int, int, int, int]


def grid_line_pixel(p: RGBA) -> bool:
    if p[3] < 128:
        return False
    mx = max(p[0], p[1], p[2])
    mn = min(p[0], p[1], p[2])
    return mx - mn <= 24 and 95 <= luminance(p) <= 245 and saturation(p) < 0.11


def bg_or_grid_pixel(p: RGBA) -> bool:
    mx = max(p[0], p[1], p[2])
    mn = min(p[0], p[1], p[2])
    return saturation(p) < 0.10 and luminance(p) > 90 and mx - mn <= 32


def bucket_rgb(p: RGBA, bucket_size: int) -> RGBA:
    rgb = tuple(min(255, max(0, int(round(channel / bucket_size) * bucket_size))) for channel in p[:3])
    return (rgb[0], rgb[1], rgb[2], 255)


def group_centers(scores: list[int], threshold: float) -> list[float]:
    centers: list[float] = []
    start: int | None = None
    values: list[int] = []
    for i, score in enumerate(scores):
        if score >= threshold:
            if start is None:
                start = i
                values = []
            values.append(score)
        elif start is not None:
            end = i - 1
            if end - start <= 9:
                total = sum(values)
                center = sum((start + j) * value for j, value in enumerate(values)) / total if total else (start + end) / 2
                centers.append(center)
            start = None
            values = []
    if start is not None:
        end = len(scores) - 1
        if end - start <= 9:
            total = sum(values)
            center = sum((start + j) * value for j, value in enumerate(values)) / total if total else (start + end) / 2
            centers.append(center)
    return centers


def merge_close(values: list[float], min_dist: float = 8.0) -> list[float]:
    if not values:
        return []
    merged: list[float] = []
    cluster = [sorted(values)[0]]
    for value in sorted(values)[1:]:
        if value - cluster[-1] <= min_dist:
            cluster.append(value)
        else:
            merged.append(sum(cluster) / len(cluster))
            cluster = [value]
    merged.append(sum(cluster) / len(cluster))
    return merged


def detected_line_positions(frame: Frame, width: int, pixels: list[RGBA], axis: str) -> tuple[list[float], list[float], float]:
    if axis == "x":
        scores = [
            sum(1 for yy in range(frame.h) if grid_line_pixel(pixels[(frame.y + yy) * width + frame.x + xx]))
            for xx in range(frame.w)
        ]
        length = frame.w
        ortho = frame.h
    elif axis == "y":
        scores = [
            sum(1 for xx in range(frame.w) if grid_line_pixel(pixels[(frame.y + yy) * width + frame.x + xx]))
            for yy in range(frame.h)
        ]
        length = frame.h
        ortho = frame.w
    else:
        raise ValueError(f"unsupported axis {axis!r}")

    raw: list[float] = []
    for pct in (0.25, 0.20, 0.16, 0.12):
        raw.extend(group_centers(scores, ortho * pct))
    raw = merge_close(raw)
    diffs = [b - a for a, b in zip(raw, raw[1:]) if 14 <= b - a <= 38]
    spacing = statistics.median(diffs) if diffs else length / 24
    intervals = max(1, round((length - 1) / spacing))
    step = (length - 1) / intervals
    lines = [i * step for i in range(intervals + 1)]
    return lines, raw, spacing


def draw_grid(pixels: list[RGBA], width: int, height: int, x0: int, y0: int, panel_px: int, grid_size: int) -> None:
    stroke_rect(pixels, width, height, x0 - 2, y0 - 2, panel_px + 4, panel_px + 4, (0, 0, 0, 255))
    for i in range(grid_size + 1):
        x = x0 + round(i * panel_px / grid_size)
        y = y0 + round(i * panel_px / grid_size)
        draw_line(pixels, width, height, x, y0, x, y0 + panel_px, (182, 182, 182, 255))
        draw_line(pixels, width, height, x0, y, x0 + panel_px, y, (182, 182, 182, 255))


def cell_bounds(c0: float, c1: float, padding: float) -> tuple[int, int]:
    pad = max(1.0, (c1 - c0) * padding)
    return int(c0 + pad), int(c1 - pad + 0.9999)


def clean_sheet(args: argparse.Namespace) -> dict:
    image_path = Path(args.image)
    width, height, pixels = read_png_rgba(image_path)
    frames = [args.side_frame, args.front_frame, args.top_frame] if args.side_frame and args.front_frame and args.top_frame else detect_grid_frames(width, height, pixels)
    if len(frames) != 3:
        return {
            "asset": args.asset,
            "image": str(image_path),
            "pass": False,
            "checks": [{"id": "orthographic_frame_count", "pass": False, "expected": 3, "actual": len(frames)}],
        }

    grid_size = int(args.grid_size)
    cell_px = int(args.cell_px)
    panel_px = grid_size * cell_px
    margin_x = int(args.margin_x)
    panel_gap = int(args.panel_gap)
    panel_y = int(args.panel_y)
    title_y = int(args.title_y)
    label_y = int(args.label_y)
    label_x = int(args.label_x)
    out_width = margin_x * 2 + panel_px * 3 + panel_gap * 2
    out_height = panel_y + panel_px + int(args.bottom_margin)
    out_pixels = [(255, 255, 255, 255) for _ in range(out_width * out_height)]
    overlay_pixels = list(pixels)

    draw_text(out_pixels, out_width, out_height, label_x, label_y, args.asset, (0, 0, 0, 255), 4)
    panel_x = {
        "side": margin_x,
        "front": margin_x + panel_px + panel_gap,
        "top": margin_x + (panel_px + panel_gap) * 2,
    }
    report: dict = {
        "asset": args.asset,
        "image": str(image_path),
        "grid_size": grid_size,
        "cell_px": cell_px,
        "bucket_size": args.bucket_size,
        "sample_padding": args.sample_padding,
        "object_threshold": args.object_threshold,
        "frames": {},
        "views": {},
        "sampling": "cut by detected source grid lines; center source cells in target grid; color is per-cell non-background RGB bucket mode",
    }

    for title, name, frame in zip(["Side", "Front", "Top"], ["side", "front", "top"], frames, strict=True):
        xbase = panel_x[name]
        text_w = (len(title) * 6 - 1) * 4
        draw_text(out_pixels, out_width, out_height, xbase + (panel_px - text_w) // 2, title_y, title, (0, 0, 0, 255), 4)
        draw_grid(out_pixels, out_width, out_height, xbase, panel_y, panel_px, grid_size)

        xlines, raw_x, sx = detected_line_positions(frame, width, pixels, "x")
        ylines, raw_y, sy = detected_line_positions(frame, width, pixels, "y")
        src_cols = len(xlines) - 1
        src_rows = len(ylines) - 1
        offset_x = (grid_size - src_cols) // 2
        offset_y = (grid_size - src_rows) // 2
        occupied: dict[tuple[int, int], RGBA] = {}

        for line in xlines:
            x = frame.x + round(line)
            draw_line(overlay_pixels, width, height, x, frame.y, x, frame.y + frame.h - 1, (0, 120, 255, 190))
        for line in ylines:
            y = frame.y + round(line)
            draw_line(overlay_pixels, width, height, frame.x, y, frame.x + frame.w - 1, y, (255, 80, 0, 190))

        for cy in range(src_rows):
            for cx in range(src_cols):
                px0 = frame.x + xlines[cx]
                px1 = frame.x + xlines[cx + 1]
                py0 = frame.y + ylines[cy]
                py1 = frame.y + ylines[cy + 1]
                ix0, ix1 = cell_bounds(px0, px1, args.sample_padding)
                iy0, iy1 = cell_bounds(py0, py1, args.sample_padding)
                buckets: Counter[RGBA] = Counter()
                total = 0
                for yy in range(iy0, iy1):
                    for xx in range(ix0, ix1):
                        total += 1
                        if xx < frame.x + 2 or xx >= frame.x + frame.w - 2 or yy < frame.y + 2 or yy >= frame.y + frame.h - 2:
                            continue
                        if xx < 0 or xx >= width or yy < 0 or yy >= height:
                            continue
                        p = pixels[yy * width + xx]
                        if bg_or_grid_pixel(p):
                            continue
                        buckets[bucket_rgb(p, args.bucket_size)] += 1
                non_bg = sum(buckets.values())
                if total and non_bg / total >= args.object_threshold:
                    ox = offset_x + cx
                    oy = offset_y + cy
                    if 0 <= ox < grid_size and 0 <= oy < grid_size:
                        color = buckets.most_common(1)[0][0]
                        occupied[(ox, oy)] = color
                        fill_rect(
                            out_pixels,
                            out_width,
                            out_height,
                            xbase + ox * cell_px + 1,
                            panel_y + oy * cell_px + 1,
                            cell_px - 1,
                            cell_px - 1,
                            color,
                        )

        draw_grid(out_pixels, out_width, out_height, xbase, panel_y, panel_px, grid_size)
        xs = [x for x, _y in occupied]
        ys = [y for _x, y in occupied]
        report["frames"][name] = {"x": frame.x, "y": frame.y, "w": frame.w, "h": frame.h}
        report["views"][name] = {
            "detected_source_grid": [src_cols, src_rows],
            "raw_line_counts": [len(raw_x), len(raw_y)],
            "spacing_estimate": [round(sx, 2), round(sy, 2)],
            "output_offset": [offset_x, offset_y],
            "cells": len(occupied),
            "bbox": [min(xs), min(ys), max(xs) + 1, max(ys) + 1] if occupied else None,
            "size": [max(xs) + 1 - min(xs), max(ys) + 1 - min(ys)] if occupied else None,
        }

    if args.out:
        write_png(Path(args.out), out_width, out_height, out_pixels)
    if args.overlay_out:
        write_png(Path(args.overlay_out), width, height, overlay_pixels)
    report["pass"] = True
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Clean an AI Side/Front/Top source sheet by cutting the source's own grid lines.")
    parser.add_argument("--image", required=True)
    parser.add_argument("--asset", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out")
    parser.add_argument("--overlay-out")
    parser.add_argument("--grid-size", type=int, default=32)
    parser.add_argument("--cell-px", type=int, default=16)
    parser.add_argument("--bucket-size", type=int, default=8)
    parser.add_argument("--sample-padding", type=float, default=0.18)
    parser.add_argument("--object-threshold", type=float, default=0.18)
    parser.add_argument("--margin-x", type=int, default=34)
    parser.add_argument("--panel-gap", type=int, default=34)
    parser.add_argument("--panel-y", type=int, default=132)
    parser.add_argument("--title-y", type=int, default=82)
    parser.add_argument("--label-x", type=int, default=34)
    parser.add_argument("--label-y", type=int, default=24)
    parser.add_argument("--bottom-margin", type=int, default=42)
    parser.add_argument("--side-frame", type=parse_frame)
    parser.add_argument("--front-frame", type=parse_frame)
    parser.add_argument("--top-frame", type=parse_frame)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = clean_sheet(args)
    except Exception as exc:  # noqa: BLE001
        report = {
            "asset": args.asset if "args" in locals() else None,
            "image": args.image if "args" in locals() else None,
            "pass": False,
            "checks": [{"id": "cleaner_error", "pass": False, "expected": "successful source sheet cleanup", "actual": str(exc)}],
        }
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if getattr(args, "json_out", None):
        Path(args.json_out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
