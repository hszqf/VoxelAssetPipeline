#!/usr/bin/env python3
"""Small CLI for the standalone VoxelAssetPipeline project."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run_python(script: Path, *args: str) -> int:
    return subprocess.call([sys.executable, str(script), *args], cwd=ROOT)


def main() -> None:
    parser = argparse.ArgumentParser(prog="voxel_pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("generate-design-sheet")
    sub.add_parser("check-design-sheet")
    sub.add_parser("generate-quick-trial")
    sub.add_parser("check-quick-trial")
    sub.add_parser("generate-house-trial")
    sub.add_parser("check-house-trial")
    sub.add_parser("generate-dog-trial")
    sub.add_parser("check-dog-trial")
    sub.add_parser("generate-horse-trial")
    sub.add_parser("check-horse-trial")
    sub.add_parser("generate-pig-trial")
    sub.add_parser("check-pig-trial")
    sub.add_parser("generate-yellow-mouse-trial")
    sub.add_parser("check-yellow-mouse-trial")
    check_source = sub.add_parser("check-source-sheet")
    check_source.add_argument("--image", required=True)
    check_source.add_argument("--asset", required=True)
    check_source.add_argument("--side", required=True)
    check_source.add_argument("--front", required=True)
    check_source.add_argument("--top", required=True)
    check_source.add_argument("--tolerance", default="4")
    check_source.add_argument("--origin-tolerance", default="4")
    check_source.add_argument("--grid-line-tolerance", default="12")
    check_source.add_argument("--grid-size", default="64")
    check_source.add_argument("--side-frame")
    check_source.add_argument("--front-frame")
    check_source.add_argument("--top-frame")
    check_source.add_argument("--allow-colored-annotations", action="store_true")
    check_source.add_argument("--json-out")
    clean_source = sub.add_parser("clean-source-sheet")
    clean_source.add_argument("--image", required=True)
    clean_source.add_argument("--asset", required=True)
    clean_source.add_argument("--out", required=True)
    clean_source.add_argument("--json-out")
    clean_source.add_argument("--overlay-out")
    clean_source.add_argument("--grid-size", default="32")
    clean_source.add_argument("--cell-px", default="16")
    clean_source.add_argument("--bucket-size", default="8")
    clean_source.add_argument("--sample-padding", default="0.18")
    clean_source.add_argument("--object-threshold", default="0.18")
    clean_source.add_argument("--side-frame")
    clean_source.add_argument("--front-frame")
    clean_source.add_argument("--top-frame")
    sub.add_parser("build-viewer-data")
    apply_lw = sub.add_parser("apply-littleworld")
    apply_lw.add_argument("--project", required=True)
    args = parser.parse_args()

    if args.cmd == "generate-design-sheet":
        raise SystemExit(run_python(ROOT / "workflows" / "littleworld_design_sheet.py"))
    if args.cmd == "check-design-sheet":
        raise SystemExit(run_python(ROOT / "workflows" / "check_design_sheet.py"))
    if args.cmd == "generate-quick-trial":
        raise SystemExit(run_python(ROOT / "workflows" / "quick_trial_assets.py"))
    if args.cmd == "check-quick-trial":
        raise SystemExit(run_python(ROOT / "workflows" / "check_quick_trial.py"))
    if args.cmd == "generate-house-trial":
        raise SystemExit(run_python(ROOT / "workflows" / "house_trial_assets.py"))
    if args.cmd == "check-house-trial":
        raise SystemExit(run_python(ROOT / "workflows" / "check_house_trial.py"))
    if args.cmd == "generate-dog-trial":
        raise SystemExit(run_python(ROOT / "workflows" / "dog_trial_assets.py"))
    if args.cmd == "check-dog-trial":
        raise SystemExit(run_python(ROOT / "workflows" / "check_dog_trial.py"))
    if args.cmd == "generate-horse-trial":
        raise SystemExit(run_python(ROOT / "workflows" / "horse_trial_assets.py"))
    if args.cmd == "check-horse-trial":
        raise SystemExit(run_python(ROOT / "workflows" / "check_horse_trial.py"))
    if args.cmd == "generate-pig-trial":
        raise SystemExit(run_python(ROOT / "workflows" / "pig_trial_assets.py"))
    if args.cmd == "check-pig-trial":
        raise SystemExit(run_python(ROOT / "workflows" / "check_pig_trial.py"))
    if args.cmd == "generate-yellow-mouse-trial":
        raise SystemExit(run_python(ROOT / "workflows" / "yellow_mouse_trial_assets.py"))
    if args.cmd == "check-yellow-mouse-trial":
        raise SystemExit(run_python(ROOT / "workflows" / "check_yellow_mouse_trial.py"))
    if args.cmd == "check-source-sheet":
        cmd_args = [
            "--image",
            args.image,
            "--asset",
            args.asset,
            "--side",
            args.side,
            "--front",
            args.front,
            "--top",
            args.top,
            "--tolerance",
            args.tolerance,
            "--origin-tolerance",
            args.origin_tolerance,
            "--grid-line-tolerance",
            args.grid_line_tolerance,
            "--grid-size",
            args.grid_size,
        ]
        if args.side_frame:
            cmd_args.extend(["--side-frame", args.side_frame])
        if args.front_frame:
            cmd_args.extend(["--front-frame", args.front_frame])
        if args.top_frame:
            cmd_args.extend(["--top-frame", args.top_frame])
        if args.allow_colored_annotations:
            cmd_args.append("--allow-colored-annotations")
        if args.json_out:
            cmd_args.extend(["--json-out", args.json_out])
        raise SystemExit(run_python(ROOT / "voxel_asset_pipeline" / "source_sheet_check.py", *cmd_args))
    if args.cmd == "clean-source-sheet":
        cmd_args = [
            "--image",
            args.image,
            "--asset",
            args.asset,
            "--out",
            args.out,
            "--grid-size",
            args.grid_size,
            "--cell-px",
            args.cell_px,
            "--bucket-size",
            args.bucket_size,
            "--sample-padding",
            args.sample_padding,
            "--object-threshold",
            args.object_threshold,
        ]
        if args.json_out:
            cmd_args.extend(["--json-out", args.json_out])
        if args.overlay_out:
            cmd_args.extend(["--overlay-out", args.overlay_out])
        if args.side_frame:
            cmd_args.extend(["--side-frame", args.side_frame])
        if args.front_frame:
            cmd_args.extend(["--front-frame", args.front_frame])
        if args.top_frame:
            cmd_args.extend(["--top-frame", args.top_frame])
        raise SystemExit(run_python(ROOT / "voxel_asset_pipeline" / "source_sheet_clean.py", *cmd_args))
    if args.cmd == "build-viewer-data":
        raise SystemExit(subprocess.call(["node", str(ROOT / "viewer" / "build-embedded-data.mjs")], cwd=ROOT))
    if args.cmd == "apply-littleworld":
        raise SystemExit(run_python(ROOT / "adapters" / "littleworld" / "apply_to_unity_prefabs.py", "--project", args.project))


if __name__ == "__main__":
    main()
