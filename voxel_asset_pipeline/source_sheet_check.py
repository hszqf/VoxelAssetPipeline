#!/usr/bin/env python3
"""Check AI source sheets before voxel geometry is created.

This checker is intentionally mechanical. It does not try to understand an
animal or prop semantically; it only verifies layout, rough silhouette bounds,
and orthographic registration signals that are easy to miss by eye.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import statistics
import struct
import sys
import zlib


RGBA = tuple[int, int, int, int]


@dataclass(frozen=True)
class Frame:
    x: int
    y: int
    w: int
    h: int

    def inner(self, margin: int) -> "Frame":
        return Frame(self.x + margin, self.y + margin, max(1, self.w - margin * 2), max(1, self.h - margin * 2))


@dataclass(frozen=True)
class Bounds:
    x0: float
    y0: float
    x1: float
    y1: float
    grid_size: float = 64.0

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def bottom_gap(self) -> float:
        return self.grid_size - self.y1


def paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def read_png_rgba(path: Path) -> tuple[int, int, list[RGBA]]:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"{path} is not a PNG file")

    pos = 8
    width = height = bit_depth = color_type = interlace = None
    idat = bytearray()
    while pos < len(data):
        if pos + 8 > len(data):
            raise ValueError("truncated PNG chunk header")
        size = struct.unpack(">I", data[pos : pos + 4])[0]
        name = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + size]
        pos += 12 + size
        if name == b"IHDR":
            width, height, bit_depth, color_type, _compression, _filter, interlace = struct.unpack(">IIBBBBB", chunk)
        elif name == b"IDAT":
            idat.extend(chunk)
        elif name == b"IEND":
            break

    if width is None or height is None or bit_depth is None or color_type is None or interlace is None:
        raise ValueError("missing PNG IHDR")
    if bit_depth != 8:
        raise ValueError(f"unsupported PNG bit depth {bit_depth}; save as 8-bit PNG")
    if interlace != 0:
        raise ValueError("interlaced PNG is not supported")

    channels_by_type = {0: 1, 2: 3, 4: 2, 6: 4}
    if color_type not in channels_by_type:
        raise ValueError(f"unsupported PNG color type {color_type}; use RGB or RGBA PNG")
    channels = channels_by_type[color_type]
    stride = width * channels
    raw = zlib.decompress(bytes(idat))
    rows: list[bytearray] = []
    prev = bytearray(stride)
    src = 0
    for _y in range(height):
        filter_type = raw[src]
        src += 1
        row = bytearray(raw[src : src + stride])
        src += stride
        for i in range(stride):
            left = row[i - channels] if i >= channels else 0
            up = prev[i]
            up_left = prev[i - channels] if i >= channels else 0
            if filter_type == 0:
                recon = row[i]
            elif filter_type == 1:
                recon = (row[i] + left) & 0xFF
            elif filter_type == 2:
                recon = (row[i] + up) & 0xFF
            elif filter_type == 3:
                recon = (row[i] + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                recon = (row[i] + paeth(left, up, up_left)) & 0xFF
            else:
                raise ValueError(f"unsupported PNG filter type {filter_type}")
            row[i] = recon
        rows.append(row)
        prev = row

    pixels: list[RGBA] = []
    for row in rows:
        for x in range(width):
            off = x * channels
            if color_type == 0:
                v = row[off]
                pixels.append((v, v, v, 255))
            elif color_type == 2:
                pixels.append((row[off], row[off + 1], row[off + 2], 255))
            elif color_type == 4:
                v = row[off]
                pixels.append((v, v, v, row[off + 1]))
            else:
                pixels.append((row[off], row[off + 1], row[off + 2], row[off + 3]))
    return width, height, pixels


def luminance(p: RGBA) -> float:
    return 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]


def saturation(p: RGBA) -> float:
    mx = max(p[0], p[1], p[2])
    mn = min(p[0], p[1], p[2])
    return 0.0 if mx == 0 else (mx - mn) / mx


def rgb_distance(a: RGBA, b: RGBA) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def grid_like_pixel(p: RGBA) -> bool:
    if p[3] < 32:
        return False
    mx = max(p[0], p[1], p[2])
    mn = min(p[0], p[1], p[2])
    lum = luminance(p)
    return mx - mn <= 30 and 70 <= lum <= 238


def detect_grid_frames(width: int, height: int, pixels: list[RGBA]) -> list[Frame]:
    mask = bytearray(width * height)
    for i, p in enumerate(pixels):
        if grid_like_pixel(p):
            mask[i] = 1

    visited = bytearray(width * height)
    components: list[tuple[int, Frame]] = []
    for start, value in enumerate(mask):
        if not value or visited[start]:
            continue
        stack = [start]
        visited[start] = 1
        count = 0
        min_x = width
        max_x = 0
        min_y = height
        max_y = 0
        while stack:
            idx = stack.pop()
            count += 1
            x = idx % width
            y = idx // width
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
            if x > 0:
                nxt = idx - 1
                if mask[nxt] and not visited[nxt]:
                    visited[nxt] = 1
                    stack.append(nxt)
            if x < width - 1:
                nxt = idx + 1
                if mask[nxt] and not visited[nxt]:
                    visited[nxt] = 1
                    stack.append(nxt)
            if y > 0:
                nxt = idx - width
                if mask[nxt] and not visited[nxt]:
                    visited[nxt] = 1
                    stack.append(nxt)
            if y < height - 1:
                nxt = idx + width
                if mask[nxt] and not visited[nxt]:
                    visited[nxt] = 1
                    stack.append(nxt)

        frame = Frame(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
        if frame.w < 80 or frame.h < 80:
            continue
        aspect = frame.w / frame.h
        density = count / max(1, frame.w * frame.h)
        if 0.65 <= aspect <= 1.35 and 0.015 <= density <= 0.95:
            components.append((count, frame))

    # Grid borders and dense grid interiors can appear as separate nested
    # components. Merge strongly overlapping candidates into one panel.
    frames: list[Frame] = []
    for _count, frame in sorted(components, key=lambda item: (item[1].x, item[1].y)):
        merged = False
        for i, existing in enumerate(frames):
            ix0 = max(frame.x, existing.x)
            iy0 = max(frame.y, existing.y)
            ix1 = min(frame.x + frame.w, existing.x + existing.w)
            iy1 = min(frame.y + frame.h, existing.y + existing.h)
            if ix1 <= ix0 or iy1 <= iy0:
                continue
            intersection = (ix1 - ix0) * (iy1 - iy0)
            smaller = min(frame.w * frame.h, existing.w * existing.h)
            if intersection / max(1, smaller) >= 0.60:
                x0 = min(frame.x, existing.x)
                y0 = min(frame.y, existing.y)
                x1 = max(frame.x + frame.w, existing.x + existing.w)
                y1 = max(frame.y + frame.h, existing.y + existing.h)
                frames[i] = Frame(x0, y0, x1 - x0, y1 - y0)
                merged = True
                break
        if not merged:
            frames.append(frame)

    # If there are extra square grids, the orthographic panels are usually the
    # rightmost three.
    if len(frames) > 3:
        frames = sorted(frames, key=lambda frame: frame.x)[-3:]
    return sorted(frames, key=lambda frame: frame.x)


def parse_frame(value: str) -> Frame:
    parts = [int(part.strip()) for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("frame must be x,y,w,h")
    return Frame(*parts)


def parse_dims(value: str) -> tuple[float, float]:
    normalized = value.lower().replace(" ", "")
    sep = "x" if "x" in normalized else ","
    parts = [float(part) for part in normalized.split(sep)]
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("dimension must be AxB, for example 40x32")
    return parts[0], parts[1]


def estimate_background(frame: Frame, width: int, pixels: list[RGBA]) -> RGBA:
    samples: list[RGBA] = []
    for y in range(frame.y, frame.y + frame.h):
        for x in range(frame.x, frame.x + frame.w):
            p = pixels[y * width + x]
            if p[3] >= 128 and luminance(p) >= 220 and saturation(p) <= 0.08:
                samples.append(p)
    if not samples:
        return (255, 255, 255, 255)
    rs = sorted(p[0] for p in samples)
    gs = sorted(p[1] for p in samples)
    bs = sorted(p[2] for p in samples)
    # Empty grid background is usually the brightest low-saturation color,
    # while grid lines are also low-saturation but darker and more frequent.
    idx = min(len(samples) - 1, int(len(samples) * 0.90))
    return (rs[idx], gs[idx], bs[idx], 255)


def near_cell_line(frame: Frame, x: int, y: int, grid_size: float) -> bool:
    cell_w = frame.w / grid_size
    cell_h = frame.h / grid_size
    cx = (x - frame.x) / cell_w
    cy = (y - frame.y) / cell_h
    dx = abs(cx - round(cx)) * cell_w
    dy = abs(cy - round(cy)) * cell_h
    return dx <= 1.15 or dy <= 1.15


def guide_color(p: RGBA) -> str | None:
    r, g, b, a = p
    if a < 128:
        return None
    if b > r + 60 and b > g + 35 and b > 130:
        return "blue"
    if g > r + 45 and g > b + 45 and g > 120:
        return "green"
    if r > g + 60 and r > b + 60 and r > 140:
        return "red"
    return None


def colored_annotation_check(frame: Frame, width: int, pixels: list[RGBA]) -> dict:
    row_counts = [0 for _ in range(frame.h)]
    col_counts = [0 for _ in range(frame.w)]
    total = 0
    by_color = {"red": 0, "green": 0, "blue": 0}
    for yy in range(frame.h):
        y = frame.y + yy
        for xx in range(frame.w):
            x = frame.x + xx
            color = guide_color(pixels[y * width + x])
            if color is None:
                continue
            row_counts[yy] += 1
            col_counts[xx] += 1
            by_color[color] += 1
            total += 1
    longest_row = max(row_counts) if row_counts else 0
    longest_col = max(col_counts) if col_counts else 0
    line_like = longest_row > frame.w * 0.18 or longest_col > frame.h * 0.18
    too_many = total > frame.w * frame.h * 0.006
    return {
        "pass": not (line_like or too_many),
        "actual": {
            "colored_pixels": total,
            "by_color": by_color,
            "longest_row": longest_row,
            "longest_col": longest_col,
        },
        "expected": "no red/green/blue dimension or axis annotations inside grid",
    }


def line_group_count(scores: list[int], threshold: float) -> int:
    count = 0
    in_group = False
    for score in scores:
        is_line = score >= threshold
        if is_line and not in_group:
            count += 1
            in_group = True
        elif not is_line:
            in_group = False
    return count


def grid_resolution_check(frame: Frame, width: int, pixels: list[RGBA]) -> dict:
    vertical_scores = [0 for _ in range(frame.w)]
    horizontal_scores = [0 for _ in range(frame.h)]
    for yy in range(frame.h):
        y = frame.y + yy
        for xx in range(frame.w):
            x = frame.x + xx
            if grid_like_pixel(pixels[y * width + x]):
                vertical_scores[xx] += 1
                horizontal_scores[yy] += 1
    vertical_base = statistics.median(vertical_scores)
    horizontal_base = statistics.median(horizontal_scores)
    vertical_peak = max(vertical_scores) if vertical_scores else 0
    horizontal_peak = max(horizontal_scores) if horizontal_scores else 0
    vertical_threshold = max(8, vertical_base + (vertical_peak - vertical_base) * 0.45)
    horizontal_threshold = max(8, horizontal_base + (horizontal_peak - horizontal_base) * 0.45)
    vertical_lines = line_group_count(vertical_scores, vertical_threshold)
    horizontal_lines = line_group_count(horizontal_scores, horizontal_threshold)
    return {
        "actual": {
            "vertical_lines": vertical_lines,
            "horizontal_lines": horizontal_lines,
            "frame_size": [frame.w, frame.h],
            "vertical_threshold": round(vertical_threshold, 1),
            "horizontal_threshold": round(horizontal_threshold, 1),
        },
        "expected": "about 65 vertical and 65 horizontal grid lines for a 64x64 guide",
    }


def estimate_object_bounds(frame: Frame, width: int, pixels: list[RGBA], grid_size: float) -> Bounds | None:
    inner = frame.inner(5)
    bg = estimate_background(inner, width, pixels)
    object_points: list[tuple[int, int]] = []
    for y in range(inner.y, inner.y + inner.h):
        for x in range(inner.x, inner.x + inner.w):
            p = pixels[y * width + x]
            if p[3] < 64:
                continue
            lum = luminance(p)
            sat = saturation(p)
            dist = rgb_distance(p, bg)
            if rgb_distance(p, bg) < 18:
                continue
            if near_cell_line(frame, x, y, grid_size) and sat < 0.18 and lum > 95:
                continue
            if dist >= 24 or sat >= 0.08 or lum <= 175:
                object_points.append((x, y))
    if not object_points:
        return None
    min_x = min(x for x, _y in object_points)
    max_x = max(x for x, _y in object_points)
    min_y = min(y for _x, y in object_points)
    max_y = max(y for _x, y in object_points)
    x0 = (min_x - frame.x) / frame.w * grid_size
    x1 = (max_x + 1 - frame.x) / frame.w * grid_size
    y0 = (min_y - frame.y) / frame.h * grid_size
    y1 = (max_y + 1 - frame.y) / frame.h * grid_size
    return Bounds(x0, y0, x1, y1, grid_size)


def add_check(checks: list[dict], check_id: str, actual, expected, passed: bool) -> None:
    checks.append({"id": check_id, "pass": bool(passed), "expected": expected, "actual": actual})


def within(actual: float, expected: float, tolerance: float) -> bool:
    return expected - tolerance <= actual <= expected + tolerance


def rounded_bounds(bounds: Bounds | None) -> dict | None:
    if bounds is None:
        return None
    return {
        "x0": round(bounds.x0, 1),
        "y0": round(bounds.y0, 1),
        "x1": round(bounds.x1, 1),
        "y1": round(bounds.y1, 1),
        "width": round(bounds.width, 1),
        "height": round(bounds.height, 1),
        "bottom_gap": round(bounds.bottom_gap, 1),
    }


def run_check(args: argparse.Namespace) -> dict:
    path = Path(args.image)
    width, height, pixels = read_png_rgba(path)
    if args.side_frame and args.front_frame and args.top_frame:
        frames = [args.side_frame, args.front_frame, args.top_frame]
        frame_source = "explicit"
    else:
        frames = detect_grid_frames(width, height, pixels)
        frame_source = "auto"

    checks: list[dict] = []
    add_check(checks, "png_readable", f"{width}x{height}", "readable 8-bit RGB/RGBA PNG", True)
    add_check(checks, "orthographic_frame_count", len(frames), 3, len(frames) == 3)

    report: dict = {
        "asset": args.asset,
        "image": str(path),
        "image_size": [width, height],
        "frame_source": frame_source,
        "frames": {},
        "observed": {},
        "checks": checks,
    }

    if len(frames) != 3:
        report["pass"] = False
        return report

    names = ["side", "front", "top"]
    expected_grid_lines = int(round(args.grid_size)) + 1
    targets = {
        "side": args.side,
        "front": args.front,
        "top": args.top,
    }
    bounds: dict[str, Bounds | None] = {}
    for name, frame in zip(names, frames, strict=True):
        report["frames"][name] = {"x": frame.x, "y": frame.y, "w": frame.w, "h": frame.h}
        grid_resolution = grid_resolution_check(frame, width, pixels)
        line_tol = args.grid_line_tolerance
        add_check(
            checks,
            f"{name}_grid_resolution",
            grid_resolution["actual"],
            f"about {expected_grid_lines} vertical and {expected_grid_lines} horizontal grid lines for a {args.grid_size:g}x{args.grid_size:g} guide; tolerance +/- {line_tol:g} lines",
            (
                abs(grid_resolution["actual"]["vertical_lines"] - expected_grid_lines) <= line_tol
                and abs(grid_resolution["actual"]["horizontal_lines"] - expected_grid_lines) <= line_tol
            ),
        )
        annotation = colored_annotation_check(frame.inner(5), width, pixels)
        add_check(
            checks,
            f"{name}_no_colored_annotations",
            annotation["actual"],
            annotation["expected"],
            bool(annotation["pass"]) or bool(args.allow_colored_annotations),
        )
        bounds[name] = estimate_object_bounds(frame, width, pixels, args.grid_size)
        report["observed"][name] = rounded_bounds(bounds[name])
        if bounds[name] is None:
            add_check(checks, f"{name}_object_detected", None, "visible silhouette pixels inside grid", False)
            continue
        target_w, target_h = targets[name]
        add_check(
            checks,
            f"{name}_width_within_target",
            round(bounds[name].width, 1),
            f"{target_w:g} +/- {args.tolerance:g}",
            within(bounds[name].width, target_w, args.tolerance),
        )
        add_check(
            checks,
            f"{name}_height_within_target",
            round(bounds[name].height, 1),
            f"{target_h:g} +/- {args.tolerance:g}",
            within(bounds[name].height, target_h, args.tolerance),
        )

    side = bounds.get("side")
    front = bounds.get("front")
    top = bounds.get("top")
    if side and front and top:
        add_check(
            checks,
            "registration_side_length_matches_top_length",
            [round(side.width, 1), round(top.width, 1)],
            f"delta <= {args.tolerance:g}",
            abs(side.width - top.width) <= args.tolerance,
        )
        add_check(
            checks,
            "registration_front_width_matches_top_depth",
            [round(front.width, 1), round(top.height, 1)],
            f"delta <= {args.tolerance:g}",
            abs(front.width - top.height) <= args.tolerance,
        )
        add_check(
            checks,
            "registration_side_height_matches_front_height",
            [round(side.height, 1), round(front.height, 1)],
            f"delta <= {args.tolerance:g}",
            abs(side.height - front.height) <= args.tolerance,
        )
        add_check(
            checks,
            "registration_side_top_x_origin",
            [round(side.x0, 1), round(top.x0, 1)],
            f"delta <= {args.origin_tolerance:g}",
            abs(side.x0 - top.x0) <= args.origin_tolerance,
        )
        add_check(
            checks,
            "registration_front_top_z_origin",
            [round(front.x0, 1), round(top.y0, 1)],
            f"delta <= {args.origin_tolerance:g}",
            abs(front.x0 - top.y0) <= args.origin_tolerance,
        )
        add_check(
            checks,
            "registration_ground_baseline",
            [round(side.bottom_gap, 1), round(front.bottom_gap, 1)],
            f"delta <= {args.tolerance:g}",
            abs(side.bottom_gap - front.bottom_gap) <= args.tolerance,
        )
        expected_top_w, expected_top_h = args.top
        if expected_top_w > expected_top_h + args.tolerance:
            add_check(
                checks,
                "top_length_orientation",
                [round(top.width, 1), round(top.height, 1)],
                "top width should be greater than top height for length-on-X assets",
                top.width > top.height + max(1.0, args.tolerance * 0.5),
            )

    report["manual_review_required"] = [
        "head/front direction matches between Side and Top",
        "legs, ears/horns, tail, handles, wings, or markings line up across views",
        "orthographic views match the approved front/back style reference",
        "source image is AI/user raster design, not a script-rendered voxel draft",
    ]
    report["pass"] = all(check["pass"] for check in checks)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check a PNG AI voxel source sheet before voxel modeling.")
    parser.add_argument("--image", required=True, help="Source sheet PNG path.")
    parser.add_argument("--asset", required=True, help="Asset/model name, such as cow or dog_golden.")
    parser.add_argument("--side", required=True, type=parse_dims, help="Target side dims as lengthxheight, e.g. 40x32.")
    parser.add_argument("--front", required=True, type=parse_dims, help="Target front dims as widthxheight, e.g. 20x32.")
    parser.add_argument("--top", required=True, type=parse_dims, help="Target top dims as lengthxdepth, e.g. 40x20.")
    parser.add_argument("--tolerance", type=float, default=4.0)
    parser.add_argument("--origin-tolerance", type=float, default=4.0)
    parser.add_argument("--grid-line-tolerance", type=float, default=12.0)
    parser.add_argument("--grid-size", type=float, default=64.0, help="Panel guide size in cells, default 64.")
    parser.add_argument("--side-frame", type=parse_frame, help="Explicit side frame x,y,w,h.")
    parser.add_argument("--front-frame", type=parse_frame, help="Explicit front frame x,y,w,h.")
    parser.add_argument("--top-frame", type=parse_frame, help="Explicit top frame x,y,w,h.")
    parser.add_argument("--allow-colored-annotations", action="store_true", help="Do not fail on colored guide lines.")
    parser.add_argument("--json-out", help="Optional JSON report path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = run_check(args)
    except Exception as exc:  # noqa: BLE001 - CLI should turn parser/check failures into a report.
        report = {
            "asset": args.asset if "args" in locals() else None,
            "image": args.image if "args" in locals() else None,
            "pass": False,
            "checks": [{"id": "checker_error", "pass": False, "expected": "successful source sheet check", "actual": str(exc)}],
        }
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if getattr(args, "json_out", None):
        Path(args.json_out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
