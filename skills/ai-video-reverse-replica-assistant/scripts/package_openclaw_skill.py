#!/usr/bin/env python3
from __future__ import annotations

import zipfile
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "openclaw"
    dist = root / "assets"
    dist.mkdir(parents=True, exist_ok=True)
    out = dist / "openclaw-skill-ai-video-reverse-replica-assistant.zip"

    include = [
        src / "skill.yaml",
        src / "system_prompt.md",
        src / "output_schema.json",
        src / "examples" / "request.json",
    ]

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in include:
            zf.write(f, f.relative_to(src.parent))

    print(f"Packaged: {out}")


if __name__ == "__main__":
    main()
