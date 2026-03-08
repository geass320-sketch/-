"""Main entrypoint for Seedance generation automation pipeline."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from playwright.sync_api import BrowserContext, sync_playwright

from config import PipelineConfig
from frame_tools import ensure_frame_exists
from models import GenerationMode, GenerationRequest
from page_controller import PageController
from seedance_planner import SeedancePlanner
from validator import VideoValidator
from video_inspector import VideoInspectionError, VideoInspector


class PipelineError(RuntimeError):
    """Top-level pipeline execution error."""


def _load_cookies(context: BrowserContext, cookies_path: Path) -> None:
    """Load persisted cookies into browser context."""
    if not cookies_path.exists():
        raise PipelineError(f"Cookie file not found: {cookies_path}")
    data = json.loads(cookies_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise PipelineError("Cookie file must contain a JSON list")
    context.add_cookies(data)


def run_pipeline(config: PipelineConfig, request: GenerationRequest, previous_video_src: str | None = None) -> str:
    """Run one generation cycle and return validated video src."""
    planner = SeedancePlanner()
    plan = planner.build_plan(request)

    if request.mode in {GenerationMode.FIRST_FRAME, GenerationMode.FIRST_LAST_FRAME}:
        for idx, path in enumerate(plan.required_images, start=1):
            ensure_frame_exists(path, f"continuation_{idx}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        _load_cookies(context, config.cookies_path)
        page = context.new_page()

        controller = PageController(page=page, config=config)
        inspector = VideoInspector(page=page, config=config)
        validator = VideoValidator(config.thresholds)

        controller.navigate()
        controller.set_prompt_with_verification(plan.compiled_prompt)
        controller.ensure_option_selected("model", request.model)
        controller.ensure_option_selected("ratio", request.ratio)
        controller.ensure_option_selected("duration", request.duration)
        controller.upload_images(plan.required_images)
        controller.click_generate()

        deadline = time.time() + config.max_wait_seconds
        last_error = "Timed out waiting for valid generated video"
        while time.time() < deadline:
            time.sleep(config.poll_interval_seconds)
            try:
                metadata = inspector.latest_metadata()
            except VideoInspectionError as exc:
                last_error = str(exc)
                continue
            result = validator.validate(metadata, previous_video_src)
            if result.ok:
                config.output_dir.mkdir(parents=True, exist_ok=True)
                with page.expect_download(timeout=config.default_timeout_ms) as dl:
                    controller.trigger_download()
                download = dl.value
                download.save_as(str(config.output_dir / download.suggested_filename))
                browser.close()
                return metadata.src
            last_error = result.reason

        browser.close()
        raise PipelineError(last_error)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seedance auto generation pipeline")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--cookies", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--ratio", required=True)
    parser.add_argument("--duration", required=True)
    parser.add_argument("--mode", choices=[mode.value for mode in GenerationMode], default=GenerationMode.TEXT2VIDEO.value)
    parser.add_argument("--first-frame")
    parser.add_argument("--last-frame")
    parser.add_argument("--previous-shot-summary")
    parser.add_argument("--previous-video-src")
    parser.add_argument("--output-dir", default="downloads")
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint for external orchestrators."""
    args = _parse_args()
    request = GenerationRequest(
        prompt=args.prompt,
        model=args.model,
        ratio=args.ratio,
        duration=args.duration,
        mode=GenerationMode(args.mode),
        first_frame_path=Path(args.first_frame) if args.first_frame else None,
        last_frame_path=Path(args.last_frame) if args.last_frame else None,
        previous_shot_summary=args.previous_shot_summary,
    )
    config = PipelineConfig(
        base_url=args.base_url,
        cookies_path=Path(args.cookies),
        output_dir=Path(args.output_dir),
    )
    src = run_pipeline(config=config, request=request, previous_video_src=args.previous_video_src)
    print(src)


if __name__ == "__main__":
    main()
