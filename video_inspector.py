"""Video inspection helpers for DOM video elements."""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from config import PipelineConfig
from models import VideoMetadata


class VideoInspectionError(RuntimeError):
    """Raised when video metadata cannot be obtained."""


class VideoInspector:
    """Read generated video metadata from the page."""

    def __init__(self, page: Page, config: PipelineConfig) -> None:
        self.page = page
        self.config = config

    def latest_video_locator(self) -> Locator:
        """Return locator for the newest video element."""
        videos = self.page.locator(self.config.selectors.latest_video)
        if videos.count() < 1:
            raise VideoInspectionError("No video element found")
        return videos.last

    def latest_src(self) -> str:
        """Return current source of latest video."""
        src = self.latest_video_locator().evaluate("(video) => video.currentSrc || video.src || ''")
        return str(src)

    def latest_metadata(self) -> VideoMetadata:
        """Return metadata of latest video element."""
        payload = self.latest_video_locator().evaluate(
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
        if int(payload["readyState"]) == 0:
            raise VideoInspectionError("Video is still loading (readyState=0)")
        return VideoMetadata(
            src=str(payload["src"]),
            duration=float(payload["duration"]),
            width=int(payload["width"]),
            height=int(payload["height"]),
        )

    def is_loading_src(self, src: str) -> bool:
        """Return whether src matches known loading patterns."""
        low = src.lower().strip()
        if not low:
            return True
        return any(part in low for part in self.config.loading_src_patterns)
