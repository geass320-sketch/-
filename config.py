"""Configuration objects for Jimeng web automation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class JimengWebSelectors:
    """All page selectors used by the Jimeng (即梦) web automation flow."""

    prompt_textarea: str = "textarea[placeholder*='描述'], textarea[placeholder*='prompt'], textarea"
    generate_button: str = (
        "button:has-text('立即生成'), button:has-text('生成视频'), button:has-text('Generate'), button:has-text('生成')"
    )
    model_dropdown: str = "[data-testid='model-select'], .model-select, [aria-label*='模型']"
    ratio_dropdown: str = "[data-testid='ratio-select'], .ratio-select, [aria-label*='比例']"
    duration_dropdown: str = "[data-testid='duration-select'], .duration-select, [aria-label*='时长']"
    upload_input: str = "input[type='file']"
    latest_video: str = "video"
    download_button: str = "a[download], button:has-text('下载'), button:has-text('Download')"


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
    selectors: JimengWebSelectors = field(default_factory=JimengWebSelectors)
    thresholds: ValidationThresholds = field(default_factory=ValidationThresholds)
