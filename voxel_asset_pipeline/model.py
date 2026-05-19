#!/usr/bin/env python3
"""Core voxel model, VOX writer, and simple isometric renderer."""
from __future__ import annotations

import struct
import zlib
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path


COLORS = {
    "soil_dark": (84, 55, 34, 255),
    "soil": (124, 82, 48, 255),
    "soil_light": (162, 111, 64, 255),
    "water_dark": (35, 96, 170, 255),
    "water": (51, 148, 218, 255),
    "water_light": (104, 205, 245, 255),
    "stone_dark": (76, 83, 92, 255),
    "stone": (118, 129, 140, 255),
    "stone_light": (166, 177, 184, 255),
    "sand_dark": (176, 130, 63, 255),
    "sand": (221, 180, 89, 255),
    "sand_light": (246, 216, 134, 255),
    "mud_dark": (66, 52, 44, 255),
    "mud": (103, 75, 55, 255),
    "humus_dark": (45, 67, 38, 255),
    "humus": (80, 105, 52, 255),
    "humus_light": (130, 154, 73, 255),
    "leaf_dark": (45, 112, 48, 255),
    "leaf": (72, 173, 67, 255),
    "leaf_light": (130, 219, 91, 255),
    "stem": (77, 134, 52, 255),
    "wood_dark": (91, 57, 36, 255),
    "wood": (143, 89, 48, 255),
    "red": (219, 62, 70, 255),
    "red_light": (246, 102, 102, 255),
    "pink": (238, 111, 161, 255),
    "pig_body": (255, 160, 168, 255),
    "pig_body_light": (255, 160, 176, 255),
    "pig_shadow": (240, 128, 144, 255),
    "pig_dark": (232, 104, 128, 255),
    "pig_deep": (184, 48, 80, 255),
    "pig_black": (40, 40, 40, 255),
    "yellow": (247, 201, 68, 255),
    "yellow_light": (255, 228, 96, 255),
    "yellow_dark": (214, 148, 39, 255),
    "orange": (236, 133, 50, 255),
    "cream": (245, 225, 178, 255),
    "white": (242, 244, 235, 255),
    "gray": (143, 151, 156, 255),
    "black": (31, 34, 38, 255),
    "blue": (59, 142, 214, 255),
    "cyan": (117, 220, 224, 255),
    "wing": (184, 230, 241, 255),
    "frog": (75, 172, 76, 255),
    "frog_light": (139, 220, 91, 255),
    "crab": (211, 72, 58, 255),
    "crab_light": (239, 111, 82, 255),
    "cactus": (54, 150, 87, 255),
    "cactus_light": (91, 199, 116, 255),
    "cloud": (232, 239, 245, 255),
    "cloud_shadow": (185, 204, 215, 255),
    "cow": (238, 232, 207, 255),
    "wolf": (110, 119, 126, 255),
    "wolf_dark": (68, 76, 86, 255),
    "dino": (77, 155, 117, 255),
    "dino_light": (113, 200, 143, 255),
}


@dataclass
class VoxelModel:
    name: str
    width: int
    height: int
    depth: int

    def __post_init__(self) -> None:
        self.voxels: dict[tuple[int, int, int], str] = {}

    def set(self, x: int, y: int, z: int, color: str) -> None:
        if 0 <= x < self.width and 0 <= y < self.height and 0 <= z < self.depth:
            self.voxels[(x, y, z)] = color

    def box(
        self,
        x0: int,
        x1: int,
        y0: int,
        y1: int,
        z0: int,
        z1: int,
        color: str,
    ) -> None:
        for x in range(x0, x1):
            for y in range(y0, y1):
                for z in range(z0, z1):
                    self.set(x, y, z, color)

    def ellipsoid(
        self,
        cx: float,
        cy: float,
        cz: float,
        rx: float,
        ry: float,
        rz: float,
        color: str,
    ) -> None:
        x0 = int(cx - rx - 1)
        x1 = int(cx + rx + 2)
        y0 = int(cy - ry - 1)
        y1 = int(cy + ry + 2)
        z0 = int(cz - rz - 1)
        z1 = int(cz + rz + 2)
        for x in range(x0, x1):
            for y in range(y0, y1):
                for z in range(z0, z1):
                    dx = (x + 0.5 - cx) / max(rx, 0.1)
                    dy = (y + 0.5 - cy) / max(ry, 0.1)
                    dz = (z + 0.5 - cz) / max(rz, 0.1)
                    if dx * dx + dy * dy + dz * dz <= 1.0:
                        self.set(x, y, z, color)

    def outline_bottom(self, color: str) -> None:
        for x in range(self.width):
            for z in range(self.depth):
                if x in (0, self.width - 1) or z in (0, self.depth - 1):
                    self.set(x, 0, z, color)


def model(name: str, w: int, h: int, d: int) -> VoxelModel:
    return VoxelModel(name, w, h, d)



def chunk(chunk_id: bytes, content: bytes = b"", children: bytes = b"") -> bytes:
    return chunk_id + struct.pack("<II", len(content), len(children)) + content + children


def write_vox(path: Path, m: VoxelModel) -> None:
    color_order: OrderedDict[str, int] = OrderedDict()
    for color in m.voxels.values():
        if color not in color_order:
            color_order[color] = len(color_order) + 1

    if len(color_order) > 255:
        raise ValueError(f"{m.name} uses too many colors: {len(color_order)}")

    size_content = struct.pack("<III", m.width, m.depth, m.height)
    voxel_items = sorted(m.voxels.items(), key=lambda item: (item[0][1], item[0][2], item[0][0]))
    xyzi_content = struct.pack("<I", len(voxel_items))
    for (x, y, z), color in voxel_items:
        xyzi_content += struct.pack("BBBB", x, z, y, color_order[color])

    palette = bytearray()
    ordered_names = list(color_order.keys())
    for i in range(256):
        if i < len(ordered_names):
            palette.extend(COLORS[ordered_names[i]])
        else:
            palette.extend((0, 0, 0, 255))

    children = (
        chunk(b"SIZE", size_content)
        + chunk(b"XYZI", xyzi_content)
        + chunk(b"RGBA", bytes(palette))
    )
    data = b"VOX " + struct.pack("<I", 150) + chunk(b"MAIN", b"", children)
    path.write_bytes(data)


def shade(color_name: str, factor: float) -> str:
    r, g, b, _ = COLORS[color_name]
    return f"#{min(255, int(r * factor)):02x}{min(255, int(g * factor)):02x}{min(255, int(b * factor)):02x}"


def opacity(color_name: str) -> float:
    return COLORS[color_name][3] / 255.0


def iso_point(x: float, y: float, z: float, scale: float) -> tuple[float, float]:
    return ((x - z) * scale, (x + z) * scale * 0.5 - y * scale)


def poly(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in points)


def render_voxel_faces(m: VoxelModel, scale: float, tx: float, ty: float) -> list[str]:
    voxels = m.voxels
    lines: list[str] = []

    def p(x: float, y: float, z: float) -> tuple[float, float]:
        px, py = iso_point(x, y, z, scale)
        return px + tx, py + ty

    # Back-to-front order for a fixed isometric camera.
    ordered = sorted(voxels.items(), key=lambda item: (item[0][0] + item[0][2], item[0][1]))
    for (x, y, z), color in ordered:
        a = opacity(color)
        alpha = f' fill-opacity="{a:.2f}"' if a < 1.0 else ""
        if (x, y + 1, z) not in voxels:
            pts = [p(x, y + 1, z), p(x + 1, y + 1, z), p(x + 1, y + 1, z + 1), p(x, y + 1, z + 1)]
            lines.append(f'<polygon points="{poly(pts)}" fill="{shade(color, 1.12)}"{alpha}/>')
        if (x + 1, y, z) not in voxels:
            pts = [p(x + 1, y, z), p(x + 1, y, z + 1), p(x + 1, y + 1, z + 1), p(x + 1, y + 1, z)]
            lines.append(f'<polygon points="{poly(pts)}" fill="{shade(color, 0.86)}"{alpha}/>')
        if (x, y, z + 1) not in voxels:
            pts = [p(x, y, z + 1), p(x + 1, y, z + 1), p(x + 1, y + 1, z + 1), p(x, y + 1, z + 1)]
            lines.append(f'<polygon points="{poly(pts)}" fill="{shade(color, 0.72)}"{alpha}/>')
    return lines


def iter_face_polygons(
    m: VoxelModel, scale: float, tx: float, ty: float
) -> list[tuple[list[tuple[float, float]], tuple[int, int, int, int], float]]:
    voxels = m.voxels
    faces = []

    def p(x: float, y: float, z: float) -> tuple[float, float]:
        px, py = iso_point(x, y, z, scale)
        return px + tx, py + ty

    ordered = sorted(voxels.items(), key=lambda item: (item[0][0] + item[0][2], item[0][1]))
    for (x, y, z), color in ordered:
        rgba = COLORS[color]
        if (x, y + 1, z) not in voxels:
            pts = [p(x, y + 1, z), p(x + 1, y + 1, z), p(x + 1, y + 1, z + 1), p(x, y + 1, z + 1)]
            faces.append((pts, rgba, 1.12))
        if (x + 1, y, z) not in voxels:
            pts = [p(x + 1, y, z), p(x + 1, y, z + 1), p(x + 1, y + 1, z + 1), p(x + 1, y + 1, z)]
            faces.append((pts, rgba, 0.86))
        if (x, y, z + 1) not in voxels:
            pts = [p(x, y, z + 1), p(x + 1, y, z + 1), p(x + 1, y + 1, z + 1), p(x, y + 1, z + 1)]
            faces.append((pts, rgba, 0.72))
    return faces


def point_in_poly(px: float, py: float, points: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(points) - 1
    for i in range(len(points)):
        xi, yi = points[i]
        xj, yj = points[j]
        crosses = (yi > py) != (yj > py)
        if crosses:
            x_intersect = (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi
            if px < x_intersect:
                inside = not inside
        j = i
    return inside


def blend(dst: tuple[int, int, int, int], src: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    sr, sg, sb, sa = src
    dr, dg, db, da = dst
    a = sa / 255.0
    inv = 1.0 - a
    return (
        int(sr * a + dr * inv),
        int(sg * a + dg * inv),
        int(sb * a + db * inv),
        255,
    )


def draw_polygon(
    pixels: list[tuple[int, int, int, int]],
    width: int,
    height: int,
    points: list[tuple[float, float]],
    rgba: tuple[int, int, int, int],
    factor: float,
) -> None:
    r, g, b, a = rgba
    src = (min(255, int(r * factor)), min(255, int(g * factor)), min(255, int(b * factor)), a)
    min_x = max(0, int(min(x for x, _ in points)) - 1)
    max_x = min(width - 1, int(max(x for x, _ in points)) + 1)
    min_y = max(0, int(min(y for _, y in points)) - 1)
    max_y = min(height - 1, int(max(y for _, y in points)) + 1)
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            if point_in_poly(x + 0.5, y + 0.5, points):
                idx = y * width + x
                pixels[idx] = blend(pixels[idx], src)


def write_png(path: Path, width: int, height: int, pixels: list[tuple[int, int, int, int]]) -> None:
    def png_chunk(name: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)

    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            raw.extend(pixels[y * width + x])

    png = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + png_chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def render_preview_png(models: list[VoxelModel], path: Path) -> None:
    cols = 6
    rows = 4
    cell_w = 210
    cell_h = 190
    width = cols * cell_w
    height = rows * cell_h
    scale = 5.0
    bg = (244, 241, 233, 255)
    pixels = [bg for _ in range(width * height)]

    for i, m in enumerate(models):
        col = i % cols
        row = i // cols
        cx = col * cell_w + cell_w * 0.5
        baseline = row * cell_h + cell_h * 0.72
        model_center_x = (m.width - m.depth) * scale * 0.5
        model_center_y = (m.width + m.depth) * scale * 0.25 - m.height * scale * 0.5
        tx = cx - model_center_x
        ty = baseline - model_center_y
        for pts, rgba, factor in iter_face_polygons(m, scale, tx, ty):
            draw_polygon(pixels, width, height, pts, rgba, factor)

    write_png(path, width, height, pixels)


def render_preview_svg(models: list[VoxelModel], path: Path) -> None:
    cols = 6
    rows = 4
    cell_w = 210
    cell_h = 190
    width = cols * cell_w
    height = rows * cell_h
    scale = 5.0

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f4f1e9"/>',
        '<style>text{font:12px Arial, sans-serif;fill:#606060}</style>',
    ]

    for i, m in enumerate(models):
        col = i % cols
        row = i // cols
        cx = col * cell_w + cell_w * 0.5
        baseline = row * cell_h + cell_h * 0.72
        model_center_x = (m.width - m.depth) * scale * 0.5
        model_center_y = (m.width + m.depth) * scale * 0.25 - m.height * scale * 0.5
        tx = cx - model_center_x
        ty = baseline - model_center_y
        lines.extend(render_voxel_faces(m, scale, tx, ty))
        lines.append(f'<text x="{col * cell_w + 12}" y="{row * cell_h + cell_h - 16}">{m.name}</text>')

    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")

