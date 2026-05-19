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
SOURCE_REFERENCE = "examples/horse_trial/reference_horse_icon_three_view_clean.png"


def make_voxel_horse() -> VoxelModel:
    """Build a one-cell chestnut horse with long legs, raised neck, mane, and tail."""
    m = VoxelModel("voxel_horse", 46, 34, 16)

    # Long rounded torso, centered inside the 64-cell frame.
    m.ellipsoid(20.0, 15.5, 8.0, 13.5, 6.4, 5.6, "wood")
    m.box(9, 31, 10, 18, 4, 12, "wood")
    m.box(11, 29, 18, 22, 5, 11, "sand_dark")
    m.box(13, 27, 20, 23, 6, 10, "sand")
    m.box(11, 30, 9, 12, 5, 11, "sand_dark")

    # Four long legs with slightly larger dark hooves.
    for x0 in (12, 27):
        for z0 in (4, 10):
            m.box(x0, x0 + 3, 0, 13, z0, z0 + 3, "wood")
            m.box(x0 - 1, x0 + 4, 0, 2, z0 - 1, z0 + 4, "black")
            m.box(x0, x0 + 3, 11, 15, z0, z0 + 3, "sand_dark")

    # Chest, sloped neck, and head face toward +X.
    m.box(28, 33, 16, 24, 5, 11, "wood")
    m.box(31, 36, 19, 28, 5, 11, "wood")
    m.box(35, 42, 20, 28, 4, 12, "wood")
    m.box(41, 46, 18, 24, 5, 11, "sand_dark")
    m.box(43, 46, 18, 22, 6, 10, "cream")

    # Mane, ears, eyes, and muzzle details.
    m.box(29, 37, 23, 30, 7, 9, "wood_dark")
    m.box(33, 38, 27, 31, 7, 9, "wood_dark")
    m.box(36, 38, 27, 33, 5, 7, "wood_dark")
    m.box(36, 38, 27, 33, 9, 11, "wood_dark")
    m.set(40, 24, 4, "black")
    m.set(40, 24, 11, "black")
    m.set(45, 20, 6, "black")
    m.set(45, 20, 9, "black")

    # Rear tail is connected to the torso and falls behind the back legs.
    m.box(3, 9, 18, 21, 7, 10, "wood_dark")
    m.box(1, 5, 13, 19, 7, 10, "wood_dark")
    m.box(0, 3, 10, 15, 7, 10, "wood_dark")

    return m


BUILDERS = [make_voxel_horse]


def reference_view_items(model_name: str) -> list[dict]:
    base = "examples/horse_trial/reference_views"
    return [
        {"id": "iso", "label": "Icon", "path": f"{base}/{model_name}_iso.png"},
        {"id": "source", "label": "Source", "path": SOURCE_REFERENCE},
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
        "order": 85,
    }
    (OUT_DIR / "dataset.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")


def generate() -> list[dict]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    models = [build() for build in BUILDERS]
    manifest: list[dict] = []

    render_reference_sheet(models[0], OUT_DIR / "reference_horse_icon_three_view_clean.png", include_icon=True)
    render_reference_sheet(models[0], OUT_DIR / "reference_horse_three_view_clean.png", include_icon=False)

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
                "scale_tier": "medium",
                "review_status": "pending_review",
                "size": [model.width, model.height, model.depth],
                "voxel_count": len(model.voxels),
                "observed": "Procedural chestnut voxel horse with long legs, raised head, dark mane, cream muzzle, four hooves, and connected rear tail.",
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
