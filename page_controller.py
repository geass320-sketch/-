"""Safe page control helpers for Jimeng web Playwright automation."""

from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from config import PipelineConfig


class PageControlError(RuntimeError):
    """Raised when a required page operation fails."""


class PageController:
    """Encapsulates all DOM interactions and writeback checks."""

    def __init__(self, page: Page, config: PipelineConfig) -> None:
        self.page = page
        self.config = config

    def navigate(self) -> None:
        """Open Jimeng web page and wait for prompt input readiness."""
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

    def _verify_upload_success(self, minimum_expected: int, timeout_seconds: float = 3.0) -> bool:
        """Check both input files and rendered previews to detect upload success."""
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            files_seen = self.page.evaluate(
                """
                (selector) => {
                    const nodes = Array.from(document.querySelectorAll(selector));
                    return nodes.reduce((sum, n) => sum + (n.files ? n.files.length : 0), 0);
                }
                """,
                self.config.selectors.upload_input,
            )
            preview_count = self.page.locator(self.config.selectors.uploaded_preview_items).count()
            if int(files_seen) >= minimum_expected or int(preview_count) >= minimum_expected:
                return True
            self.page.wait_for_timeout(200)
        return False

    def _upload_by_input(self, paths: tuple[Path, ...]) -> bool:
        """Attempt direct set_input_files and synthesize events for JS-heavy UIs."""
        input_node = self.page.locator(self.config.selectors.upload_input).first
        input_node.set_input_files([str(path) for path in paths])
        self.page.evaluate(
            """
            (selector) => {
                const node = document.querySelector(selector);
                if (!node) return;
                node.dispatchEvent(new Event('input', { bubbles: true }));
                node.dispatchEvent(new Event('change', { bubbles: true }));
            }
            """,
            self.config.selectors.upload_input,
        )
        return self._verify_upload_success(len(paths))

    def _upload_by_file_chooser(self, paths: tuple[Path, ...]) -> bool:
        """Attempt click-triggered file chooser path for hijacked input flows."""
        triggers = self.page.locator(self.config.selectors.upload_triggers)
        trigger_count = triggers.count()
        if trigger_count == 0:
            return False

        for idx in range(trigger_count):
            candidate = triggers.nth(idx)
            try:
                with self.page.expect_file_chooser(timeout=2_500) as chooser_info:
                    candidate.click()
                chooser = chooser_info.value
                chooser.set_files([str(path) for path in paths])
            except PlaywrightTimeoutError:
                continue
            if self._verify_upload_success(len(paths)):
                return True
        return False

    def upload_images(self, paths: tuple[Path, ...]) -> None:
        """Upload required continuation images with multi-strategy fallback."""
        if not paths:
            return
        for path in paths:
            if not path.exists():
                raise PageControlError(f"Required image does not exist: {path}")

        if self._upload_by_input(paths):
            return
        if self._upload_by_file_chooser(paths):
            return
        raise PageControlError(
            "Upload failed after both direct input and file-chooser strategies; "
            "likely due to page-side anti-automation upload checks"
        )

    def click_generate(self) -> None:
        """Click generate button."""
        self.page.locator(self.config.selectors.generate_button).first.click()

    def trigger_download(self) -> None:
        """Click download after validation has passed."""
        self.page.locator(self.config.selectors.download_button).first.click()
