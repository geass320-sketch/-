"""Validation gates for generation success criteria."""

from __future__ import annotations

from config import ValidationThresholds
from models import ValidationResult, VideoMetadata


class VideoValidator:
    """Apply strict success criteria beyond element presence."""

    def __init__(self, thresholds: ValidationThresholds) -> None:
        self.thresholds = thresholds

    def validate(self, current: VideoMetadata, previous_src: str | None) -> ValidationResult:
        """Validate generated video metadata against quality gates."""
        if not current.src:
            return ValidationResult(False, "Generated video src is empty")
        if previous_src and current.src == previous_src:
            return ValidationResult(False, "Generated video src did not change from previous run")
        if current.duration < self.thresholds.min_duration_seconds:
            return ValidationResult(False, f"Video duration {current.duration:.2f}s below threshold")
        if current.width < self.thresholds.min_width or current.height < self.thresholds.min_height:
            return ValidationResult(False, "Video resolution below threshold")
        return ValidationResult(True, "ok")
