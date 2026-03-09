"""Continuation-specific prompt utilities."""

from __future__ import annotations

from models import GenerationMode, GenerationRequest


class ContinuationEngine:
    """Build continuity constraints for continuation modes."""

    def continuity_clause(self, request: GenerationRequest) -> str:
        """Return continuity instructions aligned with the request mode."""
        if request.mode == GenerationMode.TEXT2VIDEO:
            return "镜头连贯、动作清晰、画面稳定，按提示直接开始完整新段落。"

        if request.mode == GenerationMode.FIRST_FRAME:
            return self._base_progression_clause(request)

        if request.mode == GenerationMode.FIRST_LAST_FRAME:
            end_state = request.end_state_hint or "给定尾帧所描述的结尾画面状态"
            return f"{self._base_progression_clause(request)} 最终必须到达的结尾画面状态（end_state）：{end_state}。"

        if request.mode == GenerationMode.EXTEND:
            return self._base_progression_clause(request)

        return self._base_progression_clause(request)

    @staticmethod
    def _base_progression_clause(request: GenerationRequest) -> str:
        previous = request.previous_shot_summary or "上一段镜头"
        return (
            f"从上一段结尾状态继续（参考：{previous}）；不要重复上一段已完成动作/构图；"
            "必须推进到新的动作与新的画面状态；保持角色身份、服装、环境与光线一致。"
        )
