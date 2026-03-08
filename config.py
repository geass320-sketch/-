"""Configuration objects for Seedance automation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SeedanceSelectors:
    """All page selectors used by the automation flow."""

    prompt_textarea: str = "textarea[placeholder*='prompt'], textarea"
    generate_button: str = "button:has-text('Generate'), button:has-text('生成')"
    model_dropdown: str = "[data-testid='model-select'], .model-select"
    ratio_dropdown: str = "[data-testid='ratio-select'], .ratio-select"
    duration_dropdown: str = "[data-testid='duration-select'], .duration-select"
    upload_input: str = "input[type='file']"
    latest_video: str = "video"
    download_button: str = "a[download], button:has-text('Download'), button:has-text('下载')"


@dataclass(frozen=True)
class ValidationThresholds:
    """Numeric thresholds for generated video validation."""

    min_duration_seconds: float = 3.0
    min_width: int = 200
    min_height: int = 200


@dataclass(frozen=True)
class PipelineConfig:
    """Top-level runtime configuration for pipeline execution."""

    base_url: str
    cookies_path: Path
    output_dir: Path = Path("downloads")
    default_timeout_ms: int = 25_000
    poll_interval_seconds: float = 1.0
    max_wait_seconds: int = 180
    selectors: SeedanceSelectors = field(default_factory=SeedanceSelectors)
    thresholds: ValidationThresholds = field(default_factory=ValidationThresholds)
