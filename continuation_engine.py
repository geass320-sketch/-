"""Continuation-specific prompt utilities."""

from __future__ import annotations

from models import GenerationMode, GenerationRequest


class ContinuationError(ValueError):
    """Raised when continuation settings are invalid."""


class ContinuationEngine:
    """Build continuity constraints for continuation modes."""

    def continuity_clause(self, request: GenerationRequest) -> str:
        """Return continuity instructions aligned with the request mode."""
        if request.mode == GenerationMode.TEXT2VIDEO:
            return "Start a coherent standalone shot with clear action progression."

        if request.mode == GenerationMode.FIRST_FRAME:
            self._require(request.first_frame_path, "first_frame mode requires first_frame_path")
            return self._base_progression_clause(request)

        if request.mode == GenerationMode.FIRST_LAST_FRAME:
            self._require(request.first_frame_path, "first_last_frame mode requires first_frame_path")
            self._require(request.last_frame_path, "first_last_frame mode requires last_frame_path")
            return f"{self._base_progression_clause(request)} Reach a clear end-state consistent with provided last frame."

        if request.mode == GenerationMode.EXTEND:
            return (
                "Extend mode placeholder: continue timeline naturally while preserving visual continuity "
                "and introducing meaningful new action."
            )

        raise ContinuationError(f"Unsupported mode: {request.mode}")

    @staticmethod
    def _require(value: object | None, message: str) -> None:
        if value is None:
            raise ContinuationError(message)

    @staticmethod
    def _base_progression_clause(request: GenerationRequest) -> str:
        previous = request.previous_shot_summary or "the previous shot"
        return (
            f"Maintain consistent character, outfit, environment, and lighting from {previous}; "
            "do not repeat the prior shot composition; progress into a distinct new action/state."
        )
