"""Prompt compilation for Seedance generation."""

from __future__ import annotations

from models import PromptParts


class PromptCompiler:
    """Compile prompt parts into final Seedance-style input."""

    def compile(self, parts: PromptParts) -> str:
        """Compose a readable multi-section prompt string."""
        segments = [
            f"Main prompt: {parts.main_prompt.strip()}",
            f"Continuity/Constraints: {parts.continuity_prompt.strip()}",
            f"Negative constraints: {parts.negative_constraints.strip()}",
        ]
        compiled = "\n".join(segments).strip()
        if not compiled or compiled == "Main prompt:\nContinuity/Constraints:\nNegative constraints:":
            raise ValueError("Compiled prompt is empty")
        return compiled
