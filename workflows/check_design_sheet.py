#!/usr/bin/env python3
"""Check design-sheet trial assets against style and proportion constraints."""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voxel_asset_pipeline.checks import color_points, components, read_vox
OUT_DIR = ROOT / "examples" / "design_sheet_trial"
REPORT_PATH = OUT_DIR / "check_report.json"
CELL_RESOLUTION = 64
ASSET_NAMES = [
    "design_flower",
    "design_mushroom",
    "design_shell",
    "design_bee",
    "design_butterfly",
    "design_fish",
    "design_tree",
    "design_cloud",
    "design_crab",
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


def base_checks(name: str, model: dict, expected_size: list[int], max_axis: int) -> list[dict]:
    checks: list[dict] = []
    size = model["size"]
    check_item(checks, "size", size, expected_size)
    check_item(checks, "inside_one_cell", game_cells(size), [1, 1, 1])
    check_item(checks, "max_axis_within_style_scale", max(size), f"<= {max_axis}", passed=max(size) <= max_axis)
    check_item(checks, "has_voxels", len(model["voxels"]), "> 0", passed=len(model["voxels"]) > 0)
    add_structure_checks(checks, model)
    return checks


def check_flower(model: dict) -> dict:
    checks = base_checks("design_flower", model, [14, 18, 14], 22)
    petals = color_points(model, {"pink"})
    stem = color_points(model, {"stem"})
    center = color_points(model, {"yellow"})
    check_item(checks, "stem_components", len(components(stem)), 1)
    check_item(checks, "petal_voxels_min", len(petals), ">= 48", passed=len(petals) >= 48)
    check_item(checks, "yellow_center_voxels", len(center), 8)
    return {"name": "design_flower", "checks": checks, "pass": all(c["pass"] for c in checks)}


def check_mushroom(model: dict) -> dict:
    checks = base_checks("design_mushroom", model, [12, 12, 12], 14)
    cap = color_points(model, {"red"})
    stem = color_points(model, {"cream", "sand_light"})
    spots = color_points(model, {"white"})
    check_item(checks, "cap_components", len(components(cap)), 1)
    check_item(checks, "stem_components", len(components(stem)), 1)
    check_item(checks, "white_spots_min", len(components(spots)), ">= 3", passed=len(components(spots)) >= 3)
    return {"name": "design_mushroom", "checks": checks, "pass": all(c["pass"] for c in checks)}


def check_shell(model: dict) -> dict:
    checks = base_checks("design_shell", model, [14, 8, 10], 16)
    shell = set(model["voxels"])
    ribs = color_points(model, {"sand_dark"})
    check_item(checks, "shell_component", len(components(shell)), 1)
    check_item(checks, "rib_voxels_min", len(ribs), ">= 20", passed=len(ribs) >= 20)
    check_item(checks, "low_profile", model["size"][1], "<= 8", passed=model["size"][1] <= 8)
    return {"name": "design_shell", "checks": checks, "pass": all(c["pass"] for c in checks)}


def check_bee(model: dict) -> dict:
    checks = base_checks("design_bee", model, [20, 14, 14], 22)
    wings = color_points(model, {"wing"})
    head_eyes = {p for p, color in model["voxels"].items() if color == "black" and p[0] <= 2 and 6 <= p[1] <= 7 and p[2] in {5, 9}}
    stripes = {p for p, color in model["voxels"].items() if color == "black" and 6 <= p[0] <= 15}
    check_item(checks, "wing_components", len(components(wings)), 2)
    check_item(checks, "front_eye_voxels", len(head_eyes), 8)
    check_item(checks, "stripe_columns_min", len({p[0] for p in stripes}), ">= 5", passed=len({p[0] for p in stripes}) >= 5)
    return {"name": "design_bee", "checks": checks, "pass": all(c["pass"] for c in checks)}


def check_butterfly(model: dict) -> dict:
    checks = base_checks("design_butterfly", model, [8, 17, 22], 24)
    wings = color_points(model, {"orange"})
    body = {p for p, color in model["voxels"].items() if color == "black" and 3 <= p[0] <= 4 and 10 <= p[2] <= 11}
    markings = color_points(model, {"yellow"})
    check_item(checks, "wing_components", len(components(wings)), 4)
    check_item(checks, "body_component", len(components(body)), 1)
    check_item(checks, "yellow_mark_voxels", len(markings), 16)
    return {"name": "design_butterfly", "checks": checks, "pass": all(c["pass"] for c in checks)}


def check_fish(model: dict) -> dict:
    checks = base_checks("design_fish", model, [20, 11, 10], 22)
    eyes = color_points(model, {"white"})
    pupils = {p for p, color in model["voxels"].items() if color == "black" and p[0] <= 3}
    fins = color_points(model, {"water_dark", "water_light"})
    check_item(checks, "eye_components", len(components(eyes)), 2)
    check_item(checks, "pupil_voxels", len(pupils), 2)
    check_item(checks, "fin_voxels_min", len(fins), ">= 18", passed=len(fins) >= 18)
    return {"name": "design_fish", "checks": checks, "pass": all(c["pass"] for c in checks)}


def check_tree(model: dict) -> dict:
    checks = base_checks("design_tree", model, [28, 34, 28], 36)
    trunk = color_points(model, {"wood", "wood_dark"})
    canopy = {p for p, color in model["voxels"].items() if color in {"leaf", "leaf_light", "leaf_dark"} and p[1] >= 13}
    soil = color_points(model, {"soil"})
    check_item(checks, "trunk_components", len(components(trunk)), 1)
    check_item(checks, "canopy_components", len(components(canopy)), 1)
    check_item(checks, "base_voxels_min", len(soil), ">= 250", passed=len(soil) >= 250)
    return {"name": "design_tree", "checks": checks, "pass": all(c["pass"] for c in checks)}


def check_cloud(model: dict) -> dict:
    checks = base_checks("design_cloud", model, [20, 14, 16], 20)
    cloud = color_points(model, {"cloud", "cloud_shadow"})
    shadow = color_points(model, {"cloud_shadow"})
    check_item(checks, "cloud_components", len(components(cloud)), 1)
    check_item(checks, "shadow_voxels_min", len(shadow), ">= 120", passed=len(shadow) >= 120)
    check_item(checks, "compact_height", model["size"][1], "<= 14", passed=model["size"][1] <= 14)
    return {"name": "design_cloud", "checks": checks, "pass": all(c["pass"] for c in checks)}


def check_crab(model: dict) -> dict:
    checks = base_checks("design_crab", model, [24, 9, 18], 24)
    body = color_points(model, {"crab", "crab_light", "sand_light"})
    eyes = color_points(model, {"black"})
    check_item(checks, "body_components", len(components(body)), 1)
    check_item(checks, "eye_components", len(components(eyes)), 2)
    check_item(checks, "low_profile", model["size"][1], "<= 9", passed=model["size"][1] <= 9)
    return {"name": "design_crab", "checks": checks, "pass": all(c["pass"] for c in checks)}


def main() -> None:
    models = {name: read_vox(OUT_DIR / f"{name}.vox") for name in ASSET_NAMES}
    report = [
        check_flower(models["design_flower"]),
        check_mushroom(models["design_mushroom"]),
        check_shell(models["design_shell"]),
        check_bee(models["design_bee"]),
        check_butterfly(models["design_butterfly"]),
        check_fish(models["design_fish"]),
        check_tree(models["design_tree"]),
        check_cloud(models["design_cloud"]),
        check_crab(models["design_crab"]),
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


