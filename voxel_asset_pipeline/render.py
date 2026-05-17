#!/usr/bin/env python3
"""Render 64-cell side/front/top reference views for voxel assets."""

from __future__ import annotations

from pathlib import Path

from .model import COLORS, VoxelModel, draw_polygon, iter_face_polygons, write_png
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


def draw_line(pixels, width: int, height: int, x0: int, y0: int, x1: int, y1: int, color) -> None:
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        put_pixel(pixels, width, height, x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def stroke_rect_thick(pixels, width: int, height: int, x: int, y: int, w: int, h: int, color, thickness: int) -> None:
    for i in range(thickness):
        stroke_rect(pixels, width, height, x + i, y + i, max(1, w - i * 2), max(1, h - i * 2), color)


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


def model_to_dict(model: VoxelModel) -> dict:
    return {"size": [model.width, model.height, model.depth], "voxels": model.voxels}


def model_offset(model: VoxelModel, frame_size: int = 64) -> tuple[int, int, int]:
    return ((frame_size - model.width) // 2, 0, (frame_size - model.depth) // 2)


def projected_bounds(model: VoxelModel, view, frame_size: int = 64) -> tuple[int, int, int, int]:
    _, axes, _, _ = view
    offset = model_offset(model, frame_size)
    ranges = {
        "x": (offset[0], offset[0] + model.width),
        "y": (0, model.height),
        "z": (offset[2], offset[2] + model.depth),
    }
    a0, a1 = ranges[axes[0]]
    b0, b1 = ranges[axes[1]]
    return a0, b0, a1 - a0, b1 - b0


def draw_projection_panel(
    pixels,
    width: int,
    height: int,
    panel_x: int,
    panel_y: int,
    model: VoxelModel,
    view,
    frame_size: int = 64,
) -> None:
    scale = 2
    frame = frame_size * scale
    ox = panel_x + 24
    oy = panel_y + 34
    minor = (226, 222, 211, 255)
    major = (174, 166, 149, 255)
    bbox = (33, 182, 215, 255)
    border = (54, 50, 44, 255)

    fill_rect(pixels, width, height, ox, oy, frame + 1, frame + 1, (255, 253, 248, 255))
    for i in range(frame_size + 1):
        color = major if i % 8 == 0 else minor
        x = ox + i * scale
        y = oy + i * scale
        draw_line(pixels, width, height, x, oy, x, oy + frame, color)
        draw_line(pixels, width, height, ox, y, ox + frame, y, color)
    stroke_rect_thick(pixels, width, height, ox, oy, frame, frame, border, 2)

    a0, b0, bw, bh = projected_bounds(model, view, frame_size)
    stroke_rect_thick(
        pixels,
        width,
        height,
        ox + a0 * scale,
        oy + (frame_size - b0 - bh) * scale,
        bw * scale,
        bh * scale,
        bbox,
        2,
    )

    projection = visible_projection(model_to_dict(model), view, model_offset(model, frame_size))
    for (vx, vy), color_name in projection.items():
        x = ox + vx * scale
        y = oy + (frame_size - vy - 1) * scale
        fill_rect(pixels, width, height, x, y, scale, scale, COLORS[color_name])


def draw_iso_panel(pixels, width: int, height: int, panel_x: int, panel_y: int, panel_w: int, panel_h: int, model: VoxelModel) -> None:
    scale = 5.8
    polygons = list(iter_face_polygons(model, scale, 0, 0))
    xs = [x for pts, _, _ in polygons for x, _ in pts]
    ys = [y for pts, _, _ in polygons for _, y in pts]
    if xs and ys:
        fit = min(1.0, (panel_w - 44) / max(max(xs) - min(xs), 1), (panel_h - 42) / max(max(ys) - min(ys), 1))
        scale *= fit
    polygons = list(iter_face_polygons(model, scale, 0, 0))
    xs = [x for pts, _, _ in polygons for x, _ in pts]
    ys = [y for pts, _, _ in polygons for _, y in pts]
    tx = panel_x + (panel_w - (max(xs) - min(xs))) * 0.5 - min(xs) if xs else panel_x
    ty = panel_y + (panel_h - (max(ys) - min(ys))) * 0.5 - min(ys) if ys else panel_y
    for pts, rgba, factor in iter_face_polygons(model, scale, tx, ty):
        draw_polygon(pixels, width, height, pts, rgba, factor)


def render_reference_sheet(model: VoxelModel, path: Path, include_icon: bool = True, frame_size: int = 64) -> None:
    """Render one source sheet containing Icon plus Side/Front/Top views."""
    icon_w = 260 if include_icon else 0
    view_w = 178
    height = 196
    width = icon_w + view_w * len(VIEWS)
    pixels = [(244, 241, 233, 255) for _ in range(width * height)]

    if include_icon:
        draw_iso_panel(pixels, width, height, 0, 0, icon_w, height, model)
    for col, view in enumerate(VIEWS):
        draw_projection_panel(pixels, width, height, icon_w + col * view_w, 0, model, view, frame_size)

    write_png(path, width, height, pixels)


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
