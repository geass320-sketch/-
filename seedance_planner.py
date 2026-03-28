"""Planner that prepares validated generation plans before page interaction."""

from __future__ import annotations

from models import GenerationMode, GenerationPlan, GenerationRequest, PromptParts
from continuation_engine import ContinuationEngine
from prompt_compiler import PromptCompiler


class PlanningError(ValueError):
    """Raised when input cannot produce a safe generation plan."""


class JimengPlanner:
    """Create a generation plan with structured prompt parts for Jimeng web."""

    def __init__(self) -> None:
        self._continuation = ContinuationEngine()
        self._compiler = PromptCompiler()

    def build_plan(self, request: GenerationRequest) -> GenerationPlan:
        """Validate input and return a plan ready for automation."""
        if not request.prompt.strip():
            raise PlanningError("Prompt cannot be empty")
        if not request.model.strip() or not request.ratio.strip() or not request.duration.strip():
            raise PlanningError("Model, ratio, and duration must all be provided")

        continuity = self._continuation.continuity_clause(request)
        negatives = "no duplicated prior shot, no identity drift, no lighting inconsistency, no abrupt scene jump"
        parts = PromptParts(
            main_prompt=request.prompt,
            continuity_prompt=continuity,
            negative_constraints=negatives,
        )
        compiled = self._compiler.compile(parts)

        required_images: tuple = ()
        if request.mode == GenerationMode.FIRST_FRAME:
            required_images = (request.first_frame_path,)
        elif request.mode == GenerationMode.FIRST_LAST_FRAME:
            required_images = (request.first_frame_path, request.last_frame_path)
        required_images = tuple(path for path in required_images if path is not None)

        return GenerationPlan(
            request=request,
            prompt_parts=parts,
            compiled_prompt=compiled,
            required_images=required_images,
        )


class SeedancePlanner(JimengPlanner):
    """Backward-compatible alias for older imports."""
