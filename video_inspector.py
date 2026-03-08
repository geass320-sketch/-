"""Video inspection helpers for DOM video elements."""

from __future__ import annotations

from playwright.sync_api import Page

from config import PipelineConfig
from models import VideoMetadata


class VideoInspectionError(RuntimeError):
    """Raised when video metadata cannot be obtained."""


class VideoInspector:
    """Read generated video metadata from the page."""

    def __init__(self, page: Page, config: PipelineConfig) -> None:
        self.page = page
        self.config = config

    def latest_metadata(self) -> VideoMetadata:
        """Return metadata of latest video element."""
        locator = self.page.locator(self.config.selectors.latest_video).first
        locator.wait_for(timeout=self.config.default_timeout_ms)
        payload = locator.evaluate(
            """
            (video) => ({
                src: video.currentSrc || video.src || '',
                duration: Number(video.duration || 0),
                width: Number(video.videoWidth || 0),
                height: Number(video.videoHeight || 0),
                readyState: Number(video.readyState || 0),
            })
            """
        )
        if payload["readyState"] == 0:
            raise VideoInspectionError("Video is still loading (readyState=0)")
        return VideoMetadata(
            src=str(payload["src"]),
            duration=float(payload["duration"]),
            width=int(payload["width"]),
            height=int(payload["height"]),
        )
