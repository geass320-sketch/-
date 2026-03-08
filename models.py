"""Typed domain models for generation planning and execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class GenerationMode(str, Enum):
    """Supported Seedance generation modes."""

    TEXT2VIDEO = "text2video"
    FIRST_FRAME = "first_frame"
    FIRST_LAST_FRAME = "first_last_frame"
    EXTEND = "extend"


@dataclass(frozen=True)
class GenerationRequest:
    """External input model used by orchestration callers."""

    prompt: str
    model: str
    ratio: str
    duration: str
    mode: GenerationMode = GenerationMode.TEXT2VIDEO
    first_frame_path: Path | None = None
    last_frame_path: Path | None = None
    previous_shot_summary: str | None = None


@dataclass(frozen=True)
class PromptParts:
    """Structured prompt segments for Seedance-oriented prompting."""

    main_prompt: str
    continuity_prompt: str
    negative_constraints: str


@dataclass(frozen=True)
class GenerationPlan:
    """Prepared plan used to drive a safe generation attempt."""

    request: GenerationRequest
    prompt_parts: PromptParts
    compiled_prompt: str
    required_images: tuple[Path, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class VideoMetadata:
    """Video details read from DOM/video element."""

    src: str
    duration: float
    width: int
    height: int


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of generation validation checks."""

    ok: bool
    reason: str


@dataclass(frozen=True)
class GenerationOutput:
    """Per-task generation output after validation and download."""

    task_id: int
    video_src: str
    download_path: Path
