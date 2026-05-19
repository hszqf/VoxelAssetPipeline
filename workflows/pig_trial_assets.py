#!/usr/bin/env python3
"""Generate a voxel pig from the approved 32-grid Side/Front/Top source sheet."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voxel_asset_pipeline.model import VoxelModel, render_preview_png, render_preview_svg, write_png, write_vox
from voxel_asset_pipeline.render import VIEWS, draw_iso_panel, draw_projection_panel, render_reference_sheet, render_review
from voxel_asset_pipeline.source_sheet_check import Frame, detect_grid_frames, read_png_rgba
from voxel_asset_pipeline.source_sheet_clean import bg_or_grid_pixel, bucket_rgb


OUT_DIR = ROOT / "examples" / "pig_trial"
CELL_RESOLUTION = 32
ASSETS = ["voxel_pig"]
STYLE_REFERENCE = "examples/pig_trial/voxel_pig_style_reference.png"
SOURCE_REFERENCE = "examples/pig_trial/voxel_pig_source_32_attempt2_linecut_mode_cli.png"
GRID_SIZE = 32


@dataclass(frozen=True)
class SourceView:
    cells: dict[tuple[int, int], tuple[int, int, int]]
    width: int
    height: int
    bbox: tuple[int, int, int, int]


def source_color_to_palette(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    if max(rgb) <= 72:
        return "pig_black"
    if r <= 205 and g <= 72:
        return "pig_deep"
    if r <= 236:
        return "pig_dark"
    if r <= 248 and g <= 136:
        return "pig_shadow"
    if b >= 172:
        return "pig_body_light"
    return "pig_body"


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


def read_approved_source_views() -> dict[str, SourceView]:
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
        x0, y0 = min(xs), min(ys)
        x1, y1 = max(xs), max(ys)
        local = {(x - x0, y - y0): color for (x, y), color in cells.items()}
        result[name] = SourceView(local, x1 - x0 + 1, y1 - y0 + 1, (x0, y0, x1, y1))
    return result


def top_cell_for_x(top: SourceView, x: int, z: int) -> tuple[int, int] | None:
    if not (0 <= z < top.height):
        return None
    if 0 <= x < top.width:
        return (x, z)
    if x == top.width:
        return (top.width - 1, z)
    return None


def make_voxel_pig() -> VoxelModel:
    """Build voxel_pig by intersecting the approved Side/Front/Top source masks."""
    views = read_approved_source_views()
    side = views["side"]
    front = views["front"]
    top = views["top"]

    width = side.width
    height = max(side.height, front.height)
    depth = front.width
    model = VoxelModel("voxel_pig", width, height, depth)

    for x in range(width):
        for y in range(height):
            if (x, y) not in side.cells:
                continue
            for z in range(depth):
                top_key = top_cell_for_x(top, x, z)
                if (z, y) in front.cells and top_key is not None and top_key in top.cells:
                    model.set(x, y, z, "pig_body")

    apply_projection_surface_colors(model, views)
    return model


def apply_projection_surface_colors(model: VoxelModel, views: dict[str, SourceView]) -> None:
    side = views["side"]
    front = views["front"]
    top = views["top"]

    for (x, y), rgb in side.cells.items():
        zs = [z for z in range(model.depth) if (x, y, z) in model.voxels]
        if zs:
            model.set(x, y, max(zs), source_color_to_palette(rgb))

    for (x, z), rgb in top.cells.items():
        for mx in (x, x + 1 if x == top.width - 1 and model.width == top.width + 1 else x):
            ys = [y for y in range(model.height) if (mx, y, z) in model.voxels]
            if ys:
                model.set(mx, max(ys), z, source_color_to_palette(rgb))

    for (z, y), rgb in front.cells.items():
        xs = [x for x in range(model.width) if (x, y, z) in model.voxels]
        if xs:
            model.set(min(xs), y, z, source_color_to_palette(rgb))


BUILDERS = [make_voxel_pig]


def reference_view_items(model_name: str) -> list[dict]:
    base = "examples/pig_trial/reference_views"
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


def render_pipeline_reference_32(models: list[VoxelModel], path: Path) -> None:
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
        "id": "pig-trial",
        "name": "Voxel Pig",
        "cellResolution": CELL_RESOLUTION,
        "order": 90,
    }
    (OUT_DIR / "dataset.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")


def generate() -> list[dict]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    models = [build() for build in BUILDERS]
    manifest: list[dict] = []

    render_reference_sheet(models[0], OUT_DIR / "reference_pig_icon_three_view_clean.png", include_icon=True, frame_size=CELL_RESOLUTION)
    render_reference_sheet(models[0], OUT_DIR / "reference_pig_three_view_clean.png", include_icon=False, frame_size=CELL_RESOLUTION)

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
                "observed": "Generated from the approved 32-grid pig Side/Front/Top source by visual-hull intersection, with visible surface colors sampled from the source cells.",
            }
        )

    write_dataset_metadata()
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    render_preview_png(models, OUT_DIR / "preview.png")
    render_preview_svg(models, OUT_DIR / "preview.svg")
    render_review(OUT_DIR / "projection_review.png", OUT_DIR, ASSETS, [CELL_RESOLUTION, CELL_RESOLUTION, CELL_RESOLUTION])
    render_pipeline_reference_32(models, OUT_DIR / "reference_pig_pipeline.png")
    render_individual_reference_views(models)
    return manifest


def main() -> None:
    manifest = generate()
    print(f"Generated {len(manifest)} pig-trial .vox files in {OUT_DIR.relative_to(ROOT)}")
    for item in manifest:
        print(f"{item['name']}: size={item['size']} voxels={item['voxel_count']}")

    print("Running pig-trial checks...")
    from workflows.check_pig_trial import main as check_main

    check_main()


if __name__ == "__main__":
    main()
