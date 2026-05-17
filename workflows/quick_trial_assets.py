#!/usr/bin/env python3
"""Generate a second small asset set to exercise the standalone pipeline."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voxel_asset_pipeline.model import VoxelModel, render_preview_png, render_preview_svg, write_png, write_vox
from voxel_asset_pipeline.render import VIEWS, render_review
from workflows.littleworld_design_sheet import draw_iso_panel, draw_projection_panel, render_pipeline_reference


OUT_DIR = ROOT / "examples" / "quick_trial"
CELL_RESOLUTION = 64
ASSETS = [
    "trial_cactus",
    "trial_frog",
    "trial_rock_cluster",
    "trial_lantern",
]


def make_trial_cactus() -> VoxelModel:
    m = VoxelModel("trial_cactus", 16, 23, 16)
    m.box(4, 12, 0, 2, 4, 12, "sand")
    m.box(5, 11, 2, 3, 5, 11, "sand_light")

    m.box(7, 10, 3, 18, 7, 10, "cactus")
    m.box(8, 9, 3, 18, 8, 9, "cactus_light")
    m.box(4, 7, 9, 12, 7, 10, "cactus")
    m.box(4, 6, 9, 16, 7, 10, "cactus")
    m.box(10, 13, 12, 15, 7, 10, "cactus")
    m.box(12, 14, 12, 20, 7, 10, "cactus")
    m.box(7, 10, 18, 20, 7, 10, "cactus_light")
    m.box(8, 9, 20, 22, 8, 9, "red")
    return m


def make_trial_frog() -> VoxelModel:
    m = VoxelModel("trial_frog", 18, 10, 16)
    m.ellipsoid(9.0, 3.6, 8.0, 6.8, 3.0, 5.2, "frog")
    m.ellipsoid(9.0, 3.2, 8.0, 4.0, 2.0, 3.2, "frog_light")
    m.box(2, 7, 0, 2, 3, 6, "frog")
    m.box(11, 16, 0, 2, 3, 6, "frog")
    m.box(3, 7, 0, 2, 10, 13, "frog")
    m.box(11, 15, 0, 2, 10, 13, "frog")

    m.box(4, 7, 6, 8, 4, 7, "frog_light")
    m.box(11, 14, 6, 8, 4, 7, "frog_light")
    m.set(5, 8, 5, "white")
    m.set(12, 8, 5, "white")
    m.set(5, 8, 4, "black")
    m.set(12, 8, 4, "black")
    return m


def make_trial_rock_cluster() -> VoxelModel:
    m = VoxelModel("trial_rock_cluster", 18, 9, 16)
    m.ellipsoid(7.0, 3.2, 8.0, 5.5, 3.2, 4.4, "stone")
    m.ellipsoid(11.4, 3.8, 7.4, 4.5, 3.4, 4.0, "stone_dark")
    m.ellipsoid(9.2, 5.0, 10.8, 3.8, 3.0, 3.6, "stone_light")
    m.box(5, 14, 0, 1, 5, 12, "stone_dark")
    return m


def make_trial_lantern() -> VoxelModel:
    m = VoxelModel("trial_lantern", 12, 22, 12)
    m.box(3, 9, 0, 2, 3, 9, "wood_dark")
    m.box(5, 7, 2, 11, 5, 7, "wood")
    m.box(3, 9, 10, 16, 3, 9, "yellow")
    m.box(4, 8, 11, 15, 4, 8, "yellow_light")
    m.box(2, 10, 16, 18, 2, 10, "orange")
    m.box(4, 8, 18, 20, 4, 8, "red")
    m.box(5, 7, 20, 22, 5, 7, "wood_dark")
    return m


BUILDERS = [
    make_trial_cactus,
    make_trial_frog,
    make_trial_rock_cluster,
    make_trial_lantern,
]


def reference_view_items(model_name: str) -> list[dict]:
    base = "examples/quick_trial/reference_views"
    return [
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
        reference_views = reference_view_items(model.name)
        manifest.append(
            {
                "name": model.name,
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "source_image": reference_views[0]["path"],
                "reference_views": reference_views,
                "cell_resolution": CELL_RESOLUTION,
                "game_cells": [1, 1, 1],
                "scale_tier": "tiny",
                "review_status": "pending_review",
                "size": [model.width, model.height, model.depth],
                "voxel_count": len(model.voxels),
                "observed": "Quick-trial procedural asset used to test a fresh generate/check/viewer path.",
            }
        )

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    render_preview_png(models, OUT_DIR / "preview.png")
    render_preview_svg(models, OUT_DIR / "preview.svg")
    render_review(OUT_DIR / "projection_review.png", OUT_DIR, ASSETS, [CELL_RESOLUTION, CELL_RESOLUTION, CELL_RESOLUTION])
    render_pipeline_reference(models, OUT_DIR / "reference_quick_trial_pipeline.png")
    render_individual_reference_views(models)
    return manifest


def main() -> None:
    manifest = generate()
    print(f"Generated {len(manifest)} quick-trial .vox files in {OUT_DIR.relative_to(ROOT)}")
    for item in manifest:
        print(f"{item['name']}: size={item['size']} voxels={item['voxel_count']}")

    print("Running quick-trial checks...")
    from workflows.check_quick_trial import main as check_main

    check_main()


if __name__ == "__main__":
    main()
