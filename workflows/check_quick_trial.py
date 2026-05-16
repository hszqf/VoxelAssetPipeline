#!/usr/bin/env python3
"""Check quick-trial assets against basic structure and scale constraints."""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voxel_asset_pipeline.checks import color_points, components, read_vox


OUT_DIR = ROOT / "examples" / "quick_trial"
REPORT_PATH = OUT_DIR / "check_report.json"
CELL_RESOLUTION = 64
ASSET_NAMES = [
    "trial_cactus",
    "trial_frog",
    "trial_rock_cluster",
    "trial_lantern",
]


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


def check_cactus(model: dict) -> dict:
    checks = base_checks(model, [16, 23, 16], 24)
    cactus = color_points(model, {"cactus", "cactus_light"})
    flower = color_points(model, {"red"})
    check_item(checks, "cactus_voxels_min", len(cactus), ">= 120", passed=len(cactus) >= 120)
    check_item(checks, "flower_voxels", len(flower), 2)
    return {"name": "trial_cactus", "checks": checks, "pass": all(c["pass"] for c in checks)}


def check_frog(model: dict) -> dict:
    checks = base_checks(model, [18, 10, 16], 20)
    frog = color_points(model, {"frog", "frog_light"})
    eyes = color_points(model, {"white", "black"})
    check_item(checks, "body_voxels_min", len(frog), ">= 250", passed=len(frog) >= 250)
    check_item(checks, "eye_voxels", len(eyes), 4)
    return {"name": "trial_frog", "checks": checks, "pass": all(c["pass"] for c in checks)}


def check_rock_cluster(model: dict) -> dict:
    checks = base_checks(model, [18, 9, 16], 20)
    stones = color_points(model, {"stone", "stone_dark", "stone_light"})
    check_item(checks, "stone_voxels_min", len(stones), ">= 300", passed=len(stones) >= 300)
    check_item(checks, "low_profile", model["size"][1], "<= 9", passed=model["size"][1] <= 9)
    return {"name": "trial_rock_cluster", "checks": checks, "pass": all(c["pass"] for c in checks)}


def check_lantern(model: dict) -> dict:
    checks = base_checks(model, [12, 22, 12], 24)
    light = color_points(model, {"yellow", "yellow_light"})
    wood = color_points(model, {"wood", "wood_dark"})
    check_item(checks, "light_voxels_min", len(light), ">= 200", passed=len(light) >= 200)
    check_item(checks, "wood_voxels_min", len(wood), ">= 60", passed=len(wood) >= 60)
    return {"name": "trial_lantern", "checks": checks, "pass": all(c["pass"] for c in checks)}


def main() -> None:
    models = {name: read_vox(OUT_DIR / f"{name}.vox") for name in ASSET_NAMES}
    report = [
        check_cactus(models["trial_cactus"]),
        check_frog(models["trial_frog"]),
        check_rock_cluster(models["trial_rock_cluster"]),
        check_lantern(models["trial_lantern"]),
    ]
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
