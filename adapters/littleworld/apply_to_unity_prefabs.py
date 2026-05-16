#!/usr/bin/env python3
"""Point LittleWorld entity prefabs at generated design-sheet VOX files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SIZE_PER_VOX = "0.015625"
DEFAULT_ENTITIES = {
    "Flower": "design_flower.vox",
    "Mushroom": "design_mushroom.vox",
    "Shell": "design_shell.vox",
    "Bee": "design_bee.vox",
    "Butterfly": "design_butterfly.vox",
    "Fish": "design_fish.vox",
    "Tree": "design_tree.vox",
    "Cloud": "design_cloud.vox",
    "Crab": "design_crab.vox",
}


def patch_prefab(path: Path, vox_path: str) -> dict:
    text = path.read_text(encoding="utf-8")
    marker = "m_EditorClassIdentifier: Assembly-CSharp::MVVoxModel"
    marker_index = text.find(marker)
    if marker_index < 0:
        raise ValueError(f"{path} has no MVVoxModel block")
    next_doc = text.find("\n--- !u!", marker_index + len(marker))
    block_end = len(text) if next_doc < 0 else next_doc
    before = text[:marker_index]
    block = text[marker_index:block_end]
    after = text[block_end:]
    old_path_match = re.search(r"ed_filePath: (.*)", block)
    old_size_match = re.search(r"sizePerVox: (.*)", block)
    if not old_path_match or not old_size_match:
        raise ValueError(f"{path} MVVoxModel block is missing ed_filePath or sizePerVox")
    patched = re.sub(r"ed_filePath: .*", f"ed_filePath: {vox_path}", block, count=1)
    patched = re.sub(r"sizePerVox: .*", f"sizePerVox: {SIZE_PER_VOX}", patched, count=1)
    next_text = before + patched + after
    if next_text != text:
        path.write_text(next_text, encoding="utf-8", newline="\n")
    return {
        "prefab": str(path),
        "old_vox": old_path_match.group(1),
        "new_vox": vox_path,
        "old_size_per_vox": old_size_match.group(1),
        "new_size_per_vox": SIZE_PER_VOX,
        "changed": next_text != text,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="LittleWorld project root")
    parser.add_argument("--asset-root", default="Assets/Voxel/design_sheet_trial")
    parser.add_argument("--entities", nargs="*", default=list(DEFAULT_ENTITIES.keys()))
    args = parser.parse_args()
    project = Path(args.project).resolve()
    report = []
    for entity in args.entities:
        vox_name = DEFAULT_ENTITIES[entity]
        prefab = project / "Assets" / "Resources" / "LittleWorld" / "Entities" / f"Entity_{entity}.prefab"
        vox_path = f"{args.asset_root}/{vox_name}"
        report.append({"entity": entity, **patch_prefab(prefab, vox_path)})
    report_path = project / args.asset_root / "game_integration_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    for item in report:
        status = "updated" if item["changed"] else "already"
        print(f"{status}: {item['entity']} -> {item['new_vox']} @ {item['new_size_per_vox']}")


if __name__ == "__main__":
    main()
