"""Frame asset helpers used by continuation workflows."""

from __future__ import annotations

from pathlib import Path


class FrameToolsError(ValueError):
    """Raised when a frame asset path is invalid."""


def ensure_frame_exists(path: Path | None, label: str) -> Path:
    """Ensure an optional frame path is present and exists."""
    if path is None:
        raise FrameToolsError(f"{label} frame is required but missing")
    if not path.exists():
        raise FrameToolsError(f"{label} frame does not exist: {path}")
    return path
