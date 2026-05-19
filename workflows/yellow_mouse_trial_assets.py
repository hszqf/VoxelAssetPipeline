#!/usr/bin/env python3
"""Generate voxel_yellow_fantasy_mouse from the approved cleaned source sheet."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voxel_asset_pipeline.model import VoxelModel, render_preview_png, render_preview_svg, write_png, write_vox
from voxel_asset_pipeline.checks import components
from voxel_asset_pipeline.render import VIEWS, draw_iso_panel, draw_projection_panel, render_review
from voxel_asset_pipeline.source_sheet_check import Frame, detect_grid_frames, read_png_rgba
from voxel_asset_pipeline.source_sheet_clean import bg_or_grid_pixel, bucket_rgb


OUT_DIR = ROOT / "examples" / "yellow_mouse_trial"
CELL_RESOLUTION = 64
ASSETS = ["voxel_yellow_fantasy_mouse"]
STYLE_REFERENCE = "examples/yellow_mouse_trial/voxel_yellow_fantasy_mouse_style_reference.png"
SOURCE_REFERENCE = "examples/yellow_mouse_trial/voxel_yellow_fantasy_mouse_source_attempt3_clean64.png"
GRID_SIZE = 64
TARGET_LENGTH = 22
TARGET_HEIGHT = 24
TARGET_DEPTH = 20


@dataclass(frozen=True)
class SourceView:
    cells: dict[tuple[int, int], tuple[int, int, int]]
    bbox: tuple[int, int, int, int]


def source_color_to_palette(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    if max(rgb) <= 72:
        return "black"
    if r >= 228 and g >= 210 and b >= 145:
        return "cream"
    if r >= 178 and g >= 120 and b <= 86:
        return "yellow_light" if g >= 170 else "yellow"
    if r >= 140 and g >= 86 and b <= 70:
        return "yellow_dark"
    if r >= 80 and g <= 105 and b <= 70:
        return "mouse_brown" if r >= 105 else "mouse_brown_dark"
    if g >= 82 and b >= 82:
        return "mouse_teal"
    return "yellow"


def sample_cell(
    pixels: list[tuple[int, int, int, int]],
    image_w: int,
    frame: Frame,
    gx: int,
    gy: int,
) -> tuple[int, int, int] | None:
    cell = (frame.w - 1) / GRID_SIZE
    x0 = int(round(frame.x + gx * cell + cell * 0.25))
    x1 = int(round(frame.x + (gx + 1) * cell - cell * 0.25))
    y0 = int(round(frame.y + (GRID_SIZE - 1 - gy) * cell + cell * 0.25))
    y1 = int(round(frame.y + (GRID_SIZE - gy) * cell - cell * 0.25))
    colors: Counter[tuple[int, int, int]] = Counter()
    for y in range(y0, y1):
        for x in range(x0, x1):
            rgba = pixels[y * image_w + x]
            if not bg_or_grid_pixel(rgba):
                colors[bucket_rgb(rgba, 8)[:3]] += 1
    return colors.most_common(1)[0][0] if colors else None


def read_source_views() -> dict[str, SourceView]:
    image = ROOT / SOURCE_REFERENCE
    image_w, image_h, pixels = read_png_rgba(image)
    frames = detect_grid_frames(image_w, image_h, pixels)
    if len(frames) != 3:
        raise ValueError(f"Expected 3 source frames in {image}, found {len(frames)}")

    result: dict[str, SourceView] = {}
    for name, frame in zip(("side", "front", "top"), frames):
        cells: dict[tuple[int, int], tuple[int, int, int]] = {}
        for gy in range(GRID_SIZE):
            for gx in range(GRID_SIZE):
                color = sample_cell(pixels, image_w, frame, gx, gy)
                if color is not None:
                    cells[(gx, gy)] = color
        if not cells:
            raise ValueError(f"No occupied source cells found for {name}")
        xs = [x for x, _ in cells]
        ys = [y for _, y in cells]
        result[name] = SourceView(cells, (min(xs), min(ys), max(xs) + 1, max(ys) + 1))
    return result


def source_origins(views: dict[str, SourceView]) -> tuple[int, int, int]:
    side = views["side"].bbox
    front = views["front"].bbox
    top = views["top"].bbox
    origin_x = min(side[0], top[0])
    origin_y = min(side[1], front[1])
    origin_z = min(front[0], top[1])
    return origin_x, origin_y, origin_z


def make_voxel_yellow_fantasy_mouse() -> VoxelModel:
    """Build the asset by intersecting the approved Side/Front/Top masks."""
    views = read_source_views()
    side = views["side"]
    front = views["front"]
    top = views["top"]
    origin_x, origin_y, origin_z = source_origins(views)

    model = VoxelModel("voxel_yellow_fantasy_mouse", TARGET_LENGTH, TARGET_HEIGHT, TARGET_DEPTH)
    for x in range(model.width):
        for y in range(model.height):
            if (origin_x + x, origin_y + y) not in side.cells:
                continue
            for z in range(model.depth):
                if (origin_z + z, origin_y + y) in front.cells and (origin_x + x, origin_z + z) in top.cells:
                    model.set(x, y, z, "yellow")

    apply_projection_surface_colors(model, views, (origin_x, origin_y, origin_z))
    connect_detached_components(model)
    return model


def connect_detached_components(model: VoxelModel) -> None:
    """Add minimal same-palette supports for tiny source-derived overhangs."""
    comps = sorted(components(model.voxels.keys()), key=len, reverse=True)
    if len(comps) <= 1:
        return

    main = set(comps[0])
    for comp in comps[1:]:
        start, end = min(
            ((a, b) for a in comp for b in main),
            key=lambda pair: sum(abs(pair[0][i] - pair[1][i]) for i in range(3)),
        )
        x, y, z = start
        tx, ty, tz = end
        while x != tx:
            x += 1 if tx > x else -1
            model.set(x, y, z, "yellow")
            main.add((x, y, z))
        while y != ty:
            y += 1 if ty > y else -1
            model.set(x, y, z, "yellow")
            main.add((x, y, z))
        while z != tz:
            z += 1 if tz > z else -1
            model.set(x, y, z, "yellow")
            main.add((x, y, z))
        main.update(comp)


def apply_projection_surface_colors(
    model: VoxelModel,
    views: dict[str, SourceView],
    origins: tuple[int, int, int],
) -> None:
    origin_x, origin_y, origin_z = origins
    side = views["side"]
    front = views["front"]
    top = views["top"]

    for (gx, gy), rgb in side.cells.items():
        x = gx - origin_x
        y = gy - origin_y
        if not (0 <= x < model.width and 0 <= y < model.height):
            continue
        zs = [z for z in range(model.depth) if (x, y, z) in model.voxels]
        if zs:
            model.set(x, y, max(zs), source_color_to_palette(rgb))

    for (gx, gy), rgb in top.cells.items():
        x = gx - origin_x
        z = gy - origin_z
        if not (0 <= x < model.width and 0 <= z < model.depth):
            continue
        ys = [y for y in range(model.height) if (x, y, z) in model.voxels]
        if ys:
            model.set(x, max(ys), z, source_color_to_palette(rgb))

    for (gx, gy), rgb in front.cells.items():
        z = gx - origin_z
        y = gy - origin_y
        if not (0 <= z < model.depth and 0 <= y < model.height):
            continue
        xs = [x for x in range(model.width) if (x, y, z) in model.voxels]
        if xs:
            model.set(min(xs), y, z, source_color_to_palette(rgb))


BUILDERS = [make_voxel_yellow_fantasy_mouse]


def reference_view_items(model_name: str) -> list[dict]:
    base = "examples/yellow_mouse_trial/reference_views"
    return [
        {"id": "source", "label": "Source", "path": SOURCE_REFERENCE},
        {"id": "style", "label": "Style", "path": STYLE_REFERENCE},
        {"id": "iso", "label": "Icon", "path": f"{base}/{model_name}_iso.png"},
        {"id": "front3q", "label": "Front 3/4", "path": f"{base}/{model_name}_front3q.png"},
        {"id": "side", "label": "Side", "path": f"{base}/{model_name}_side.png"},
        {"id": "front", "label": "Front", "path": f"{base}/{model_name}_front.png"},
        {"id": "top", "label": "Top", "path": f"{base}/{model_name}_top.png"},
    ]


def render_individual_reference_views(models: list[VoxelModel]) -> None:
    ref_dir = OUT_DIR / "reference_views"
    ref_dir.mkdir(parents=True, exist_ok=True)
    for model in models:
        iso_w, row_h = 260, 196
        iso_pixels = [(244, 241, 233, 255) for _ in range(iso_w * row_h)]
        draw_iso_panel(iso_pixels, iso_w, row_h, 0, 0, iso_w, row_h, model)
        write_png(ref_dir / f"{model.name}_iso.png", iso_w, row_h, iso_pixels)

        front_pixels = [(244, 241, 233, 255) for _ in range(iso_w * row_h)]
        draw_iso_panel(front_pixels, iso_w, row_h, 0, 0, iso_w, row_h, model, "front3q")
        write_png(ref_dir / f"{model.name}_front3q.png", iso_w, row_h, front_pixels)

        panel_w = 178
        for view in VIEWS:
            pixels = [(244, 241, 233, 255) for _ in range(panel_w * row_h)]
            draw_projection_panel(pixels, panel_w, row_h, 0, 0, model, view, CELL_RESOLUTION)
            write_png(ref_dir / f"{model.name}_{view[0]}.png", panel_w, row_h, pixels)


def render_pipeline_reference(models: list[VoxelModel], path: Path) -> None:
    row_h = 196
    iso_w = 260
    panel_w = 178
    width = iso_w * 2 + panel_w * len(VIEWS)
    height = row_h * len(models)
    pixels = [(244, 241, 233, 255) for _ in range(width * height)]

    for row, model in enumerate(models):
        y = row * row_h
        draw_iso_panel(pixels, width, height, 0, y, iso_w, row_h, model)
        draw_iso_panel(pixels, width, height, iso_w, y, iso_w, row_h, model, "front3q")
        for col, view in enumerate(VIEWS):
            draw_projection_panel(pixels, width, height, iso_w * 2 + col * panel_w, y, model, view, CELL_RESOLUTION)
    write_png(path, width, height, pixels)


def write_dataset_metadata() -> None:
    metadata = {
        "id": "yellow-mouse-trial",
        "name": "Voxel Yellow Fantasy Mouse",
        "cellResolution": CELL_RESOLUTION,
        "order": 95,
    }
    (OUT_DIR / "dataset.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")


def generate() -> list[dict]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    models = [build() for build in BUILDERS]
    manifest: list[dict] = []

    for model in models:
        path = OUT_DIR / f"{model.name}.vox"
        write_vox(path, model)
        manifest.append(
            {
                "name": model.name,
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "source_image": SOURCE_REFERENCE,
                "reference_views": reference_view_items(model.name),
                "cell_resolution": CELL_RESOLUTION,
                "game_cells": [1, 1, 1],
                "scale_tier": "small",
                "review_status": "pending_review",
                "size": [model.width, model.height, model.depth],
                "voxel_count": len(model.voxels),
                "observed": "Generated from the approved cleaned Side/Front/Top yellow fantasy mouse source by visual-hull intersection, with surface colors sampled from the source cells.",
            }
        )

    write_dataset_metadata()
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    render_preview_png(models, OUT_DIR / "preview.png")
    render_preview_svg(models, OUT_DIR / "preview.svg")
    render_review(OUT_DIR / "projection_review.png", OUT_DIR, ASSETS, [CELL_RESOLUTION, CELL_RESOLUTION, CELL_RESOLUTION])
    render_pipeline_reference(models, OUT_DIR / "reference_yellow_mouse_pipeline.png")
    render_individual_reference_views(models)
    return manifest


def main() -> None:
    manifest = generate()
    print(f"Generated {len(manifest)} yellow-mouse-trial .vox files in {OUT_DIR.relative_to(ROOT)}")
    for item in manifest:
        print(f"{item['name']}: size={item['size']} voxels={item['voxel_count']}")

    print("Running yellow-mouse-trial checks...")
    from workflows.check_yellow_mouse_trial import main as check_main

    check_main()


if __name__ == "__main__":
    main()
