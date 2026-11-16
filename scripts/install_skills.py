#!/usr/bin/env python3
"""Install all skills in this repository into the active Codex skills directory."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPOSITORY_ROOT / "skills"
INSTALL_ROOT = Path(os.environ.get("CODEX_SKILLS_DIR", str(Path.home() / ".codex" / "skills"))).expanduser()


def main() -> int:
    skills = sorted(path for path in SKILLS_ROOT.iterdir() if path.is_dir())
    INSTALL_ROOT.mkdir(parents=True, exist_ok=True)
    for skill in skills:
        target = INSTALL_ROOT / skill.name
        if target.exists() or target.is_symlink():
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()
        shutil.copytree(skill, target)
        print(f"Installed {skill.name} -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
