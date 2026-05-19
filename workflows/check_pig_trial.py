#!/usr/bin/env python3
"""Check generated pig asset against source-derived structure and colors."""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voxel_asset_pipeline.checks import color_points, components, read_vox
from voxel_asset_pipeline.render import VIEWS, model_offset, visible_projection


OUT_DIR = ROOT / "examples" / "pig_trial"
REPORT_PATH = OUT_DIR / "check_report.json"
CELL_RESOLUTION = 32
ASSET_NAMES = ["voxel_pig"]


def check_item(checks: list[dict], check_id: str, actual, expected, passed: bool | None = None) -> None:
    checks.append(
        {
            "id": check_id,
            "pass": actual == expected if passed is None else passed,
            "expected": expected,
            "actual": actual,
        }
    )


def game_cells(size: list[int]) -> list[int]:
    return [max(1, math.ceil(v / CELL_RESOLUTION)) for v in size]


def add_structure_checks(checks: list[dict], model: dict) -> None:
    comps = components(model["voxels"].keys())
    sizes = sorted((len(comp) for comp in comps), reverse=True)
    check_item(checks, "single_connected_component", len(comps), 1)
    check_item(checks, "floating_component_sizes", sizes[1:], [])


def projection_size(model: dict, view) -> list[int]:
    projection = visible_projection(model, view, model_offset_from_dict(model))
    xs = [x for x, _ in projection]
    ys = [y for _, y in projection]
    return [max(xs) - min(xs) + 1, max(ys) - min(ys) + 1] if projection else [0, 0]


def model_offset_from_dict(model: dict) -> tuple[int, int, int]:
    width, height, depth = model["size"]
    return ((CELL_RESOLUTION - width) // 2, 0, (CELL_RESOLUTION - depth) // 2)


def check_voxel_pig(model: dict) -> dict:
    checks: list[dict] = []
    size = model["size"]
    check_item(checks, "size", size, [20, 15, 9])
    check_item(checks, "inside_one_32_cell", game_cells(size), [1, 1, 1])
    check_item(checks, "has_voxels", len(model["voxels"]), "> 0", passed=len(model["voxels"]) > 0)
    check_item(checks, "voxel_count_range", len(model["voxels"]), "1000..1500", passed=1000 <= len(model["voxels"]) <= 1500)
    add_structure_checks(checks, model)

    body = color_points(model, {"pig_body", "pig_body_light", "pig_shadow"})
    dark = color_points(model, {"pig_dark", "pig_deep"})
    black = color_points(model, {"pig_black"})
    check_item(checks, "body_voxels_min", len(body), ">= 350", passed=len(body) >= 350)
    check_item(checks, "dark_detail_voxels_min", len(dark), ">= 12", passed=len(dark) >= 12)
    check_item(checks, "black_detail_voxels_min", len(black), ">= 8", passed=len(black) >= 8)

    side_size = projection_size(model, VIEWS[0])
    front_size = projection_size(model, VIEWS[1])
    top_size = projection_size(model, VIEWS[2])
    check_item(checks, "side_projection_size", side_size, [20, 15])
    check_item(checks, "front_projection_size", front_size, [9, 15])
    check_item(checks, "top_projection_width", top_size[0], "19..20", passed=19 <= top_size[0] <= 20)
    check_item(checks, "top_projection_depth", top_size[1], 9)
    return {"name": "voxel_pig", "checks": checks, "pass": all(c["pass"] for c in checks)}


def main() -> None:
    models = {name: read_vox(OUT_DIR / f"{name}.vox") for name in ASSET_NAMES}
    report = [check_voxel_pig(models["voxel_pig"])]
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    failed = [item for item in report if not item["pass"]]
    for item in report:
        status = "PASS" if item["pass"] else "FAIL"
        print(f"{status} {item['name']}")
        for check in item["checks"]:
            if not check["pass"]:
                print(f"  - {check['id']}: expected {check['expected']}, actual {check['actual']}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
