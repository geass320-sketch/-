"""Safe page control helpers for Seedance Playwright automation."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Page

from config import PipelineConfig


class PageControlError(RuntimeError):
    """Raised when a required page operation fails."""


class PageController:
    """Encapsulates all DOM interactions and writeback checks."""

    def __init__(self, page: Page, config: PipelineConfig) -> None:
        self.page = page
        self.config = config

    def navigate(self) -> None:
        """Open Seedance page and wait for prompt input readiness."""
        self.page.goto(self.config.base_url, wait_until="domcontentloaded", timeout=self.config.default_timeout_ms)
        self.page.locator(self.config.selectors.prompt_textarea).first.wait_for(timeout=self.config.default_timeout_ms)

    def set_prompt_with_verification(self, prompt: str) -> None:
        """Fill prompt and verify read-back value to avoid accidental generation."""
        if not prompt.strip():
            raise PageControlError("Prompt is empty; generation is blocked")
        field = self.page.locator(self.config.selectors.prompt_textarea).first
        field.fill(prompt)
        actual = field.input_value().strip()
        if actual != prompt.strip():
            raise PageControlError("Prompt writeback verification failed")

    def ensure_option_selected(self, label: str, value: str) -> None:
        """Select model/ratio/duration and verify selected text contains expected value."""
        mapping = {
            "model": self.config.selectors.model_dropdown,
            "ratio": self.config.selectors.ratio_dropdown,
            "duration": self.config.selectors.duration_dropdown,
        }
        selector = mapping.get(label)
        if selector is None:
            raise PageControlError(f"Unknown option label: {label}")

        control = self.page.locator(selector).first
        control.click()
        option = self.page.locator(f"text={value}").first
        option.click()
        selected_text = control.inner_text().strip().lower()
        if value.strip().lower() not in selected_text:
            raise PageControlError(f"{label} selection verification failed for value '{value}'")

    def upload_images(self, paths: tuple[Path, ...]) -> None:
        """Upload required continuation images and verify count."""
        if not paths:
            return
        for path in paths:
            if not path.exists():
                raise PageControlError(f"Required image does not exist: {path}")
        input_node = self.page.locator(self.config.selectors.upload_input).first
        input_node.set_input_files([str(path) for path in paths])

    def click_generate(self) -> None:
        """Click generate button."""
        self.page.locator(self.config.selectors.generate_button).first.click()

    def trigger_download(self) -> None:
        """Click download after validation has passed."""
        self.page.locator(self.config.selectors.download_button).first.click()
