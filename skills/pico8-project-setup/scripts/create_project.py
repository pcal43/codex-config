#!/usr/bin/env python3
"""Create a generic, runnable PICO-8 project scaffold."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def ask(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    answer = input(f"{prompt}{suffix}: ").strip()
    return answer or (default or "")


def validate_name(name: str) -> str:
    if not NAME_RE.fullmatch(name):
        raise ValueError("project name must use lowercase letters, digits, hyphens, or underscores")
    return name


def shell_quote_lua(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def shrinko8_default() -> str:
    example = Path("/Users/pcal/dev/shrinko8/shrinko8.py")
    return str(example) if example.exists() else "shrinko8.py"


def files_for(name: str, version: str, shrinko8_script: str) -> dict[str, str]:
    cart = """pico-8 cartridge // http://www.pico-8.com
version 43
__lua__

#include version.lua
#include src/main.lua
"""
    main_lua = f'''function _init()
end

function _update60()
end

function _draw()
    cls(1)
    print("hello from {shell_quote_lua(name)}", 38, 60, 7)
end
'''
    justfile = r'''set dotenv-filename := "project.env"
set dotenv-load
set export

PROJECT_NAME := env("PROJECT_NAME")
VERSION := env("VERSION")
PICO8_BIN := env("PICO8_BIN")
SHRINKO8_SCRIPT := env("SHRINKO8_SCRIPT")

ROOT_DIR := "."
BUILD_DIR := ROOT_DIR + "/build"
PICO8_HOME := ROOT_DIR + "/pico8-home"
PICO8_CARTS := PICO8_HOME + "/carts"
GAME_ROOT := PICO8_CARTS + "/" + PROJECT_NAME
GAME_CART := GAME_ROOT + "/" + PROJECT_NAME + ".p8"
MINIFIED_CART := BUILD_DIR + "/" + PROJECT_NAME + "-min.p8"
RELEASE_ARTIFACT := BUILD_DIR + "/" + PROJECT_NAME + "-" + VERSION + ".p8.png"
SPRITES_SOURCE := "resources/spritesheet.aseprite"
SPRITES_PNG := "resources/spritesheet.png"
ASEPRITE_BIN := if `uname -s` == "Darwin" { "/Applications/Aseprite.app/Contents/MacOS/aseprite" } else { "aseprite" }
SPRITES_PYTHON := env_var_or_default("SPRITES_PYTHON", "python3")

clean:
    rm -rf "$BUILD_DIR"

version:
    mkdir -p "$GAME_ROOT"
    printf '%s\n' '--lint: used::VERSION' 'VERSION = "'$VERSION'"' > "$GAME_ROOT/version.lua"

minify: version
    mkdir -p "$BUILD_DIR"
    python3 "$SHRINKO8_SCRIPT" "$GAME_CART" "$MINIFIED_CART" --minify --focus-chars

lint: version
    python3 "$SHRINKO8_SCRIPT" "$GAME_CART" --lint

sprites-edit:
    "{{ASEPRITE_BIN}}" "{{SPRITES_SOURCE}}"

sprites-export:
    "{{ASEPRITE_BIN}}" -b "{{SPRITES_SOURCE}}" --frame-range 0,0 --save-as "{{SPRITES_PNG}}"

sprites-encode:
    {{SPRITES_PYTHON}} tools/encode_sprites.py "{{SPRITES_PNG}}" "$GAME_CART"

sprites: sprites-export sprites-encode

build: minify

count: build
    python3 "$SHRINKO8_SCRIPT" "$MINIFIED_CART" --count

run:
    test -f "$MINIFIED_CART" || (echo "Missing $MINIFIED_CART; run 'just build' first."; exit 1)
    "$PICO8_BIN" -home "$PICO8_HOME" -root_path "$PICO8_CARTS" -run "$MINIFIED_CART"

release: clean build
    "$PICO8_BIN" -home "$PICO8_HOME" -root_path "$PICO8_CARTS" "$MINIFIED_CART" -export "$RELEASE_ARTIFACT"
'''
    project_env = f"""PROJECT_NAME={name}
VERSION={version}
PICO8_BIN=/Applications/PICO-8.app/Contents/MacOS/pico8
SHRINKO8_SCRIPT={shrinko8_script}
"""
    gitignore = r'''/#*
*~
.DS_Store

build/

/pico8-home/log.txt
/pico8-home/activity_log.txt
/pico8-home/backup/
/pico8-home/config.txt
/pico8-home/favourites.txt
/pico8-home/sdl_controller.txt
/pico8-home/sdl_controllers.txt
/pico8-home/cdata/
'''
    agents = f'''# {name} PICO-8 project guide

## Layout

- The playable cart is `pico8-home/carts/{name}/{name}.p8`.
- Lua source lives in `pico8-home/carts/{name}/src/` and is included in explicit order by the cart.
- `project.env` contains project/version settings and local PICO-8/Shrinko8 paths.
- `resources/spritesheet.aseprite` is the editable 128×128 sprite sheet; `resources/spritesheet.png` is its exported first frame. `tools/encode_sprites.py` writes the full sprite sheet to the cart's `__gfx__` section, including the lower half shared with map memory.
- `build/` and `pico8-home/` runtime files are generated; do not edit or commit them as source.

## Commands

- `just minify` builds `build/{name}-min.p8`.
- `just lint` runs Shrinko8 lint.
- `just build` creates the minified cart without launching PICO-8.
- `just count` reports the built cart size.
- `just run` launches an already-built cart in PICO-8; run it from the interactive macOS user's session.
- `just release` exports `build/{name}-{version}.p8.png`.
- `just sprites-edit` opens the Aseprite sheet; `just sprites-export` exports its first frame; `just sprites-encode` encodes the PNG; and `just sprites` runs export and encoding in order. Run Aseprite recipes from an interactive macOS session. Normal builds do not export sprites.
- Sprite encoding requires Pillow and exact standard PICO-8 palette colors. Fully transparent pixels become color 0; partial transparency and other colors are rejected. Set `SPRITES_PYTHON` to a Python command with Pillow if the default `python3` cannot import it (for example `arch -x86_64 python3` on macOS).

Keep the cart include order intentional and preserve PICO-8 Lua semantics when editing source.
'''
    version_lua = f'--lint: used::VERSION\nVERSION = "{shell_quote_lua(version)}"\n'
    return {
        ".gitignore": gitignore,
        "AGENTS.md": agents,
        "Justfile": justfile,
        "project.env": project_env,
        f"pico8-home/carts/{name}/{name}.p8": cart,
        f"pico8-home/carts/{name}/version.lua": version_lua,
        f"pico8-home/carts/{name}/src/main.lua": main_lua,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--name", help="lowercase project name; prompted when omitted")
    parser.add_argument("--version", default="0.0.1")
    args = parser.parse_args()

    destination = args.destination.expanduser()
    if destination.exists():
        if not destination.is_dir():
            print(f"error: destination is not a directory: {destination}", file=sys.stderr)
            return 2
        if any(destination.iterdir()):
            print(f"error: destination is not empty: {destination}", file=sys.stderr)
            return 2

    name = args.name or ask("Project name")
    try:
        validate_name(name)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if not args.version.strip():
        print("error: version must not be empty", file=sys.stderr)
        return 2

    files = files_for(name, args.version.strip(), shrinko8_default())
    assets = Path(__file__).resolve().parent.parent / "assets"
    asset_files = {
        "resources/spritesheet.aseprite": (assets / "spritesheet.aseprite").read_bytes(),
        "resources/spritesheet.png": (assets / "spritesheet.png").read_bytes(),
        "tools/encode_sprites.py": (assets / "encode_sprites.py").read_bytes(),
    }
    directories = {destination / "docs", destination / "etc", destination / "resources", destination / "tools"}
    directories.update((destination / path).parent for path in files)
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    for relative, contents in files.items():
        (destination / relative).write_text(contents, encoding="utf-8")
    for relative, contents in asset_files.items():
        (destination / relative).write_bytes(contents)

    print(f"Created PICO-8 project: {destination}")
    print(f"Project name: {name}")
    print("Next: cd into the project and run `just build`, then `just run` from an interactive session.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
