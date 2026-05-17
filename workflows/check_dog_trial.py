#!/usr/bin/env python3
"""Check selected dog asset against structure and dog-specific cues."""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voxel_asset_pipeline.checks import color_points, components, read_vox


OUT_DIR = ROOT / "examples" / "dog_trial"
REPORT_PATH = OUT_DIR / "check_report.json"
CELL_RESOLUTION = 64
ASSET_NAMES = ["dog_golden"]


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


def check_dog_golden(model: dict) -> dict:
    checks: list[dict] = []
    size = model["size"]
    check_item(checks, "size", size, [24, 16, 14])
    check_item(checks, "inside_one_cell", game_cells(size), [1, 1, 1])
    check_item(checks, "max_axis_within_style_scale", max(size), "<= 24", passed=max(size) <= 24)
    check_item(checks, "has_voxels", len(model["voxels"]), "> 0", passed=len(model["voxels"]) > 0)
    add_structure_checks(checks, model)

    coat = color_points(model, {"sand", "sand_light"})
    muzzle = color_points(model, {"cream"})
    ears_and_paws = color_points(model, {"wood_dark"})
    collar = color_points(model, {"blue"})
    face = color_points(model, {"black"})
    check_item(checks, "coat_voxels_min", len(coat), ">= 300", passed=len(coat) >= 300)
    check_item(checks, "muzzle_voxels_min", len(muzzle), ">= 60", passed=len(muzzle) >= 60)
    check_item(checks, "ear_and_paw_voxels_min", len(ears_and_paws), ">= 50", passed=len(ears_and_paws) >= 50)
    check_item(checks, "collar_voxels", len(collar), 18)
    check_item(checks, "face_detail_voxels_min", len(face), ">= 10", passed=len(face) >= 10)
    return {"name": "dog_golden", "checks": checks, "pass": all(c["pass"] for c in checks)}


def main() -> None:
    models = {name: read_vox(OUT_DIR / f"{name}.vox") for name in ASSET_NAMES}
    report = [check_dog_golden(models["dog_golden"])]
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
