"""Safe page control helpers for Seedance Playwright automation."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Locator, Page

from config import PipelineConfig


class PageControlError(RuntimeError):
    """Raised when a required page operation fails."""


class PreflightError(PageControlError):
    """Raised when preflight selector checks fail."""


class PageController:
    """Encapsulates all DOM interactions and writeback checks."""

    def __init__(self, page: Page, config: PipelineConfig) -> None:
        self.page = page
        self.config = config

    def navigate(self) -> None:
        """Open Seedance page and wait for prompt input readiness."""
        self.page.goto(self.config.base_url, wait_until="domcontentloaded", timeout=self.config.default_timeout_ms)
        self.page.locator(self.config.selectors.prompt_textarea).first.wait_for(timeout=self.config.default_timeout_ms)

    def preflight_selectors(self) -> None:
        """Ensure critical selectors are present and visible before generation."""
        checks = [
            ("prompt_textarea", self.config.selectors.prompt_textarea, True),
            ("mode_tab", self.config.selectors.mode_tab, False),
            ("model_dropdown", self.config.selectors.model_dropdown, True),
            ("ratio_dropdown", self.config.selectors.ratio_dropdown, True),
            ("duration_dropdown", self.config.selectors.duration_dropdown, True),
            ("upload_input", self.config.selectors.upload_input, False),
            ("generate_button", self.config.selectors.generate_button, True),
            ("latest_video", self.config.selectors.latest_video, False),
        ]
        for label, selector, exact_one in checks:
            self._assert_selector(label=label, selector=selector, exact_one=exact_one)

    def _assert_selector(self, label: str, selector: str, exact_one: bool) -> None:
        locator = self.page.locator(selector)
        count = locator.count()
        if exact_one and count != 1:
            raise PreflightError(f"Preflight failed: selector '{label}' expected count=1, got {count}: {selector}")
        if not exact_one and count < 1:
            raise PreflightError(f"Preflight failed: selector '{label}' expected count>=1, got 0: {selector}")
        if sum(1 for idx in range(count) if locator.nth(idx).is_visible()) < 1:
            raise PreflightError(f"Preflight failed: selector '{label}' has no visible elements: {selector}")

    def current_mode_label(self) -> str:
        """Return currently selected mode text from UI when available."""
        selected = self.page.locator(self.config.selectors.selected_mode)
        if selected.count() > 0:
            return selected.first.inner_text().strip()
        tabs = self.page.locator(self.config.selectors.mode_tab)
        if tabs.count() > 0:
            return tabs.first.inner_text().strip()
        return "unknown"

    def set_prompt_with_verification(self, prompt: str) -> None:
        """Fill prompt and verify read-back value to avoid accidental generation."""
        if not prompt.strip():
            raise PageControlError("Prompt is empty; generation is blocked")
        field = self.page.locator(self.config.selectors.prompt_textarea).first
        field.fill(prompt)
        if field.input_value().strip() != prompt.strip():
            raise PageControlError("Prompt writeback verification failed")

    def ensure_option_selected(self, label: str, value: str) -> None:
        """Select model/ratio/duration with stable selectors and verify selection."""
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
        role_option = self.page.get_by_role("option", name=value)
        if role_option.count() > 0:
            role_option.first.click()
        else:
            option = self.page.locator(self.config.selectors.option_items).filter(has_text=value)
            if option.count() == 0:
                option = self.page.locator(f"[aria-selected][data-value='{value}'], [data-value='{value}']")
            if option.count() == 0:
                raise PageControlError(f"{label} option not found for value '{value}'")
            option.first.click()

        selected_text = control.inner_text().strip().lower()
        if value.strip().lower() not in selected_text:
            selected = self.page.locator("[role='option'][aria-selected='true']").filter(has_text=value)
            if selected.count() < 1:
                raise PageControlError(f"{label} selection verification failed for value '{value}'")

    def set_reference_files(self, paths: tuple[Path, ...]) -> bool:
        """Upload provided references only; returns True when marker appears."""
        if not paths:
            return False
        for path in paths:
            if not path.exists() or path.stat().st_size <= 0:
                raise PageControlError(f"当前缺少可上传的本地文件路径/素材下载失败: {path}")
        input_node = self.page.locator(self.config.selectors.upload_input).first
        input_node.set_input_files([str(path) for path in paths])
        marker = self.page.locator(self.config.selectors.uploaded_asset_marker)
        return marker.count() > 0

    def click_generate(self) -> None:
        """Click generate button."""
        self.page.locator(self.config.selectors.generate_button).first.click()

    def ensure_generate_clickable(self) -> None:
        """Try to make generate button interactable for retry clicks."""
        button = self.page.locator(self.config.selectors.generate_button).first
        button.scroll_into_view_if_needed()
        for selector in ("button:has-text('关闭')", "button:has-text('稍后')", "[aria-label='Close']", ".guide-close"):
            node = self.page.locator(selector)
            if node.count() > 0 and node.first.is_visible():
                node.first.click()

    def toast_messages(self) -> list[str]:
        """Collect visible toast/status messages for diagnostics."""
        messages: list[str] = []
        loc = self.page.locator(self.config.selectors.toast)
        for i in range(min(loc.count(), 8)):
            text = loc.nth(i).inner_text().strip()
            if text:
                messages.append(text)
        return messages

    def form_errors(self) -> list[str]:
        """Collect visible form validation messages."""
        errors: list[str] = []
        loc = self.page.locator(self.config.selectors.form_error)
        for i in range(min(loc.count(), 8)):
            text = loc.nth(i).inner_text().strip()
            if text:
                errors.append(text)
        return errors

    def card_count(self) -> int:
        """Return number of visible video cards."""
        cards = self.page.locator(self.config.selectors.latest_video_card)
        return cards.count() if cards.count() > 0 else self.page.locator(self.config.selectors.latest_video).count()

    def has_generate_busy_indicator(self) -> bool:
        """Check whether generate button enters busy state."""
        return self.page.locator(self.config.selectors.generate_busy).count() > 0

    def latest_video_container(self, src_hint: str | None = None) -> Locator:
        """Return video container optionally matched by src hint."""
        cards = self.page.locator(self.config.selectors.latest_video_card)
        if src_hint and cards.count() > 0:
            matched = cards.filter(has=self.page.locator(f"video[src*='{src_hint}']"))
            if matched.count() > 0:
                return matched.first
        if cards.count() > 0:
            return cards.last
        videos = self.page.locator(self.config.selectors.latest_video)
        if videos.count() < 1:
            raise PageControlError("No latest video container could be located")
        return videos.last.locator("xpath=ancestor-or-self::*[1]")

    def has_zero_duration_marker(self, src_hint: str | None = None) -> bool:
        """Detect placeholder cards showing 00:00 duration."""
        container = self.latest_video_container(src_hint=src_hint)
        text = container.inner_text().strip()
        duration = container.locator(self.config.selectors.card_duration_text)
        if duration.count() > 0:
            text += " " + duration.first.inner_text().strip()
        return "00:00" in text

    def click_scoped_download(self, src_hint: str | None = None) -> None:
        """Click download button within latest/new video scope only."""
        container = self.latest_video_container(src_hint=src_hint)
        scoped_button = container.locator(self.config.selectors.download_button)
        if scoped_button.count() < 1:
            raise PageControlError("Scoped download button not found in latest video container")
        scoped_button.first.click()
