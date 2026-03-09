"""Planner that prepares validated generation plans before page interaction."""

from __future__ import annotations

from continuation_engine import ContinuationEngine
from models import GenerationPlan, GenerationRequest, PromptParts
from prompt_compiler import PromptCompiler


class PlanningError(ValueError):
    """Raised when input cannot produce a safe generation plan."""


class SeedancePlanner:
    """Create a generation plan with structured prompt parts."""

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
        negatives = (
            "负面约束：不要重复上一段镜头；不要角色身份漂移；不要服装突变；不要光线与场景突变；"
            "不要抖动和明显穿帮。"
            " Optional EN: no duplicated prior shot, no identity drift, no outfit drift, "
            "no lighting inconsistency, no abrupt scene jump."
        )
        parts = PromptParts(
            main_prompt=request.prompt,
            continuity_prompt=continuity,
            negative_constraints=negatives,
        )
        compiled = self._compiler.compile(parts)

        images = [p for p in (request.first_frame_path, request.last_frame_path, *request.reference_paths) if p is not None]
        return GenerationPlan(
            request=request,
            prompt_parts=parts,
            compiled_prompt=compiled,
            required_images=tuple(images),
        )
