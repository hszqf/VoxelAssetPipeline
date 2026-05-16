#!/usr/bin/env python3
"""Render 64-cell side/front/top reference views for voxel assets."""

from __future__ import annotations

from pathlib import Path

from .model import COLORS, write_png
from .checks import read_vox

VIEWS = [
    ("side", ("x", "y"), "z", 1),
    ("front", ("z", "y"), "x", -1),
    ("top", ("x", "z"), "y", 1),
]


def put_pixel(pixels, width: int, height: int, x: int, y: int, color) -> None:
    if 0 <= x < width and 0 <= y < height:
        pixels[y * width + x] = color


def fill_rect(pixels, width: int, height: int, x0: int, y0: int, w: int, h: int, color) -> None:
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            put_pixel(pixels, width, height, x, y, color)


def stroke_rect(pixels, width: int, height: int, x0: int, y0: int, w: int, h: int, color) -> None:
    for x in range(x0, x0 + w):
        put_pixel(pixels, width, height, x, y0, color)
        put_pixel(pixels, width, height, x, y0 + h - 1, color)
    for y in range(y0, y0 + h):
        put_pixel(pixels, width, height, x0, y, color)
        put_pixel(pixels, width, height, x0 + w - 1, y, color)


def axis_index(axis: str) -> int:
    return {"x": 0, "y": 1, "z": 2}[axis]


def visible_projection(model: dict, view, offset: tuple[int, int, int] = (0, 0, 0)) -> dict[tuple[int, int], str]:
    _, axes, depth_axis, depth_direction = view
    a = axis_index(axes[0])
    b = axis_index(axes[1])
    d = axis_index(depth_axis)
    chosen: dict[tuple[int, int], tuple[int, str]] = {}
    for pos, color in model["voxels"].items():
        shifted = (pos[0] + offset[0], pos[1] + offset[1], pos[2] + offset[2])
        key = (shifted[a], shifted[b])
        depth = shifted[d] * depth_direction
        if key not in chosen or depth > chosen[key][0]:
            chosen[key] = (depth, color)
    return {key: color for key, (_, color) in chosen.items()}


def render_review(path: Path, out_dir: Path, assets: list[str], frame_size: list[int]) -> None:
    cell_w = 280
    cell_h = 190
    width = cell_w * len(VIEWS)
    height = cell_h * len(assets)
    bg = (244, 241, 233, 255)
    grid = (216, 212, 202, 255)
    border = (32, 32, 30, 96)
    bbox = (33, 182, 215, 255)
    pixels = [bg for _ in range(width * height)]

    for row, asset in enumerate(assets):
        model = read_vox(out_dir / f"{asset}.vox")
        offset = (
            (frame_size[0] - model["size"][0]) // 2,
            0,
            (frame_size[2] - model["size"][2]) // 2,
        )
        for col, view in enumerate(VIEWS):
            _, axes, _, _ = view
            view_w = frame_size[axis_index(axes[0])]
            view_h = frame_size[axis_index(axes[1])]
            scale = min((cell_w - 54) / view_w, (cell_h - 42) / view_h)
            ox = int(col * cell_w + (cell_w - view_w * scale) * 0.5)
            oy = int(row * cell_h + (cell_h - view_h * scale) * 0.5)
            for x in range(view_w + 1):
                px = int(ox + x * scale)
                for y in range(oy, int(oy + view_h * scale) + 1):
                    put_pixel(pixels, width, height, px, y, grid)
            for y in range(view_h + 1):
                py = int(oy + y * scale)
                for x in range(ox, int(ox + view_w * scale) + 1):
                    put_pixel(pixels, width, height, x, py, grid)
            stroke_rect(pixels, width, height, ox, oy, int(view_w * scale), int(view_h * scale), border)

            projection = visible_projection(model, view, offset)
            for (vx, vy), color_name in projection.items():
                x0 = int(ox + vx * scale)
                y0 = int(oy + (view_h - vy - 1) * scale)
                fill_rect(pixels, width, height, x0, y0, max(1, int(scale)), max(1, int(scale)), COLORS[color_name])
            stroke_rect(pixels, width, height, ox, oy, int(view_w * scale), int(view_h * scale), bbox)
    write_png(path, width, height, pixels)
