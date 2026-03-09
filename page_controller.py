"""Safe page control helpers for Seedance Playwright automation."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError

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
        self._resolved: dict[str, str] = {}
        self._preflight_report: dict[str, dict[str, object]] = {}

    def navigate(self) -> None:
        """Open Seedance page and wait for prompt input readiness."""
        self.page.goto(self.config.base_url, wait_until="domcontentloaded", timeout=self.config.default_timeout_ms)
        self.page.locator(self.config.selectors.prompt_textarea).first.wait_for(timeout=self.config.default_timeout_ms)

    def preflight_selectors(self) -> dict[str, dict[str, object]]:
        """Resolve selectors from candidate lists and validate presence/visibility."""
        requirements = {
            "prompt_textarea": (True, True, [
                self.config.selectors.prompt_textarea,
                "textarea[data-testid='prompt-input']",
                "[contenteditable='true'][data-testid*='prompt']",
            ]),
            "mode_tab": (False, True, [
                self.config.selectors.mode_tab,
                "[data-testid*='mode'] [role='tab']",
                "button[role='tab']",
            ]),
            "model_dropdown": (True, True, [
                self.config.selectors.model_dropdown,
                "[data-testid*='model']",
                "button[aria-label*='模型'], button[aria-label*='Model']",
            ]),
            "ratio_dropdown": (True, True, [
                self.config.selectors.ratio_dropdown,
                "[data-testid*='ratio']",
                "button[aria-label*='比例'], button[aria-label*='Ratio']",
            ]),
            "duration_dropdown": (True, True, [
                self.config.selectors.duration_dropdown,
                "[data-testid*='duration']",
                "button[aria-label*='时长'], button[aria-label*='Duration']",
            ]),
            "upload_input": (False, False, [
                self.config.selectors.upload_input,
                "input[type='file'][accept*='image']",
                "input[type='file'][accept*='video']",
            ]),
            "generate_button": (False, True, [
                self.config.selectors.generate_button,
                "button[data-testid*='generate']",
                "button:has-text('立即生成'), button:has-text('生成视频')",
            ]),
            "latest_video": (False, False, [
                self.config.selectors.latest_video,
                "[data-testid*='video'] video",
            ]),
            "latest_video_card": (False, False, [
                self.config.selectors.latest_video_card,
                "[data-testid*='card']",
                ".card",
            ]),
            "download_button": (False, False, [
                self.config.selectors.download_button,
                "[data-testid*='download']",
                "a[href*='.mp4']",
            ]),
        }

        report: dict[str, dict[str, object]] = {}
        for label, (exact_one, require_visible, candidates) in requirements.items():
            resolved, info = self._resolve_selector(candidates=candidates, exact_one=exact_one, require_visible=require_visible)
            report[label] = info
            if resolved is None:
                self._preflight_report = report
                raise PreflightError(f"Preflight failed: {label} no candidate matched. report={report}")
            self._resolved[label] = resolved

        self._preflight_report = report
        return report

    def _resolve_selector(
        self,
        candidates: list[str],
        exact_one: bool,
        require_visible: bool,
    ) -> tuple[str | None, dict[str, object]]:
        stats: list[dict[str, object]] = []
        for selector in candidates:
            locator = self.page.locator(selector)
            count = locator.count()
            visible = sum(1 for idx in range(count) if locator.nth(idx).is_visible())
            stats.append({"selector": selector, "count": count, "visible": visible})

            visible_ok = visible >= 1 if require_visible else count >= 1
            if exact_one:
                if count == 1 and visible_ok:
                    return selector, {"selected": selector, "candidates": stats}
            else:
                if count >= 1 and visible_ok:
                    return selector, {"selected": selector, "candidates": stats}
        return None, {"selected": None, "candidates": stats}

    def _sel(self, label: str, fallback: str) -> str:
        return self._resolved.get(label, fallback)

    def _first_prefer_visible(self, selector: str) -> Locator:
        loc = self.page.locator(selector)
        if loc.count() < 1:
            raise PageControlError(f"Selector not found: {selector}")
        for idx in range(loc.count()):
            node = loc.nth(idx)
            if node.is_visible():
                return node
        return loc.first

    def set_mode(self, mode_value: str) -> None:
        """Select generation mode tab best-effort and verify mode consistency."""
        mapping = {
            "text2video": ["全能参考", "文生视频", "文本", "Text"],
            "first_frame": ["首帧", "首图", "First Frame"],
            "first_last_frame": ["首尾帧", "首尾", "First/Last"],
            "extend": ["续写", "扩展", "Extend"],
        }
        candidates = mapping.get(mode_value, [mode_value])

        tabs = self.page.locator(self._sel("mode_tab", self.config.selectors.mode_tab))
        if tabs.count() < 1:
            raise PageControlError("未找到模式选择区域")

        for label in candidates:
            node = tabs.filter(has_text=label)
            if node.count() > 0:
                target = node.first
                target.scroll_into_view_if_needed()
                target.click(timeout=3_000)
                current = self.current_mode_label().lower()
                if label.lower()[:2] in current or label.lower() in current:
                    return

        current = self.current_mode_label()
        raise PageControlError(f"模式选择失败: 期望 {mode_value}, 当前 {current}")

    def current_mode_label(self) -> str:
        """Return currently selected mode text from UI when available."""
        selected = self.page.locator(self.config.selectors.selected_mode)
        if selected.count() > 0:
            return selected.first.inner_text().strip()
        tabs = self.page.locator(self._sel("mode_tab", self.config.selectors.mode_tab))
        if tabs.count() > 0:
            return tabs.first.inner_text().strip()
        return "unknown"

    def set_prompt_with_verification(self, prompt: str) -> None:
        """Fill prompt and verify read-back value to avoid accidental generation."""
        if not prompt.strip():
            raise PageControlError("Prompt is empty; generation is blocked")
        field = self._first_prefer_visible(self._sel("prompt_textarea", self.config.selectors.prompt_textarea))
        field.fill(prompt)
        if field.input_value().strip() != prompt.strip():
            raise PageControlError("Prompt writeback verification failed")

    def ensure_option_selected(self, label: str, value: str) -> None:
        """Select model/ratio/duration with retry strategies and verification."""
        mapping = {
            "model": self._sel("model_dropdown", self.config.selectors.model_dropdown),
            "ratio": self._sel("ratio_dropdown", self.config.selectors.ratio_dropdown),
            "duration": self._sel("duration_dropdown", self.config.selectors.duration_dropdown),
        }
        selector = mapping.get(label)
        if selector is None:
            raise PageControlError(f"Unknown option label: {label}")

        last_err = ""
        for _ in range(3):
            try:
                control = self._first_prefer_visible(selector)
                control.scroll_into_view_if_needed()
                control.click(timeout=3_000)

                role_option = self.page.get_by_role("option", name=value)
                if role_option.count() > 0:
                    role_option.first.click(timeout=3_000)
                else:
                    option = self.page.locator(self.config.selectors.option_items).filter(has_text=value)
                    if option.count() == 0:
                        option = self.page.locator(f"[aria-selected][data-value='{value}'], [data-value='{value}']")
                    if option.count() == 0:
                        option = self.page.get_by_text(value, exact=True)
                    if option.count() == 0:
                        raise PageControlError(f"{label} option not found for value '{value}'")
                    option.first.click(timeout=3_000)

                selected_text = control.inner_text().strip().lower()
                if value.strip().lower() in selected_text:
                    return
                selected = self.page.locator("[role='option'][aria-selected='true']").filter(has_text=value)
                if selected.count() > 0:
                    return
                last_err = f"{label} selection not reflected in UI"
            except Exception as exc:  # noqa: BLE001
                last_err = str(exc)
                self.page.keyboard.press("Escape")
                continue

        raise PageControlError(f"{label} selection verification failed for '{value}': {last_err}")

    def set_reference_files(self, paths: tuple[Path, ...]) -> bool:
        """Upload files directly through input[type=file] without opening file chooser."""
        if not paths:
            return False
        for path in paths:
            if not path.exists() or path.stat().st_size <= 0:
                raise PageControlError(f"当前缺少可上传的本地文件路径/素材下载失败: {path}")

        selector = self._sel("upload_input", self.config.selectors.upload_input)

        try:
            self.page.set_input_files(selector, [str(path) for path in paths], timeout=5_000)
            marker = self.page.locator(self.config.selectors.uploaded_asset_marker)
            if marker.count() > 0:
                return True
        except Exception:
            pass

        inputs = self.page.locator(selector)
        if inputs.count() < 1:
            raise PageControlError("未找到可用上传 input[type=file]")

        last_err = ""
        for idx in range(inputs.count()):
            node = inputs.nth(idx)
            try:
                node.set_input_files([str(path) for path in paths], timeout=5_000)
                if self._upload_verified(node):
                    return True
            except Exception as exc:  # noqa: BLE001
                last_err = str(exc)
                continue

        raise PageControlError(f"上传失败：未能通过 input[type=file] 写入文件。{last_err}")

    def _upload_verified(self, input_node: Locator) -> bool:
        marker = self.page.locator(self.config.selectors.uploaded_asset_marker)
        if marker.count() > 0:
            return True
        try:
            file_count = input_node.evaluate("(el) => (el.files ? el.files.length : 0)")
            return int(file_count) > 0
        except Exception:  # noqa: BLE001
            return False

    def click_generate(self) -> None:
        """Click generate button with robust interactability checks."""
        button = self._first_prefer_visible(self._sel("generate_button", self.config.selectors.generate_button))
        last_err = ""
        for _ in range(3):
            try:
                button.scroll_into_view_if_needed()
                disabled = button.evaluate("(el) => el.disabled || el.getAttribute('aria-disabled') === 'true'")
                if disabled:
                    raise PageControlError("生成按钮当前为禁用态")
                button.click(timeout=3_000)
                return
            except Exception as exc:  # noqa: BLE001
                last_err = str(exc)
                self.ensure_generate_clickable()
                try:
                    button.click(timeout=3_000, force=True)
                    return
                except PlaywrightTimeoutError:
                    self.page.keyboard.press("Enter")
                    continue
        raise PageControlError(f"点击生成失败: {last_err}")

    def ensure_generate_clickable(self) -> None:
        """Try to make generate button interactable for retry clicks."""
        button = self._first_prefer_visible(self._sel("generate_button", self.config.selectors.generate_button))
        button.scroll_into_view_if_needed()
        for selector in ("button:has-text('关闭')", "button:has-text('稍后')", "[aria-label='Close']", ".guide-close", ".modal-close"):
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
        cards = self.page.locator(self._sel("latest_video_card", self.config.selectors.latest_video_card))
        return cards.count() if cards.count() > 0 else self.page.locator(self._sel("latest_video", self.config.selectors.latest_video)).count()

    def has_generate_busy_indicator(self) -> bool:
        """Check whether generate button enters busy state."""
        return self.page.locator(self.config.selectors.generate_busy).count() > 0

    def latest_video_container(self, src_hint: str | None = None) -> Locator:
        """Return video container optionally matched by src hint."""
        card_selector = self._sel("latest_video_card", self.config.selectors.latest_video_card)
        video_selector = self._sel("latest_video", self.config.selectors.latest_video)
        cards = self.page.locator(card_selector)
        if src_hint and cards.count() > 0:
            matched = cards.filter(has=self.page.locator(f"video[src*='{src_hint}']"))
            if matched.count() > 0:
                return matched.first
        if cards.count() > 0:
            return cards.last
        videos = self.page.locator(video_selector)
        if videos.count() < 1:
            raise PageControlError("No latest video container could be located")
        return videos.last.locator("xpath=ancestor-or-self::*[1]")

    def explicit_failure_messages(self) -> list[str]:
        """Collect explicit generation failure messages from visible UI text only."""
        messages: list[str] = []
        candidates = self.toast_messages() + self.form_errors()

        cards = self.page.locator(self._sel("latest_video_card", self.config.selectors.latest_video_card))
        if cards.count() > 0:
            for idx in range(min(cards.count(), 3)):
                txt = cards.nth(idx).inner_text().strip()
                if txt:
                    candidates.append(txt)

        for text in candidates:
            lowered = text.lower()
            if any(keyword.lower() in lowered for keyword in self.config.explicit_failure_keywords):
                messages.append(text)

        dedup: list[str] = []
        seen: set[str] = set()
        for msg in messages:
            if msg not in seen:
                seen.add(msg)
                dedup.append(msg)
        return dedup

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
        scoped_button = container.locator(self._sel("download_button", self.config.selectors.download_button))
        if scoped_button.count() < 1:
            raise PageControlError("Scoped download button not found in latest video container")
        scoped_button.first.click()
