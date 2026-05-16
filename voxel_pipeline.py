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
    sub.add_parser("build-viewer-data")
    apply_lw = sub.add_parser("apply-littleworld")
    apply_lw.add_argument("--project", required=True)
    args = parser.parse_args()

    if args.cmd == "generate-design-sheet":
        raise SystemExit(run_python(ROOT / "workflows" / "littleworld_design_sheet.py"))
    if args.cmd == "check-design-sheet":
        raise SystemExit(run_python(ROOT / "workflows" / "check_design_sheet.py"))
    if args.cmd == "build-viewer-data":
        raise SystemExit(subprocess.call(["node", str(ROOT / "viewer" / "build-embedded-data.mjs")], cwd=ROOT))
    if args.cmd == "apply-littleworld":
        raise SystemExit(run_python(ROOT / "adapters" / "littleworld" / "apply_to_unity_prefabs.py", "--project", args.project))


if __name__ == "__main__":
    main()
