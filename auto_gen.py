"""Main entrypoint for Jimeng web generation automation pipeline."""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from pathlib import Path

from playwright.sync_api import BrowserContext, sync_playwright

from config import PipelineConfig
from frame_tools import ensure_frame_exists
from models import GenerationMode, GenerationOutput, GenerationRequest
from page_controller import PageController
from seedance_planner import JimengPlanner
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


def _validate_local_inputs(request: GenerationRequest, compiled_prompt: str) -> None:
    """Validate local frame inputs before browser automation starts."""
    if request.mode in {GenerationMode.FIRST_FRAME, GenerationMode.FIRST_LAST_FRAME}:
        if request.first_frame_path is not None:
            ensure_frame_exists(request.first_frame_path, "first")
        if request.mode == GenerationMode.FIRST_LAST_FRAME:
            ensure_frame_exists(request.last_frame_path, "last")
    if not compiled_prompt.strip():
        raise PipelineError("Compiled prompt is empty")


def _download_target_path(output_dir: Path, suggested_name: str, task_id: int) -> Path:
    """Build deterministic per-task download path to avoid overwrite collisions."""
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate = output_dir / f"task_{task_id}_{suggested_name}"
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    return output_dir / f"{stem}_{int(time.time() * 1000)}{suffix}"


def run_single_generation(
    config: PipelineConfig,
    request: GenerationRequest,
    task_id: int,
    previous_video_src: str | None = None,
) -> GenerationOutput:
    """Run one validated generation task and return structured output."""
    planner = JimengPlanner()
    plan = planner.build_plan(request)
    _validate_local_inputs(request, plan.compiled_prompt)

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
                with page.expect_download(timeout=config.default_timeout_ms) as dl:
                    controller.trigger_download()
                download = dl.value
                save_path = _download_target_path(config.output_dir, download.suggested_filename, task_id)
                download.save_as(str(save_path))
                browser.close()
                return GenerationOutput(task_id=task_id, video_src=metadata.src, download_path=save_path)
            last_error = result.reason

        browser.close()
        raise PipelineError(f"Task {task_id} failed: {last_error}")


def run_pipeline(
    config: PipelineConfig,
    request: GenerationRequest,
    previous_video_src: str | None = None,
    count: int = 1,
    concurrency: int = 1,
) -> list[GenerationOutput]:
    """Run one or many generation tasks and return only when all complete."""
    if count < 1:
        raise PipelineError("count must be >= 1")
    if concurrency < 1:
        raise PipelineError("concurrency must be >= 1")

    max_workers = min(concurrency, count)
    task_outputs: dict[int, GenerationOutput] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(
                run_single_generation,
                replace(config),
                replace(request),
                task_id,
                previous_video_src,
            ): task_id
            for task_id in range(1, count + 1)
        }

        for future in as_completed(futures):
            task_id = futures[future]
            result = future.result()
            task_outputs[task_id] = result

    return [task_outputs[idx] for idx in sorted(task_outputs)]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Jimeng web auto generation pipeline")
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
    parser.add_argument("--count", type=int, default=1, help="Number of videos to generate")
    parser.add_argument("--concurrency", type=int, default=1, help="Parallel workers for generation")
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
    outputs = run_pipeline(
        config=config,
        request=request,
        previous_video_src=args.previous_video_src,
        count=args.count,
        concurrency=args.concurrency,
    )
    print(
        json.dumps(
            [
                {
                    "task_id": output.task_id,
                    "video_src": output.video_src,
                    "download_path": str(output.download_path),
                }
                for output in outputs
            ],
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
