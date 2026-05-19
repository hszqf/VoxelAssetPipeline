#!/usr/bin/env python3
"""Generate a single voxel house asset with review images."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voxel_asset_pipeline.model import VoxelModel, render_preview_png, render_preview_svg, write_png, write_vox
from voxel_asset_pipeline.render import VIEWS, render_review
from workflows.littleworld_design_sheet import draw_iso_panel, draw_projection_panel, render_pipeline_reference


OUT_DIR = ROOT / "examples" / "house_trial"
CELL_RESOLUTION = 64
ASSETS = ["voxel_cottage"]


def make_voxel_cottage() -> VoxelModel:
    m = VoxelModel("voxel_cottage", 34, 34, 28)

    m.box(3, 31, 0, 2, 3, 25, "stone_dark")
    m.box(4, 30, 2, 4, 4, 24, "stone")

    m.box(5, 29, 4, 19, 5, 23, "cream")
    m.box(5, 29, 4, 6, 5, 23, "sand_dark")
    m.box(5, 7, 4, 19, 5, 23, "wood")
    m.box(27, 29, 4, 19, 5, 23, "wood_dark")

    m.box(14, 20, 4, 13, 23, 24, "wood_dark")
    m.box(15, 19, 5, 13, 24, 25, "wood")
    m.set(19, 9, 24, "yellow")

    for x0 in (8, 23):
        m.box(x0, x0 + 5, 10, 16, 23, 24, "wood_dark")
        m.box(x0 + 1, x0 + 4, 11, 15, 24, 26, "cyan")
        m.box(x0 + 2, x0 + 3, 10, 16, 24, 25, "wood_dark")
        m.box(x0, x0 + 5, 12, 13, 24, 25, "wood_dark")

    m.box(29, 30, 9, 15, 10, 16, "wood_dark")
    m.box(30, 32, 10, 14, 11, 15, "blue")
    m.box(30, 31, 12, 13, 11, 15, "wood_dark")
    m.box(30, 31, 10, 14, 13, 14, "wood_dark")

    eave_y = 18
    center_x = 16.5
    for x in range(1, 33):
        roof_height = max(0, int(14 - abs(x + 0.5 - center_x)))
        top_y = eave_y + roof_height
        color = "red_light" if 14 <= x <= 18 else "red"
        for z in range(2, 26):
            for y in range(eave_y, top_y + 1):
                m.set(x, y, z, color)

    m.box(1, 33, 17, 19, 2, 26, "wood_dark")
    m.box(15, 19, 31, 33, 2, 26, "red_light")

    m.box(23, 27, 25, 34, 15, 19, "stone_dark")
    m.box(24, 26, 26, 34, 16, 18, "stone")
    m.box(22, 28, 33, 34, 14, 20, "stone_dark")

    m.box(12, 22, 2, 4, 23, 27, "wood")
    m.box(10, 24, 1, 2, 23, 28, "stone")
    return m


BUILDERS = [make_voxel_cottage]


def reference_view_items(model_name: str) -> list[dict]:
    base = "examples/house_trial/reference_views"
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


def write_dataset_metadata() -> None:
    metadata = {
        "id": "house-trial",
        "name": "Voxel House",
        "cellResolution": CELL_RESOLUTION,
        "order": 75,
    }
    (OUT_DIR / "dataset.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")


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
                "scale_tier": "small",
                "review_status": "pending_review",
                "size": [model.width, model.height, model.depth],
                "voxel_count": len(model.voxels),
                "observed": "Procedural voxel cottage with stone foundation, cream walls, gabled roof, chimney, door, windows, and entry step.",
            }
        )

    write_dataset_metadata()
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    render_preview_png(models, OUT_DIR / "preview.png")
    render_preview_svg(models, OUT_DIR / "preview.svg")
    render_review(OUT_DIR / "projection_review.png", OUT_DIR, ASSETS, [CELL_RESOLUTION, CELL_RESOLUTION, CELL_RESOLUTION])
    render_pipeline_reference(models, OUT_DIR / "reference_house_pipeline.png")
    render_individual_reference_views(models)
    return manifest


def main() -> None:
    manifest = generate()
    print(f"Generated {len(manifest)} house-trial .vox files in {OUT_DIR.relative_to(ROOT)}")
    for item in manifest:
        print(f"{item['name']}: size={item['size']} voxels={item['voxel_count']}")

    print("Running house-trial checks...")
    from workflows.check_house_trial import main as check_main

    check_main()


if __name__ == "__main__":
    main()
