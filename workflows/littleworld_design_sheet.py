#!/usr/bin/env python3
"""Generate vox assets derived from the provided isometric voxel design sheet."""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voxel_asset_pipeline.model import (
    COLORS,
    VoxelModel,
    draw_polygon,
    iter_face_polygons,
    render_preview_png,
    render_preview_svg,
    write_png,
    write_vox,
)
from voxel_asset_pipeline.render import VIEWS, fill_rect, oriented_model, put_pixel, render_review, stroke_rect, visible_projection


OUT_DIR = ROOT / "examples" / "design_sheet_trial"
CELL_RESOLUTION = 64
ASSETS = [
    "design_flower",
    "design_mushroom",
    "design_shell",
    "design_bee",
    "design_butterfly",
    "design_fish",
    "design_tree",
    "design_cloud",
    "design_crab",
]

SOURCE_REFERENCE_BY_MODEL = {
    "design_tree": "examples/design_sheet_trial/reference_generated_tree_cloud_crab.png",
    "design_cloud": "examples/design_sheet_trial/reference_generated_tree_cloud_crab.png",
    "design_crab": "examples/design_sheet_trial/reference_generated_tree_cloud_crab.png",
}


def make_design_flower() -> VoxelModel:
    m = VoxelModel("design_flower", 14, 18, 14)
    m.box(3, 11, 0, 2, 3, 11, "soil")
    m.box(3, 11, 2, 3, 3, 11, "leaf")
    m.box(4, 10, 3, 4, 4, 10, "leaf_light")

    m.box(6, 8, 4, 15, 6, 8, "stem")
    m.box(4, 6, 6, 8, 5, 8, "leaf")
    m.box(8, 11, 7, 9, 6, 9, "leaf_light")
    m.box(5, 7, 4, 6, 8, 10, "leaf")

    # The reference flower is a shallow voxel rosette: pink cubes around a
    # raised yellow center, viewed slightly from above.
    petal_blocks = [
        (6, 14, 3, 8, 16, 5),
        (3, 14, 4, 5, 16, 6),
        (9, 14, 4, 11, 16, 6),
        (3, 14, 7, 5, 16, 9),
        (9, 14, 7, 11, 16, 9),
        (6, 14, 9, 8, 16, 11),
    ]
    for x0, y0, z0, x1, y1, z1 in petal_blocks:
        m.box(x0, x1, y0, y1, z0, z1, "pink")
    m.box(5, 9, 14, 15, 5, 9, "pink")
    m.box(6, 8, 15, 17, 6, 8, "yellow")
    return m


def make_design_mushroom() -> VoxelModel:
    m = VoxelModel("design_mushroom", 12, 12, 12)
    m.box(4, 8, 0, 5, 4, 8, "cream")
    m.box(5, 7, 5, 7, 5, 7, "sand_light")
    m.ellipsoid(6.0, 7.7, 6.0, 5.0, 3.0, 5.0, "red")
    m.box(2, 10, 5, 7, 2, 10, "red")
    for x, y, z in [(4, 8, 3), (7, 10, 5), (8, 7, 8), (3, 6, 7)]:
        m.box(x, x + 2, y, y + 2, z, z + 2, "white")
    return m


def make_design_shell() -> VoxelModel:
    m = VoxelModel("design_shell", 14, 8, 10)
    center = (m.width - 1) / 2.0
    for z in range(m.depth):
        t = z / (m.depth - 1)
        row_width = 3 + int(round((m.width - 3) * math.sin(t * math.pi / 2) ** 0.8))
        x0 = int(round(center - row_width / 2))
        for x in range(x0, x0 + row_width):
            cross = 1.0 - abs(x - center) / max(row_width / 2, 1)
            height = max(1, int(round(1 + t * 4 + cross * 2)))
            for y in range(height):
                color = "cream" if y >= height - 2 else "sand_light"
                if z <= 2:
                    color = "sand"
                m.set(x, y, z, color)

    for rib in (-0.7, -0.35, 0.0, 0.35, 0.7):
        for z in range(2, m.depth):
            t = z / (m.depth - 1)
            row_width = 3 + int(round((m.width - 3) * math.sin(t * math.pi / 2) ** 0.8))
            x = int(round(center + rib * row_width * 0.42))
            for y in range(1, min(m.height, 2 + z // 2)):
                m.set(x, y, z, "sand_dark" if abs(rib) > 0.01 else "sand")
    return m


def make_design_bee() -> VoxelModel:
    m = VoxelModel("design_bee", 20, 14, 14)
    m.ellipsoid(10.6, 5.8, 7.0, 7.2, 3.3, 3.8, "yellow")
    m.ellipsoid(3.2, 5.8, 7.0, 3.0, 3.0, 3.0, "yellow")

    for x0 in (6, 10, 14):
        m.box(x0, x0 + 2, 2, 9, 3, 11, "black")
    m.box(17, 19, 4, 7, 5, 9, "black")

    for z in (5, 9):
        m.box(1, 3, 6, 8, z, z + 1, "black")
    m.ellipsoid(9.2, 10.4, 3.1, 4.2, 2.0, 2.5, "wing")
    m.ellipsoid(9.2, 10.4, 10.9, 4.2, 2.0, 2.5, "wing")

    for x in (5, 9, 13):
        m.box(x, x + 1, 0, 3, 3, 5, "black")
        m.box(x, x + 1, 0, 3, 9, 11, "black")
    m.box(0, 2, 8, 12, 4, 5, "black")
    m.box(0, 2, 8, 12, 9, 10, "black")
    m.box(1, 2, 7, 9, 5, 6, "black")
    return m


def make_design_butterfly() -> VoxelModel:
    m = VoxelModel("design_butterfly", 8, 17, 22)

    def wing_lobe(cx: float, cy: float, rx: float, ry: float) -> None:
        for z in range(int(cx - rx - 2), int(cx + rx + 3)):
            for y in range(int(cy - ry - 2), int(cy + ry + 3)):
                dx = (z + 0.5 - cx) / rx
                dy = (y + 0.5 - cy) / ry
                shape = dx * dx + dy * dy
                if shape <= 1.0:
                    color = "black" if shape >= 0.68 else "orange"
                    for x in range(2, 6):
                        m.set(x, y, z, color)

    # The reference icon reads best as a front-facing, thin butterfly. Keeping
    # the body shallow prevents the distorted source perspective from becoming
    # a bulky side-facing model.
    wing_lobe(5.8, 12.2, 5.2, 3.7)
    wing_lobe(16.2, 12.2, 5.2, 3.7)
    wing_lobe(6.2, 4.6, 4.3, 2.9)
    wing_lobe(15.8, 4.6, 4.3, 2.9)

    m.box(3, 5, 2, 15, 10, 12, "black")
    m.box(3, 5, 1, 3, 9, 13, "black")
    m.box(3, 5, 14, 16, 10, 12, "black")
    m.box(2, 4, 15, 17, 8, 10, "black")
    m.box(4, 6, 15, 17, 12, 14, "black")
    m.box(2, 6, 7, 8, 2, 10, "black")
    m.box(2, 6, 7, 8, 12, 20, "black")

    for point in ((2, 12, 5), (2, 12, 15), (2, 5, 5), (2, 5, 15)):
        m.box(point[0], point[0] + 1, point[1], point[1] + 2, point[2], point[2] + 2, "yellow")
    return m


def make_design_fish() -> VoxelModel:
    m = VoxelModel("design_fish", 20, 11, 10)
    m.ellipsoid(9.4, 5.3, 5.0, 7.0, 3.7, 3.7, "blue")
    m.ellipsoid(4.0, 5.0, 5.0, 3.0, 2.7, 2.8, "blue")
    m.box(16, 19, 4, 7, 4, 6, "blue")
    m.box(18, 20, 6, 10, 3, 5, "blue")
    m.box(18, 20, 1, 5, 5, 7, "water_dark")
    m.box(8, 12, 8, 10, 4, 6, "water_dark")
    m.box(9, 12, 1, 3, 4, 6, "water_light")

    for z in (3, 7):
        m.box(2, 4, 5, 8, z, z + 1, "white")
        m.set(2, 6, z, "black")
    for point in ((8, 8, 2), (12, 7, 6), (14, 4, 4)):
        m.set(*point, "water_light")
    return m


def make_design_tree() -> VoxelModel:
    m = VoxelModel("design_tree", 28, 34, 28)
    m.box(5, 23, 0, 2, 5, 23, "soil")
    m.box(5, 23, 2, 4, 5, 23, "leaf")
    m.box(6, 22, 4, 5, 6, 22, "leaf_light")

    m.box(12, 16, 4, 17, 12, 16, "wood")
    m.box(13, 15, 4, 17, 13, 15, "wood_dark")

    m.box(6, 22, 14, 21, 6, 22, "leaf_dark")
    m.box(3, 10, 13, 19, 9, 19, "leaf_dark")
    m.box(18, 25, 13, 19, 9, 19, "leaf_dark")
    m.box(9, 19, 13, 19, 3, 10, "leaf_dark")
    m.box(9, 19, 13, 19, 18, 25, "leaf_dark")

    m.box(7, 21, 19, 27, 7, 21, "leaf")
    m.box(4, 10, 18, 24, 10, 18, "leaf")
    m.box(18, 24, 18, 24, 10, 18, "leaf")
    m.box(10, 18, 18, 24, 4, 10, "leaf")
    m.box(10, 18, 18, 24, 18, 24, "leaf")

    m.box(9, 19, 26, 34, 9, 19, "leaf_light")
    m.box(11, 17, 24, 28, 11, 17, "leaf_light")
    return m


def make_design_cloud() -> VoxelModel:
    m = VoxelModel("design_cloud", 20, 14, 16)
    m.box(5, 15, 4, 10, 4, 12, "cloud")
    m.box(2, 8, 3, 9, 5, 11, "cloud")
    m.box(12, 18, 3, 9, 5, 11, "cloud")
    m.box(7, 13, 8, 14, 5, 11, "cloud")
    m.box(6, 14, 2, 6, 8, 15, "cloud_shadow")
    m.box(4, 9, 2, 6, 3, 8, "cloud_shadow")
    m.box(11, 16, 2, 6, 3, 8, "cloud_shadow")
    return m


def make_design_crab() -> VoxelModel:
    m = VoxelModel("design_crab", 24, 9, 18)
    m.box(7, 17, 2, 7, 5, 13, "crab")
    m.box(8, 16, 1, 3, 6, 14, "sand_light")
    m.box(8, 16, 6, 8, 5, 13, "crab_light")

    for x in (9, 14):
        m.box(x, x + 2, 6, 8, 3, 5, "black")

    leg_specs = [
        (4, 8, 2, 4),
        (3, 8, 7, 9),
        (16, 20, 2, 4),
        (16, 21, 7, 9),
    ]
    for x0, x1, z0, z1 in leg_specs:
        m.box(x0, x1, 1, 3, z0, z1, "crab")
        claw_x = x0 - 1 if x0 < 7 else x1 - 1
        m.box(claw_x, claw_x + 2, 0, 3, z0 - 1, z0 + 1, "crab_light")
    m.box(6, 8, 1, 3, 3, 6, "crab")
    m.box(16, 18, 1, 3, 3, 6, "crab")

    m.box(4, 7, 5, 7, 4, 6, "crab")
    m.box(2, 5, 5, 8, 3, 6, "crab_light")
    m.box(17, 20, 5, 7, 4, 6, "crab")
    m.box(19, 22, 5, 8, 3, 6, "crab_light")

    m.box(5, 7, 1, 3, 12, 15, "crab")
    m.box(17, 19, 1, 3, 12, 15, "crab")
    return m


BUILDERS = [
    make_design_flower,
    make_design_mushroom,
    make_design_shell,
    make_design_bee,
    make_design_butterfly,
    make_design_fish,
    make_design_tree,
    make_design_cloud,
    make_design_crab,
]


def model_to_dict(model: VoxelModel) -> dict:
    return {
        "size": [model.width, model.height, model.depth],
        "voxels": model.voxels,
    }


def axis_index(axis: str) -> int:
    return {"x": 0, "y": 1, "z": 2}[axis]


def model_offset(model: VoxelModel) -> tuple[int, int, int]:
    return (
        (CELL_RESOLUTION - model.width) // 2,
        0,
        (CELL_RESOLUTION - model.depth) // 2,
    )


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


def projected_bounds(model: VoxelModel, view) -> tuple[int, int, int, int]:
    _, axes, _, _ = view
    offset = model_offset(model)
    ranges = {
        "x": (offset[0], offset[0] + model.width),
        "y": (0, model.height),
        "z": (offset[2], offset[2] + model.depth),
    }
    a0, a1 = ranges[axes[0]]
    b0, b1 = ranges[axes[1]]
    return a0, b0, a1 - a0, b1 - b0


def draw_projection_panel(pixels, width: int, height: int, panel_x: int, panel_y: int, model: VoxelModel, view) -> None:
    scale = 2
    frame = CELL_RESOLUTION * scale
    ox = panel_x + 24
    oy = panel_y + 34
    minor = (226, 222, 211, 255)
    major = (174, 166, 149, 255)
    bbox = (33, 182, 215, 255)
    border = (54, 50, 44, 255)

    fill_rect(pixels, width, height, ox, oy, frame + 1, frame + 1, (255, 253, 248, 255))
    for i in range(CELL_RESOLUTION + 1):
        color = major if i % 8 == 0 else minor
        x = ox + i * scale
        y = oy + i * scale
        draw_line(pixels, width, height, x, oy, x, oy + frame, color)
        draw_line(pixels, width, height, ox, y, ox + frame, y, color)
    stroke_rect_thick(pixels, width, height, ox, oy, frame, frame, border, 2)

    a0, b0, bw, bh = projected_bounds(model, view)
    stroke_rect_thick(
        pixels,
        width,
        height,
        ox + a0 * scale,
        oy + (CELL_RESOLUTION - b0 - bh) * scale,
        bw * scale,
        bh * scale,
        bbox,
        2,
    )

    projection = visible_projection(model_to_dict(model), view, model_offset(model))
    for (vx, vy), color_name in projection.items():
        x = ox + vx * scale
        y = oy + (CELL_RESOLUTION - vy - 1) * scale
        fill_rect(pixels, width, height, x, y, scale, scale, COLORS[color_name])


def draw_iso_panel(
    pixels,
    width: int,
    height: int,
    panel_x: int,
    panel_y: int,
    model: VoxelModel,
    orientation: str = "icon",
) -> None:
    panel_w = 260
    panel_h = 196
    view_model = oriented_model(model, orientation)
    scale = 5.2
    polygons = list(iter_face_polygons(view_model, scale, 0, 0))
    xs = [x for pts, _, _ in polygons for x, _ in pts]
    ys = [y for pts, _, _ in polygons for _, y in pts]
    if xs and ys:
        bbox_w = max(xs) - min(xs)
        bbox_h = max(ys) - min(ys)
        fit = min(1.0, 224 / max(bbox_w, 1), 164 / max(bbox_h, 1))
        scale *= fit
    polygons = list(iter_face_polygons(view_model, scale, 0, 0))
    xs = [x for pts, _, _ in polygons for x, _ in pts]
    ys = [y for pts, _, _ in polygons for _, y in pts]
    tx = panel_x + (panel_w - (max(xs) - min(xs))) * 0.5 - min(xs) if xs else panel_x
    ty = panel_y + (panel_h - (max(ys) - min(ys))) * 0.5 - min(ys) if ys else panel_y
    for pts, rgba, factor in iter_face_polygons(view_model, scale, tx, ty):
        draw_polygon(pixels, width, height, pts, rgba, factor)


def render_pipeline_reference(models: list[VoxelModel], path: Path) -> None:
    row_h = 196
    iso_w = 260
    panel_w = 178
    width = iso_w * 2 + panel_w * len(VIEWS)
    height = row_h * len(models)
    pixels = [(244, 241, 233, 255) for _ in range(width * height)]

    for row, model in enumerate(models):
        y = row * row_h
        draw_iso_panel(pixels, width, height, 0, y, model)
        draw_iso_panel(pixels, width, height, iso_w, y, model, "front3q")
        for col, view in enumerate(VIEWS):
            draw_projection_panel(pixels, width, height, iso_w * 2 + col * panel_w, y, model, view)

    write_png(path, width, height, pixels)
    print(f"Wrote {path}")


def reference_view_items(model_name: str) -> list[dict]:
    base = "examples/design_sheet_trial/reference_views"
    views = [
        {"id": "iso", "label": "Icon", "path": f"{base}/{model_name}_iso.png"},
        {"id": "front3q", "label": "Front 3/4", "path": f"{base}/{model_name}_front3q.png"},
        {"id": "side", "label": "Side", "path": f"{base}/{model_name}_side.png"},
        {"id": "front", "label": "Front", "path": f"{base}/{model_name}_front.png"},
        {"id": "top", "label": "Top", "path": f"{base}/{model_name}_top.png"},
    ]
    source = SOURCE_REFERENCE_BY_MODEL.get(model_name)
    if source:
        views.insert(1, {"id": "source", "label": "Source", "path": source})
    return views


def render_individual_reference_views(models: list[VoxelModel]) -> None:
    ref_dir = OUT_DIR / "reference_views"
    ref_dir.mkdir(parents=True, exist_ok=True)
    for model in models:
        iso_w, row_h = 260, 196
        iso_pixels = [(244, 241, 233, 255) for _ in range(iso_w * row_h)]
        draw_iso_panel(iso_pixels, iso_w, row_h, 0, 0, model)
        write_png(ref_dir / f"{model.name}_iso.png", iso_w, row_h, iso_pixels)

        front_pixels = [(244, 241, 233, 255) for _ in range(iso_w * row_h)]
        draw_iso_panel(front_pixels, iso_w, row_h, 0, 0, model, "front3q")
        write_png(ref_dir / f"{model.name}_front3q.png", iso_w, row_h, front_pixels)

        panel_w = 178
        for view in VIEWS:
            pixels = [(244, 241, 233, 255) for _ in range(panel_w * row_h)]
            draw_projection_panel(pixels, panel_w, row_h, 0, 0, model, view)
            write_png(ref_dir / f"{model.name}_{view[0]}.png", panel_w, row_h, pixels)


def generate() -> list[dict]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    models = [build() for build in BUILDERS]
    manifest: list[dict] = []

    for model in models:
        path = OUT_DIR / f"{model.name}.vox"
        write_vox(path, model)
        scale_tier = "tiny" if model.name in {"design_flower", "design_mushroom", "design_shell", "design_cloud"} else "small"
        reference_views = reference_view_items(model.name)
        manifest.append(
            {
                "name": model.name,
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "source_image": reference_views[0]["path"],
                "reference_views": reference_views,
                "cell_resolution": CELL_RESOLUTION,
                "game_cells": [1, 1, 1],
                "scale_tier": scale_tier,
                "review_status": "pending_review",
                "size": [model.width, model.height, model.depth],
                "voxel_count": len(model.voxels),
                "observed": "Derived from the provided isometric voxel design sheet, then converted to side/front/top projections from the actual voxel array.",
            }
        )

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    render_preview_png(models, OUT_DIR / "preview.png")
    render_preview_svg(models, OUT_DIR / "preview.svg")
    render_review(OUT_DIR / "projection_review.png", OUT_DIR, ASSETS, [CELL_RESOLUTION, CELL_RESOLUTION, CELL_RESOLUTION])
    render_pipeline_reference(models, OUT_DIR / "reference_design_pipeline.png")
    render_individual_reference_views(models)
    return manifest


def main() -> None:
    manifest = generate()
    print(f"Generated {len(manifest)} design-sheet .vox files in {OUT_DIR.relative_to(ROOT)}")
    for item in manifest:
        print(f"{item['name']}: size={item['size']} voxels={item['voxel_count']}")

    print("Running design-sheet checks...")
    from workflows.check_design_sheet import main as check_main

    check_main()


if __name__ == "__main__":
    main()


