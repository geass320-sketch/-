"""Configuration objects for Seedance automation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SeedanceSelectors:
    """All page selectors used by the automation flow."""

    prompt_textarea: str = "textarea[placeholder*='prompt'], textarea"
    mode_tab: str = "[data-testid='mode-select'], [role='tablist'] [role='tab'], .mode-select"
    selected_mode: str = "[role='tab'][aria-selected='true'], [data-testid='mode-active'], .mode.active"
    model_dropdown: str = "[data-testid='model-select'], [aria-label*='model'], .model-select"
    ratio_dropdown: str = "[data-testid='ratio-select'], [aria-label*='ratio'], .ratio-select"
    duration_dropdown: str = "[data-testid='duration-select'], [aria-label*='duration'], .duration-select"
    upload_input: str = "input[type='file']"
    uploaded_asset_marker: str = "[data-testid='upload-thumb'], .upload-thumb, button[aria-label*='删除'], .uploaded-item"
    generate_button: str = "[data-testid='generate-button'], button:has-text('Generate'), button:has-text('生成')"
    generate_busy: str = "[data-testid='generate-button'][aria-busy='true'], button[aria-busy='true'], .loading, .spinner"
    toast: str = "[role='status'], .toast, .message, .notice"
    form_error: str = ".error, [aria-invalid='true'], [data-testid='form-error']"
    latest_video_card: str = "[data-testid='video-card'], .video-card, .result-card"
    card_duration_text: str = ".duration, [data-testid='duration']"
    latest_video: str = "video"
    download_button: str = "a[download], [data-testid='download-button'], button:has-text('Download'), button:has-text('下载')"
    option_items: str = "[role='option'], [data-testid='select-option'], .select-option"


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
    temp_dir: Path = Path("temp")
    default_timeout_ms: int = 25_000
    poll_interval_seconds: float = 1.0
    trigger_timeout_seconds: int = 8
    max_wait_seconds: int = 240
    post_success_wait_seconds: int = 6
    loading_src_patterns: tuple[str, ...] = (
        "placeholder",
        "record-loading",
        "loading",
        "pending",
    )
    explicit_failure_keywords: tuple[str, ...] = (
        "审核未通过",
        "生成失败",
        "网络异常",
        "网络超时",
        "请稍后重试",
        "failed",
        "error",
        "denied",
    )
    selectors: SeedanceSelectors = field(default_factory=SeedanceSelectors)
    thresholds: ValidationThresholds = field(default_factory=ValidationThresholds)
