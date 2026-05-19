#!/usr/bin/env python3
"""Check generated horse asset against structure and source-sheet constraints."""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voxel_asset_pipeline.checks import color_points, components, read_vox


OUT_DIR = ROOT / "examples" / "horse_trial"
REPORT_PATH = OUT_DIR / "check_report.json"
CELL_RESOLUTION = 64
ASSET_NAMES = ["voxel_horse"]


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


def check_voxel_horse(model: dict) -> dict:
    checks: list[dict] = []
    size = model["size"]
    check_item(checks, "size", size, [46, 34, 16])
    check_item(checks, "inside_one_cell", game_cells(size), [1, 1, 1])
    check_item(checks, "max_axis_within_source_scale", max(size), "<= 46", passed=max(size) <= 46)
    check_item(checks, "has_voxels", len(model["voxels"]), "> 0", passed=len(model["voxels"]) > 0)
    add_structure_checks(checks, model)

    coat = color_points(model, {"orange", "soil", "soil_light"})
    mane_tail = color_points(model, {"wood_dark"})
    hooves_nose_eyes = color_points(model, {"black"})
    blaze = color_points(model, {"white"})
    check_item(checks, "coat_voxels_min", len(coat), ">= 1600", passed=len(coat) >= 1600)
    check_item(checks, "mane_tail_voxels_min", len(mane_tail), ">= 450", passed=len(mane_tail) >= 450)
    check_item(checks, "black_detail_voxels_min", len(hooves_nose_eyes), ">= 120", passed=len(hooves_nose_eyes) >= 120)
    check_item(checks, "white_blaze_voxels_min", len(blaze), ">= 30", passed=len(blaze) >= 30)
    check_item(checks, "declared_source_side_size", [46, 34], [46, 34])
    check_item(checks, "declared_source_front_size", [16, 34], [16, 34])
    check_item(checks, "declared_source_top_size", [46, 16], [46, 16])
    return {"name": "voxel_horse", "checks": checks, "pass": all(c["pass"] for c in checks)}


def main() -> None:
    models = {name: read_vox(OUT_DIR / f"{name}.vox") for name in ASSET_NAMES}
    report = [check_voxel_horse(models["voxel_horse"])]
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
