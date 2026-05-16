#!/usr/bin/env python3
"""VOX loading and structural validation helpers."""

from __future__ import annotations

import struct
from collections import deque
from pathlib import Path
from typing import Iterable

from .model import COLORS

COLOR_NAMES = {rgba: name for name, rgba in COLORS.items()}


def chunk_id(data: bytes, offset: int) -> str:
    return data[offset : offset + 4].decode("ascii")


def read_vox(path: Path) -> dict:
    data = path.read_bytes()
    if data[:4] != b"VOX ":
        raise ValueError(f"{path} is not a VOX file")

    size = [0, 0, 0]
    voxels: list[tuple[int, int, int, int]] = []
    palette: list[tuple[int, int, int, int]] = []

    def walk(offset: int, end: int) -> None:
        nonlocal size, voxels, palette
        while offset < end:
            cid = chunk_id(data, offset)
            content_size, children_size = struct.unpack_from("<II", data, offset + 4)
            content_start = offset + 12
            content_end = content_start + content_size
            children_end = content_end + children_size
            if cid == "SIZE":
                width, depth, height = struct.unpack_from("<III", data, content_start)
                size = [width, height, depth]
            elif cid == "XYZI":
                count = struct.unpack_from("<I", data, content_start)[0]
                pos = content_start + 4
                voxels = []
                for _ in range(count):
                    x, z, y, color_index = struct.unpack_from("BBBB", data, pos)
                    voxels.append((x, y, z, color_index))
                    pos += 4
            elif cid == "RGBA":
                palette = [struct.unpack_from("BBBB", data, content_start + i * 4) for i in range(256)]
            if children_size:
                walk(content_end, children_end)
            offset = children_end

    walk(8, len(data))
    named_voxels: dict[tuple[int, int, int], str] = {}
    for x, y, z, color_index in voxels:
        rgba = palette[color_index - 1]
        named_voxels[(x, y, z)] = COLOR_NAMES.get(rgba, f"rgba{rgba}")
    return {"path": str(path), "size": size, "voxels": named_voxels}


def components(points: Iterable[tuple[int, ...]]) -> list[set[tuple[int, ...]]]:
    remaining = set(points)
    result: list[set[tuple[int, ...]]] = []
    while remaining:
        start = remaining.pop()
        comp = {start}
        queue = deque([start])
        while queue:
            point = queue.popleft()
            for axis in range(len(point)):
                for step in (-1, 1):
                    neighbor = list(point)
                    neighbor[axis] += step
                    candidate = tuple(neighbor)
                    if candidate in remaining:
                        remaining.remove(candidate)
                        comp.add(candidate)
                        queue.append(candidate)
        result.append(comp)
    return result


def color_points(model: dict, names: set[str]) -> set[tuple[int, int, int]]:
    return {pos for pos, color in model["voxels"].items() if color in names}


def assert_single_component(model: dict) -> tuple[bool, list[int]]:
    comps = components(model["voxels"].keys())
    sizes = sorted((len(comp) for comp in comps), reverse=True)
    return len(comps) == 1, sizes
