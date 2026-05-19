#!/usr/bin/env python3
"""Generate a single voxel horse asset with review images."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voxel_asset_pipeline.model import VoxelModel, render_preview_png, render_preview_svg, write_png, write_vox
from voxel_asset_pipeline.render import VIEWS, draw_iso_panel, draw_projection_panel, render_reference_sheet, render_review
from workflows.littleworld_design_sheet import render_pipeline_reference


OUT_DIR = ROOT / "examples" / "horse_trial"
CELL_RESOLUTION = 64
ASSETS = ["voxel_horse"]
STYLE_REFERENCE = "examples/horse_trial/voxel_horse_style_reference.png"
SOURCE_REFERENCE = "examples/horse_trial/voxel_horse_source_clean2.png"


def make_voxel_horse() -> VoxelModel:
    m = VoxelModel("voxel_horse", 46, 34, 16)

    # Chestnut body with enough depth to read in front and top projections.
    m.box(14, 37, 12, 24, 4, 12, "orange")
    m.box(16, 36, 14, 25, 3, 13, "orange")
    m.box(17, 34, 23, 26, 5, 11, "soil_light")
    m.box(15, 37, 10, 14, 5, 11, "soil")

    # Four sturdy legs; side projection collapses them into the expected two-leg silhouette.
    for x0 in (16, 32):
        for z0 in (4, 10):
            m.box(x0, x0 + 4, 2, 14, z0, z0 + 3, "orange")
            m.box(x0, x0 + 4, 0, 3, z0, z0 + 3, "black")
            m.box(x0 + 1, x0 + 3, 8, 13, z0, z0 + 3, "soil")

    # Neck, head, muzzle, and ears. Low X is the front/head direction.
    m.box(9, 18, 19, 28, 5, 11, "orange")
    m.box(10, 17, 25, 31, 6, 10, "orange")
    m.box(2, 11, 18, 27, 5, 11, "orange")
    m.box(0, 5, 16, 22, 6, 10, "orange")
    m.box(5, 7, 27, 34, 5, 7, "orange")
    m.box(8, 10, 28, 34, 9, 11, "orange")

    # Dark mane follows the top and back of the neck, matching the approved source sheet.
    m.box(8, 19, 26, 31, 9, 12, "wood_dark")
    m.box(10, 20, 24, 29, 7, 10, "wood_dark")
    m.box(6, 12, 25, 29, 6, 10, "wood_dark")

    # Tail is connected through the rump and drops downward at the back.
    m.box(36, 42, 18, 24, 6, 10, "wood_dark")
    m.box(40, 46, 10, 22, 5, 11, "wood_dark")
    m.box(42, 45, 8, 13, 6, 10, "wood_dark")

    # White face blaze, eyes, and black muzzle/hooves.
    m.box(0, 3, 19, 26, 7, 9, "white")
    m.box(1, 5, 17, 21, 7, 9, "white")
    m.box(0, 2, 16, 19, 6, 10, "black")
    m.box(1, 3, 23, 25, 4, 5, "black")
    m.box(1, 3, 23, 25, 11, 12, "black")

    return m


BUILDERS = [make_voxel_horse]


def reference_view_items(model_name: str) -> list[dict]:
    base = "examples/horse_trial/reference_views"
    return [
        {"id": "style", "label": "Style", "path": STYLE_REFERENCE},
        {"id": "source", "label": "Source", "path": SOURCE_REFERENCE},
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
            draw_projection_panel(pixels, panel_w, row_h, 0, 0, model, view)
            write_png(ref_dir / f"{model.name}_{view[0]}.png", panel_w, row_h, pixels)


def write_dataset_metadata() -> None:
    metadata = {
        "id": "horse-trial",
        "name": "Voxel Horse",
        "cellResolution": CELL_RESOLUTION,
        "order": 40,
    }
    (OUT_DIR / "dataset.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")


def generate() -> list[dict]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    models = [build() for build in BUILDERS]
    manifest: list[dict] = []
    render_reference_sheet(models[0], OUT_DIR / "reference_horse_model_sheet.png", include_icon=True)

    for model in models:
        path = OUT_DIR / f"{model.name}.vox"
        write_vox(path, model)
        reference_views = reference_view_items(model.name)
        manifest.append(
            {
                "name": model.name,
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "source_image": SOURCE_REFERENCE,
                "reference_views": reference_views,
                "cell_resolution": CELL_RESOLUTION,
                "game_cells": [1, 1, 1],
                "scale_tier": "small",
                "review_status": "pending_review",
                "size": [model.width, model.height, model.depth],
                "voxel_count": len(model.voxels),
                "observed": "Voxel horse built from approved source sheet: chestnut body, dark mane and tail, black hooves, and white face blaze.",
            }
        )

    write_dataset_metadata()
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    render_preview_png(models, OUT_DIR / "preview.png")
    render_preview_svg(models, OUT_DIR / "preview.svg")
    render_review(OUT_DIR / "projection_review.png", OUT_DIR, ASSETS, [CELL_RESOLUTION, CELL_RESOLUTION, CELL_RESOLUTION])
    render_pipeline_reference(models, OUT_DIR / "reference_horse_pipeline.png")
    render_individual_reference_views(models)
    return manifest


def main() -> None:
    manifest = generate()
    print(f"Generated {len(manifest)} horse-trial .vox files in {OUT_DIR.relative_to(ROOT)}")
    for item in manifest:
        print(f"{item['name']}: size={item['size']} voxels={item['voxel_count']}")

    print("Running horse-trial checks...")
    from workflows.check_horse_trial import main as check_main

    check_main()


if __name__ == "__main__":
    main()
