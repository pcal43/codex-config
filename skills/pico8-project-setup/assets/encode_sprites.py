#!/usr/bin/env python3
"""Install a 128x128 PICO-8 palette PNG as a cartridge's sprite sheet."""

import os
import re
import sys
import tempfile
from pathlib import Path

from PIL import Image


PALETTE = (
    (0, 0, 0), (29, 43, 83), (126, 37, 83), (0, 135, 81),
    (171, 82, 54), (95, 87, 79), (194, 195, 199), (255, 241, 232),
    (255, 0, 77), (255, 163, 0), (255, 236, 39), (0, 228, 54),
    (41, 173, 255), (131, 118, 156), (255, 119, 168), (255, 204, 170),
)
COLOR_INDEX = {color: index for index, color in enumerate(PALETTE)}
SECTION = re.compile(rb"^__[a-z0-9_]+__\s*(?:\r?\n|$)")


def encode_image(path):
    with Image.open(path) as image:
        if image.size != (128, 128):
            raise ValueError(f"expected a 128x128 image, got {image.size}")
        image = image.convert("RGBA")
        rows = []
        for y in range(128):
            row = []
            for x in range(128):
                r, g, b, alpha = image.getpixel((x, y))
                if alpha == 0:
                    index = 0
                elif alpha != 255:
                    raise ValueError(f"partial transparency at ({x}, {y}): {alpha}")
                elif (r, g, b) not in COLOR_INDEX:
                    raise ValueError(f"unsupported color at ({x}, {y}): RGB {(r, g, b)}")
                else:
                    index = COLOR_INDEX[(r, g, b)]
                row.append(format(index, "x"))
            rows.append("".join(row))
        return rows


def install_gfx(cart_path, rows):
    path = Path(cart_path)
    original = path.read_bytes()
    lines = original.splitlines(keepends=True)
    markers = [i for i, line in enumerate(lines) if line.rstrip(b"\r\n") == b"__gfx__"]
    if len(markers) > 1:
        raise ValueError("cartridge has multiple __gfx__ sections")
    newline = b"\r\n" if b"\r\n" in original else b"\n"
    gfx = b"__gfx__" + newline + newline.join(row.encode("ascii") for row in rows) + newline
    if markers:
        start = markers[0]
        end = start + 1
        while end < len(lines) and not SECTION.match(lines[end]):
            end += 1
        result = b"".join(lines[:start]) + gfx + b"".join(lines[end:])
    else:
        section_start = next((i for i, line in enumerate(lines) if SECTION.match(line)
                              and line.rstrip(b"\r\n") != b"__lua__"), len(lines))
        before = b"".join(lines[:section_start])
        if before and not before.endswith(b"\n"):
            before += newline
        result = before + gfx + b"".join(lines[section_start:])
    if result == original:
        return
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temp:
            temp_name = temp.name
            temp.write(result)
        os.chmod(temp_name, path.stat().st_mode & 0o777)
        os.replace(temp_name, path)
        temp_name = None
    finally:
        if temp_name is not None:
            os.unlink(temp_name)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: encode_sprites.py INPUT.png CART.p8")
    try:
        install_gfx(sys.argv[2], encode_image(sys.argv[1]))
    except (OSError, ValueError) as error:
        raise SystemExit(f"sprite encoding failed: {error}") from error


if __name__ == "__main__":
    main()
