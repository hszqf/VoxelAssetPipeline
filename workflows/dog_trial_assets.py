#!/usr/bin/env python3
"""Generate the selected golden dog voxel asset."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voxel_asset_pipeline.model import VoxelModel, render_preview_png, render_preview_svg, write_png, write_vox
from voxel_asset_pipeline.render import VIEWS, render_review
from workflows.littleworld_design_sheet import draw_iso_panel, draw_projection_panel, render_pipeline_reference


OUT_DIR = ROOT / "examples" / "dog_trial"
CELL_RESOLUTION = 64
ASSETS = ["dog_golden"]
SOURCE_REFERENCE = "examples/dog_trial/reference_dog_pack.png"


def make_dog_golden() -> VoxelModel:
    m = VoxelModel("dog_golden", 24, 16, 14)

    # Selected candidate 6: a compact golden puppy with a short straight tail,
    # floppy ears, cream muzzle, and a small blue collar.
    m.box(5, 16, 4, 10, 4, 11, "sand")
    m.box(6, 15, 4, 6, 5, 10, "cream")
    m.box(7, 12, 8, 11, 3, 6, "sand_light")

    m.box(15, 20, 8, 14, 4, 10, "sand")
    m.box(19, 23, 7, 11, 5, 9, "cream")
    m.box(15, 17, 6, 12, 2, 4, "wood_dark")
    m.box(15, 17, 6, 12, 10, 12, "wood_dark")
    m.set(20, 11, 5, "black")
    m.set(20, 11, 8, "black")
    m.box(21, 23, 8, 10, 6, 8, "black")

    m.box(14, 15, 8, 11, 4, 10, "blue")

    for x0, z0 in [(6, 4), (12, 4), (6, 9), (12, 9)]:
        m.box(x0, x0 + 2, 0, 5, z0, z0 + 2, "sand")
        m.box(x0 - 1, x0 + 2, 0, 1, z0, z0 + 3, "wood_dark")

    m.box(2, 6, 8, 10, 6, 8, "sand")
    m.box(1, 3, 7, 9, 6, 8, "sand")
    return m


BUILDERS = [make_dog_golden]


def reference_view_items(model_name: str) -> list[dict]:
    base = "examples/dog_trial/reference_views"
    return [
        {"id": "iso", "label": "Icon", "path": f"{base}/{model_name}_iso.png"},
        {"id": "source", "label": "Source", "path": SOURCE_REFERENCE},
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
        draw_iso_panel(iso_pixels, iso_w, row_h, 0, 0, model)
        write_png(ref_dir / f"{model.name}_iso.png", iso_w, row_h, iso_pixels)

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
        reference_views = reference_view_items(model.name)
        manifest.append(
            {
                "name": model.name,
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "source_image": SOURCE_REFERENCE,
                "reference_views": reference_views,
                "cell_resolution": CELL_RESOLUTION,
                "game_cells": [1, 1, 1],
                "scale_tier": "tiny",
                "review_status": "pending_review",
                "size": [model.width, model.height, model.depth],
                "voxel_count": len(model.voxels),
                "observed": "Selected from dog reference pack candidate 6: golden puppy with floppy ears and short tail.",
            }
        )

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    render_preview_png(models, OUT_DIR / "preview.png")
    render_preview_svg(models, OUT_DIR / "preview.svg")
    render_review(OUT_DIR / "projection_review.png", OUT_DIR, ASSETS, [CELL_RESOLUTION, CELL_RESOLUTION, CELL_RESOLUTION])
    render_pipeline_reference(models, OUT_DIR / "reference_dog_pipeline.png")
    render_individual_reference_views(models)
    return manifest


def main() -> None:
    manifest = generate()
    print(f"Generated {len(manifest)} dog-trial .vox files in {OUT_DIR.relative_to(ROOT)}")
    for item in manifest:
        print(f"{item['name']}: size={item['size']} voxels={item['voxel_count']}")

    print("Running dog-trial checks...")
    from workflows.check_dog_trial import main as check_main

    check_main()


if __name__ == "__main__":
    main()
