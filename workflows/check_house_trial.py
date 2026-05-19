#!/usr/bin/env python3
"""Check generated house asset against structure and scale constraints."""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voxel_asset_pipeline.checks import color_points, components, read_vox


OUT_DIR = ROOT / "examples" / "house_trial"
REPORT_PATH = OUT_DIR / "check_report.json"
CELL_RESOLUTION = 64
ASSET_NAMES = ["voxel_cottage"]


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


def base_checks(model: dict, expected_size: list[int], max_axis: int) -> list[dict]:
    checks: list[dict] = []
    size = model["size"]
    check_item(checks, "size", size, expected_size)
    check_item(checks, "inside_one_cell", game_cells(size), [1, 1, 1])
    check_item(checks, "max_axis_within_style_scale", max(size), f"<= {max_axis}", passed=max(size) <= max_axis)
    check_item(checks, "has_voxels", len(model["voxels"]), "> 0", passed=len(model["voxels"]) > 0)
    add_structure_checks(checks, model)
    return checks


def check_voxel_cottage(model: dict) -> dict:
    checks = base_checks(model, [34, 34, 28], 40)
    wall = color_points(model, {"cream", "sand_dark"})
    roof = color_points(model, {"red", "red_light"})
    wood = color_points(model, {"wood", "wood_dark"})
    stone = color_points(model, {"stone", "stone_dark"})
    glass = color_points(model, {"blue", "cyan"})
    check_item(checks, "wall_voxels_min", len(wall), ">= 3500", passed=len(wall) >= 3500)
    check_item(checks, "roof_voxels_min", len(roof), ">= 2600", passed=len(roof) >= 2600)
    check_item(checks, "wood_voxels_min", len(wood), ">= 450", passed=len(wood) >= 450)
    check_item(checks, "stone_voxels_min", len(stone), ">= 900", passed=len(stone) >= 900)
    check_item(checks, "window_voxels_min", len(glass), ">= 35", passed=len(glass) >= 35)
    check_item(checks, "chimney_reaches_top", any(pos[1] == 33 for pos in stone), True)
    return {"name": "voxel_cottage", "checks": checks, "pass": all(c["pass"] for c in checks)}


def main() -> None:
    models = {name: read_vox(OUT_DIR / f"{name}.vox") for name in ASSET_NAMES}
    report = [check_voxel_cottage(models["voxel_cottage"])]
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
