#!/usr/bin/env python3
"""Check generated horse asset against structure, scale, and horse-specific cues."""

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
    voxels = model["voxels"]
    check_item(checks, "size", size, [46, 34, 16])
    check_item(checks, "inside_one_cell", game_cells(size), [1, 1, 1])
    check_item(checks, "max_axis_within_style_scale", max(size), "<= 48", passed=max(size) <= 48)
    check_item(checks, "has_voxels", len(voxels), "> 0", passed=len(voxels) > 0)
    add_structure_checks(checks, model)

    coat = color_points(model, {"wood", "sand", "sand_dark"})
    mane_tail = color_points(model, {"wood_dark"})
    muzzle = color_points(model, {"cream"})
    black = color_points(model, {"black"})
    hoof_points = {pos for pos in black if pos[1] <= 1}
    hoof_components = components(hoof_points)

    check_item(checks, "coat_voxels_min", len(coat), ">= 2800", passed=len(coat) >= 2800)
    check_item(checks, "mane_tail_voxels_min", len(mane_tail), ">= 250", passed=len(mane_tail) >= 250)
    check_item(checks, "muzzle_voxels_min", len(muzzle), ">= 25", passed=len(muzzle) >= 25)
    check_item(checks, "face_detail_voxels_min", len(black - hoof_points), ">= 4", passed=len(black - hoof_points) >= 4)
    check_item(checks, "hoof_component_count", len(hoof_components), 4)
    check_item(checks, "ears_reach_top", any(pos[1] >= 32 for pos in mane_tail), True)
    check_item(checks, "tail_reaches_rear", any(pos[0] <= 2 and pos[1] >= 10 for pos in mane_tail), True)
    check_item(checks, "head_reaches_front", any(pos[0] >= 44 and color in {"cream", "sand_dark"} for pos, color in voxels.items()), True)
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
