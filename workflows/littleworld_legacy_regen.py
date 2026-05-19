#!/usr/bin/env python3
"""Regenerate LittleWorld legacy VOX references at the 64-voxel scale."""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voxel_asset_pipeline.checks import components, read_vox
from voxel_asset_pipeline.model import VoxelModel, write_vox


SIZE_PER_VOX = "0.015625"

REUSE_SOURCES = {
    "Dog": ROOT / "examples" / "dog_trial" / "dog_golden.vox",
    "Horse": ROOT / "examples" / "horse_trial" / "voxel_horse.vox",
    "Mouse": ROOT / "examples" / "yellow_mouse_trial" / "voxel_yellow_fantasy_mouse.vox",
    "Cactus": ROOT / "examples" / "quick_trial" / "trial_cactus.vox",
    "Frog": ROOT / "examples" / "quick_trial" / "trial_frog.vox",
}


def snake_name(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()


def prefab_info(path: Path) -> tuple[str, str] | None:
    text = path.read_text(encoding="utf-8")
    vox = re.search(r"ed_filePath: (.*)", text)
    size = re.search(r"sizePerVox: (.*)", text)
    if not vox or not size:
        return None
    return vox.group(1).strip(), size.group(1).strip()


def patch_prefab(path: Path, vox_path: str) -> dict:
    text = path.read_text(encoding="utf-8")
    old_vox, old_size = prefab_info(path) or ("", "")
    patched = re.sub(r"ed_filePath: .*", f"ed_filePath: {vox_path}", text, count=1)
    patched = re.sub(r"sizePerVox: .*", f"sizePerVox: {SIZE_PER_VOX}", patched, count=1)
    if patched != text:
        path.write_text(patched, encoding="utf-8", newline="\n")
    return {
        "prefab": str(path),
        "old_vox": old_vox,
        "new_vox": vox_path,
        "old_size_per_vox": old_size,
        "new_size_per_vox": SIZE_PER_VOX,
        "changed": patched != text,
    }


def add_eyes(m: VoxelModel, x: int, y: int, z0: int, z1: int) -> None:
    m.set(x, y, z0, "black")
    m.set(x, y, z1, "black")


def quadruped(name: str, body: str, accent: str = "wood_dark", muzzle: str = "cream") -> VoxelModel:
    m = VoxelModel(name, 26, 18, 14)
    m.box(7, 20, 7, 13, 3, 11, body)
    m.box(10, 19, 10, 15, 4, 10, body)
    m.box(2, 8, 10, 16, 4, 10, body)
    m.box(0, 4, 10, 14, 5, 9, muzzle)
    for x0, z0 in [(8, 3), (8, 9), (17, 3), (17, 9)]:
        m.box(x0, x0 + 2, 0, 8, z0, z0 + 2, body)
        m.box(x0, x0 + 2, 0, 2, z0, z0 + 2, accent)
    m.box(20, 25, 9, 12, 6, 8, accent)
    m.box(5, 7, 15, 18, 4, 6, accent)
    m.box(5, 7, 15, 18, 8, 10, accent)
    add_eyes(m, 2, 13, 4, 9)
    return m


def cow() -> VoxelModel:
    m = quadruped("cow", "cow", "black", "cream")
    m.box(11, 16, 11, 15, 3, 5, "black")
    m.box(16, 20, 8, 12, 8, 11, "black")
    m.box(5, 7, 16, 18, 3, 5, "cream")
    m.box(5, 7, 16, 18, 9, 11, "cream")
    return m


def tiger() -> VoxelModel:
    m = quadruped("tiger", "orange", "black", "cream")
    for x in range(8, 20, 3):
        m.box(x, x + 1, 12, 15, 3, 11, "black")
    return m


def deer() -> VoxelModel:
    m = quadruped("deer", "wood", "wood_dark", "cream")
    for z in (4, 9):
        m.box(4, 5, 17, 22, z, z + 1, "wood_dark")
        m.box(3, 6, 20, 21, z, z + 1, "wood_dark")
    m.height = 22
    return m


def wolf() -> VoxelModel:
    return quadruped("wolf", "wolf", "wolf_dark", "cream")


def fox() -> VoxelModel:
    m = quadruped("fox", "orange", "wood_dark", "cream")
    m.box(21, 26, 10, 14, 5, 9, "cream")
    return m


def monkey() -> VoxelModel:
    m = VoxelModel("monkey", 18, 24, 12)
    m.box(6, 12, 5, 15, 4, 8, "wood")
    m.box(5, 13, 15, 22, 3, 9, "wood")
    m.box(6, 12, 16, 20, 2, 10, "cream")
    m.box(3, 6, 14, 19, 3, 5, "wood_dark")
    m.box(12, 15, 14, 19, 7, 9, "wood_dark")
    m.box(6, 8, 0, 6, 4, 6, "wood_dark")
    m.box(10, 12, 0, 6, 6, 8, "wood_dark")
    m.box(12, 17, 7, 10, 5, 7, "wood_dark")
    add_eyes(m, 5, 18, 4, 8)
    return m


def squirrel() -> VoxelModel:
    m = quadruped("squirrel", "wood", "wood_dark", "cream")
    m.box(19, 24, 11, 22, 4, 10, "wood_dark")
    return m


def fish_asset(name: str, body: str, accent: str = "yellow") -> VoxelModel:
    m = VoxelModel(name, 22, 12, 10)
    m.ellipsoid(9.5, 6.0, 5.0, 7.0, 4.0, 3.5, body)
    m.box(16, 22, 4, 9, 3, 7, accent)
    m.box(2, 5, 6, 9, 4, 6, "cream")
    add_eyes(m, 2, 7, 4, 6)
    return m


def pufferfish() -> VoxelModel:
    m = VoxelModel("pufferfish", 18, 14, 12)
    m.ellipsoid(8.5, 7.0, 6.0, 7.0, 5.5, 5.0, "yellow")
    m.box(14, 18, 6, 9, 5, 7, "yellow_dark")
    add_eyes(m, 3, 8, 4, 8)
    return m


def eel() -> VoxelModel:
    m = VoxelModel("electric_eel", 28, 8, 8)
    m.box(2, 24, 3, 6, 3, 5, "water")
    m.box(24, 28, 4, 6, 3, 5, "water_dark")
    m.box(5, 22, 6, 7, 4, 5, "yellow")
    add_eyes(m, 2, 5, 3, 5)
    return m


def amphibian(name: str, body: str = "frog") -> VoxelModel:
    m = VoxelModel(name, 18, 10, 16)
    m.ellipsoid(8.5, 5.0, 8.0, 6.5, 4.0, 5.5, body)
    m.box(2, 6, 7, 10, 4, 7, body)
    m.box(2, 6, 7, 10, 9, 12, body)
    m.box(3, 5, 8, 10, 5, 6, "white")
    m.box(3, 5, 8, 10, 10, 11, "white")
    add_eyes(m, 3, 9, 5, 10)
    m.box(1, 6, 1, 4, 1, 4, body)
    m.box(1, 6, 1, 4, 12, 15, body)
    m.box(12, 18, 1, 4, 1, 4, body)
    m.box(12, 18, 1, 4, 12, 15, body)
    return m


def salamander() -> VoxelModel:
    m = VoxelModel("salamander", 24, 8, 10)
    m.ellipsoid(10, 4, 5, 8, 3, 3, "orange")
    m.box(2, 5, 4, 6, 4, 7, "orange")
    m.box(17, 24, 3, 5, 4, 6, "orange")
    for x in (6, 14):
        m.box(x, x + 3, 1, 3, 1, 3, "orange")
        m.box(x, x + 3, 1, 3, 7, 9, "orange")
    add_eyes(m, 2, 5, 4, 6)
    return m


def crab_like(name: str, body: str = "crab") -> VoxelModel:
    m = VoxelModel(name, 20, 8, 14)
    m.box(6, 14, 3, 7, 4, 10, body)
    for z in (2, 10):
        m.box(2, 7, 3, 6, z, z + 2, body)
        m.box(13, 18, 3, 6, z, z + 2, body)
    m.box(1, 4, 5, 8, 2, 5, body)
    m.box(16, 19, 5, 8, 9, 12, body)
    add_eyes(m, 6, 7, 5, 8)
    return m


def shrimp() -> VoxelModel:
    m = VoxelModel("shrimp", 20, 8, 10)
    for i in range(10):
        m.box(4 + i, 6 + i, 3, 7, 3, 7, "crab_light" if i % 2 else "crab")
    m.box(14, 20, 4, 6, 4, 6, "crab")
    add_eyes(m, 3, 6, 4, 6)
    return m


def jellyfish() -> VoxelModel:
    m = VoxelModel("jellyfish", 14, 16, 14)
    m.ellipsoid(7, 11, 7, 6, 4, 6, "wing")
    for x in (4, 6, 8, 10):
        m.box(x, x + 1, 0, 10, 6, 8, "cyan")
    return m


def coral() -> VoxelModel:
    m = VoxelModel("coral", 16, 14, 12)
    m.box(7, 9, 0, 12, 5, 7, "red")
    m.box(5, 11, 6, 8, 5, 8, "red")
    for x, y, z in [(4, 6, 5), (10, 7, 6), (5, 9, 4), (11, 10, 7)]:
        m.box(x, x + 4, y, y + 2, z, z + 2, "red_light")
        m.box(x, x + 2, y, y + 5, z, z + 2, "red")
    return m


def insect(name: str, body: str = "black", wing_color: str = "wing") -> VoxelModel:
    m = VoxelModel(name, 18, 8, 14)
    m.box(5, 14, 3, 6, 5, 9, body)
    m.box(2, 6, 4, 7, 5, 9, body)
    m.box(6, 13, 6, 8, 2, 6, wing_color)
    m.box(6, 13, 6, 8, 8, 12, wing_color)
    for x in (5, 9, 13):
        m.box(x, x + 1, 1, 4, 2, 5, body)
        m.box(x, x + 1, 1, 4, 9, 12, body)
    add_eyes(m, 2, 6, 5, 8)
    return m


def scorpion() -> VoxelModel:
    m = VoxelModel("scorpion", 24, 10, 14)
    m.box(6, 15, 3, 7, 4, 10, "wood_dark")
    m.box(2, 7, 4, 7, 5, 9, "wood_dark")
    m.box(15, 19, 5, 8, 5, 9, "wood_dark")
    m.box(18, 21, 7, 10, 6, 8, "wood_dark")
    m.box(20, 23, 8, 10, 5, 9, "black")
    m.box(0, 4, 5, 8, 2, 5, "wood_dark")
    m.box(0, 4, 5, 8, 9, 12, "wood_dark")
    return m


def plant(name: str, kind: str) -> VoxelModel:
    m = VoxelModel(name, 18, 24, 18)
    if kind == "grass":
        m.box(5, 13, 0, 1, 7, 11, "leaf_dark")
        for x, z, h in [(7, 7, 8), (9, 8, 11), (6, 10, 9), (11, 9, 7)]:
            m.box(x, x + 2, 0, h, z, z + 1, "leaf")
    elif kind == "reed":
        m.box(8, 10, 0, 22, 8, 10, "stem")
        m.box(7, 11, 19, 24, 8, 10, "sand_dark")
    elif kind == "vine":
        for y in range(0, 24, 3):
            x = 7 + (y // 3) % 4
            m.box(x, x + 2, y, min(24, y + 4), 8, 10, "stem")
            m.box(x - 2, x, y + 1, min(24, y + 3), 8, 10, "leaf")
    elif kind == "lotus":
        m.box(8, 10, 0, 8, 8, 10, "stem")
        m.box(6, 12, 7, 9, 6, 12, "leaf")
        for x, z in [(5, 8), (8, 5), (11, 8), (8, 11), (7, 7), (10, 10)]:
            m.box(x, x + 3, 7, 9, z, z + 3, "pink")
        m.box(8, 10, 8, 10, 8, 10, "yellow")
    elif kind == "sunflower":
        m.box(8, 10, 0, 18, 8, 10, "stem")
        m.box(5, 13, 17, 23, 7, 11, "yellow")
        m.box(7, 11, 18, 22, 8, 10, "wood_dark")
        m.box(6, 8, 8, 11, 7, 10, "leaf")
        m.box(10, 12, 10, 13, 8, 11, "leaf")
    elif kind == "mushroom":
        m.box(8, 11, 0, 8, 8, 11, "cream")
        m.ellipsoid(9, 10, 9, 6, 4, 6, "red")
        m.box(6, 8, 11, 13, 8, 10, "white")
        m.box(10, 12, 12, 14, 6, 8, "white")
    elif kind == "dandelion":
        m.box(8, 10, 0, 15, 8, 10, "stem")
        m.ellipsoid(9, 18, 9, 4, 4, 4, "yellow_light")
    elif kind == "moss":
        m.box(4, 14, 0, 3, 4, 14, "leaf_dark")
        m.box(6, 12, 2, 5, 6, 12, "leaf")
    return m


def cactus() -> VoxelModel:
    m = VoxelModel("cactus", 16, 24, 16)
    m.box(7, 10, 0, 22, 7, 10, "cactus")
    m.box(3, 8, 10, 13, 7, 10, "cactus")
    m.box(3, 6, 10, 18, 7, 10, "cactus")
    m.box(9, 14, 14, 17, 7, 10, "cactus")
    m.box(12, 14, 14, 21, 7, 10, "cactus")
    m.box(8, 9, 20, 22, 8, 9, "cactus_light")
    return m


def item(name: str, kind: str) -> VoxelModel:
    if kind == "egg":
        m = VoxelModel(name, 10, 14, 10)
        m.ellipsoid(5, 7, 5, 4, 6, 4, "cream")
        m.box(3, 5, 9, 11, 4, 6, "white")
        return m
    if kind == "pearl":
        m = VoxelModel(name, 10, 10, 10)
        m.ellipsoid(5, 5, 5, 4, 4, 4, "white")
        m.box(3, 5, 6, 8, 3, 5, "cyan")
        return m
    if kind == "coconut":
        m = VoxelModel(name, 12, 12, 12)
        m.ellipsoid(6, 6, 6, 5, 5, 5, "wood")
        m.box(4, 5, 8, 9, 4, 5, "wood_dark")
        m.box(7, 8, 8, 9, 6, 7, "wood_dark")
        return m
    if kind == "honey":
        m = VoxelModel(name, 14, 14, 12)
        m.box(4, 11, 0, 11, 3, 9, "yellow_dark")
        m.box(5, 10, 8, 14, 4, 8, "cream")
        m.box(10, 13, 4, 11, 5, 7, "yellow")
        return m
    if kind == "milk":
        m = VoxelModel(name, 10, 16, 8)
        m.box(2, 8, 0, 12, 2, 6, "white")
        m.box(3, 7, 12, 16, 3, 5, "cream")
        m.box(2, 8, 5, 8, 1, 2, "blue")
        return m
    if kind == "pottery":
        m = VoxelModel(name, 14, 16, 14)
        m.ellipsoid(7, 7, 7, 5, 7, 5, "sand_dark")
        m.box(4, 10, 12, 16, 4, 10, "sand")
        return m
    if kind == "rainbow":
        m = VoxelModel(name, 26, 18, 8)
        colors = ["red", "orange", "yellow", "leaf", "blue", "pink"]
        for i, color in enumerate(colors):
            m.box(3 + i, 23 - i, 4 + i, 6 + i, 3, 5, color)
        m.box(4, 8, 0, 5, 3, 5, "cloud")
        m.box(18, 22, 0, 5, 3, 5, "cloud")
        return m
    if kind == "steam":
        m = VoxelModel(name, 12, 20, 12)
        for y in range(0, 18, 3):
            x = 5 + (y // 3) % 3
            z = 5 + ((y // 3) + 1) % 3
            m.box(x, x + 2, y, y + 4, z, z + 2, "cloud")
        return m
    if kind == "wool":
        m = VoxelModel(name, 14, 12, 14)
        m.ellipsoid(7, 6, 7, 6, 5, 6, "white")
        m.box(5, 9, 8, 11, 5, 9, "cloud_shadow")
        return m
    raise ValueError(kind)


def bird(name: str, body: str, wing: str = "wing") -> VoxelModel:
    m = VoxelModel(name, 20, 12, 20)
    m.ellipsoid(9, 6, 10, 5, 4, 4, body)
    m.box(4, 7, 7, 10, 8, 12, body)
    m.box(1, 9, 6, 8, 3, 8, wing)
    m.box(1, 9, 6, 8, 12, 17, wing)
    m.box(14, 19, 5, 8, 8, 12, body)
    m.box(3, 5, 7, 8, 9, 11, "yellow")
    add_eyes(m, 4, 8, 8, 12)
    return m


def dinosaur(name: str) -> VoxelModel:
    m = VoxelModel(name, 34, 22, 14)
    m.box(8, 25, 6, 13, 4, 10, "dino")
    m.box(2, 9, 11, 18, 4, 10, "dino")
    m.box(0, 4, 13, 16, 5, 9, "dino_light")
    m.box(24, 33, 8, 11, 6, 8, "dino")
    for x in (10, 20):
        m.box(x, x + 3, 0, 7, 4, 6, "dino")
        m.box(x, x + 3, 0, 7, 8, 10, "dino")
    add_eyes(m, 2, 15, 5, 9)
    return m


def triceratops() -> VoxelModel:
    m = quadruped("triceratops", "dino", "dino_light", "dino_light")
    m.box(0, 4, 15, 17, 4, 5, "cream")
    m.box(0, 4, 15, 17, 9, 10, "cream")
    m.box(2, 4, 15, 20, 6, 8, "cream")
    m.height = 20
    return m


def plesiosaur() -> VoxelModel:
    m = VoxelModel("plesiosaur", 34, 14, 16)
    m.ellipsoid(17, 6, 8, 10, 4, 5, "water")
    m.box(2, 13, 7, 10, 7, 9, "water")
    m.box(0, 4, 9, 12, 6, 10, "water")
    m.box(26, 34, 5, 7, 7, 9, "water_dark")
    for x, z in [(11, 2), (20, 2), (11, 12), (20, 12)]:
        m.box(x, x + 5, 3, 5, z, z + 2, "water_dark")
    add_eyes(m, 0, 11, 6, 9)
    return m


BUILDERS = {
    "Bird": lambda: bird("bird", "stone", "wing"),
    "Cactus": cactus,
    "Cicada": lambda: insect("cicada", "wood_dark", "wing"),
    "Clownfish": lambda: fish_asset("clownfish", "orange", "white"),
    "Coconut": lambda: item("coconut", "coconut"),
    "Coral": coral,
    "Cow": cow,
    "Dandelion": lambda: plant("dandelion", "dandelion"),
    "Deer": deer,
    "Dinosaur": lambda: dinosaur("dinosaur"),
    "Dragonfly": lambda: insect("dragonfly", "blue", "wing"),
    "Eagle": lambda: bird("eagle", "wood_dark", "cream"),
    "Egg": lambda: item("egg", "egg"),
    "ElectricEel": eel,
    "Firefly": lambda: insect("firefly", "black", "yellow_light"),
    "Fly": lambda: insect("fly", "black", "wing"),
    "Fox": fox,
    "Grass": lambda: plant("grass", "grass"),
    "HermitCrab": lambda: crab_like("hermit_crab", "crab_light"),
    "Honey": lambda: item("honey", "honey"),
    "Hummingbird": lambda: bird("hummingbird", "leaf", "cyan"),
    "Jellyfish": jellyfish,
    "Lotus": lambda: plant("lotus", "lotus"),
    "Milk": lambda: item("milk", "milk"),
    "Monkey": monkey,
    "Moss": lambda: plant("moss", "moss"),
    "Pearl": lambda: item("pearl", "pearl"),
    "Plesiosaur": plesiosaur,
    "PoisonMushroom": lambda: plant("poison_mushroom", "mushroom"),
    "Pottery": lambda: item("pottery", "pottery"),
    "Pufferfish": pufferfish,
    "Rainbow": lambda: item("rainbow", "rainbow"),
    "Reed": lambda: plant("reed", "reed"),
    "Salamander": salamander,
    "Scorpion": scorpion,
    "Shrimp": shrimp,
    "Squirrel": squirrel,
    "Steam": lambda: item("steam", "steam"),
    "Sunflower": lambda: plant("sunflower", "sunflower"),
    "Swallow": lambda: bird("swallow", "blue", "white"),
    "Tiger": tiger,
    "Toad": lambda: amphibian("toad", "frog"),
    "TreeFrog": lambda: amphibian("tree_frog", "frog_light"),
    "Triceratops": triceratops,
    "Vine": lambda: plant("vine", "vine"),
    "Wolf": wolf,
    "Wool": lambda: item("wool", "wool"),
}


def model_report(path: Path) -> dict:
    model = read_vox(path)
    comps = components(model["voxels"].keys())
    sizes = sorted((len(comp) for comp in comps), reverse=True)
    return {
        "size": model["size"],
        "voxel_count": len(model["voxels"]),
        "single_connected_component": len(comps) == 1,
        "floating_component_sizes": sizes[1:],
    }


def build_or_copy(entity: str, out_path: Path) -> str:
    reuse = REUSE_SOURCES.get(entity)
    if reuse and reuse.exists():
        shutil.copyfile(reuse, out_path)
        return str(reuse.relative_to(ROOT)).replace("\\", "/")
    builder = BUILDERS.get(entity)
    if builder is None:
        raise KeyError(f"no legacy-regen builder for {entity}")
    write_vox(out_path, builder())
    return "procedural_legacy_regen_template"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    args = parser.parse_args()

    project = Path(args.project).resolve()
    prefab_dir = project / "Assets" / "Resources" / "LittleWorld" / "Entities"
    out_dir = project / "Assets" / "Voxel" / "legacy_regen"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    integration: list[dict] = []
    failures: list[str] = []

    for prefab in sorted(prefab_dir.glob("Entity_*.prefab")):
        info = prefab_info(prefab)
        if not info:
            continue
        old_vox, old_size = info
        if old_size == SIZE_PER_VOX and not old_vox.startswith("Assets/Voxel/legacy_regen/"):
            continue
        entity = prefab.stem.replace("Entity_", "")
        out_name = f"{snake_name(entity)}.vox"
        out_path = out_dir / out_name
        try:
            source = build_or_copy(entity, out_path)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{entity}: {exc}")
            continue
        report = model_report(out_path)
        vox_rel = f"Assets/Voxel/legacy_regen/{out_name}"
        integration.append({"entity": entity, **patch_prefab(prefab, vox_rel), "source": source, **report})
        manifest.append(
            {
                "name": snake_name(entity),
                "path": vox_rel,
                "source": source,
                "cell_resolution": 64,
                "size": report["size"],
                "voxel_count": report["voxel_count"],
                "single_connected_component": report["single_connected_component"],
                "floating_component_sizes": report["floating_component_sizes"],
            }
        )

    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "game_integration_report.json").write_text(
        json.dumps({"updated": integration, "failures": failures}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Updated {len(integration)} legacy prefabs into {out_dir}")
    if failures:
        for failure in failures:
            print(f"FAILED {failure}")
        raise SystemExit(1)
    bad = [item for item in integration if not item["single_connected_component"] or item["floating_component_sizes"]]
    if bad:
        for item in bad:
            print(f"CHECK FAILED {item['entity']}: components/floating issue")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
