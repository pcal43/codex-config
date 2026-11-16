---
name: pico8-project-setup
description: Create a new empty-but-runnable PICO-8 development project with the repository layout and Justfile-based build workflow used by the local PICO-8 projects.
---

# PICO-8 Project Setup

Use this skill when the user wants a new, empty PICO-8 project scaffold. Do not use it to copy an existing game's source, assets, historical research, or game-specific tooling.

## Workflow

1. Confirm the destination directory and project name. The destination must be an existing empty directory or a path that does not exist. Never overwrite an existing non-empty directory.
2. Run `scripts/create_project.py <destination>`, passing `--name <name>` when the user has already supplied a name. If no name is supplied, let the script prompt for it. Use the script's default version unless the user requests another version.
3. Report the created path and the next commands: `just minify`, `just lint`, `just count`, and `just run`.

## Generated project contract

- The project uses `project.env` for `PROJECT_NAME`, `VERSION`, `PICO8_BIN`, and `SHRINKO8_SCRIPT`.
- The cart is `pico8-home/carts/<project>/<project>.p8`; source is under its `src/` directory.
- The cart includes `version.lua` followed by `src/main.lua` and has `_init`, `_update60`, and `_draw` hooks.
- The starter cart displays a small hello-world message so a successful run is immediately visible.
- The Justfile provides generic `clean`, `version`, `minify`, `lint`, `count`, `run`, and `release` recipes. It uses Shrinko8 for minification/linting and PICO-8 for running/exporting.
- `build/` and PICO-8 runtime state are generated. In particular, do not create or commit `pico8-home/sdl_controllers.txt`; it is runtime-generated and ignored.
- Do not initialize Git. The skill creates files only.

## Tool configuration

The script detects the example Shrinko8 path when it exists and otherwise writes a placeholder `shrinko8.py` path. Keep the generated values editable; do not install tools or modify global configuration as part of setup.
