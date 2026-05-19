#!/usr/bin/env python3
"""Check generated yellow fantasy mouse asset against source-derived structure."""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voxel_asset_pipeline.checks import color_points, components, read_vox
from voxel_asset_pipeline.render import VIEWS, visible_projection


OUT_DIR = ROOT / "examples" / "yellow_mouse_trial"
REPORT_PATH = OUT_DIR / "check_report.json"
CELL_RESOLUTION = 64
ASSET_NAMES = ["voxel_yellow_fantasy_mouse"]


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


def model_offset_from_dict(model: dict) -> tuple[int, int, int]:
    width, height, depth = model["size"]
    return ((CELL_RESOLUTION - width) // 2, 0, (CELL_RESOLUTION - depth) // 2)


def projection_size(model: dict, view) -> list[int]:
    projection = visible_projection(model, view, model_offset_from_dict(model))
    xs = [x for x, _ in projection]
    ys = [y for _, y in projection]
    return [max(xs) - min(xs) + 1, max(ys) - min(ys) + 1] if projection else [0, 0]


def check_voxel_yellow_fantasy_mouse(model: dict) -> dict:
    checks: list[dict] = []
    size = model["size"]
    voxels = model["voxels"]
    check_item(checks, "size", size, [22, 24, 20])
    check_item(checks, "inside_one_64_cell", game_cells(size), [1, 1, 1])
    check_item(checks, "has_voxels", len(voxels), "> 0", passed=len(voxels) > 0)
    check_item(checks, "voxel_count_range", len(voxels), "700..4500", passed=700 <= len(voxels) <= 4500)
    add_structure_checks(checks, model)

    body = color_points(model, {"yellow", "yellow_light", "yellow_dark"})
    cream = color_points(model, {"cream"})
    brown = color_points(model, {"mouse_brown", "mouse_brown_dark", "wood", "wood_dark"})
    black = color_points(model, {"black"})
    teal = color_points(model, {"mouse_teal"})
    check_item(checks, "yellow_body_voxels_min", len(body), ">= 450", passed=len(body) >= 450)
    check_item(checks, "cream_detail_voxels_min", len(cream), ">= 20", passed=len(cream) >= 20)
    check_item(checks, "brown_detail_voxels_min", len(brown), ">= 8", passed=len(brown) >= 8)
    check_item(checks, "black_detail_voxels_min", len(black), ">= 4", passed=len(black) >= 4)
    check_item(checks, "teal_cheek_voxels_min", len(teal), ">= 4", passed=len(teal) >= 4)

    side_size = projection_size(model, VIEWS[0])
    front_size = projection_size(model, VIEWS[1])
    top_size = projection_size(model, VIEWS[2])
    check_item(checks, "side_projection_width", side_size[0], "18..22", passed=18 <= side_size[0] <= 22)
    check_item(checks, "side_projection_height", side_size[1], "20..24", passed=20 <= side_size[1] <= 24)
    check_item(checks, "front_projection_width", front_size[0], "16..20", passed=16 <= front_size[0] <= 20)
    check_item(checks, "front_projection_height", front_size[1], "20..24", passed=20 <= front_size[1] <= 24)
    check_item(checks, "top_projection_width", top_size[0], "18..22", passed=18 <= top_size[0] <= 22)
    check_item(checks, "top_projection_depth", top_size[1], "16..20", passed=16 <= top_size[1] <= 20)
    return {"name": "voxel_yellow_fantasy_mouse", "checks": checks, "pass": all(c["pass"] for c in checks)}


def main() -> None:
    models = {name: read_vox(OUT_DIR / f"{name}.vox") for name in ASSET_NAMES}
    report = [check_voxel_yellow_fantasy_mouse(models["voxel_yellow_fantasy_mouse"])]
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
