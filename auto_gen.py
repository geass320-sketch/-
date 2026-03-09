"""Main entrypoint for Seedance generation automation pipeline."""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlparse

from playwright.sync_api import BrowserContext, TimeoutError as PlaywrightTimeoutError, sync_playwright

from config import PipelineConfig
from frame_tools import ensure_frame_exists
from models import GenerationMode, GenerationOutput, GenerationRequest, VideoMetadata
from page_controller import PageControlError, PageController, PreflightError
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


def _download_file(url: str, path: Path) -> Path:
    """Download URL to local path and ensure file is non-empty."""
    try:
        import requests
    except ImportError as exc:
        raise PipelineError("素材下载失败：当前环境缺少 requests 依赖") from exc
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    path.write_bytes(response.content)
    if not path.exists() or path.stat().st_size <= 0:
        raise PipelineError(f"素材下载失败或为空文件: {url}")
    return path


def _prepare_reference_files(config: PipelineConfig, request: GenerationRequest, task_id: int) -> tuple[Path, ...]:
    """Prepare reference files from local paths and URLs; empty means text-only mode."""
    files: list[Path] = []
    for p in request.reference_paths:
        if not p.exists() or p.stat().st_size <= 0:
            raise PipelineError(f"当前缺少可上传的本地文件路径/素材下载失败: {p}")
        files.append(p)

    if request.first_frame_path is not None:
        files.append(ensure_frame_exists(request.first_frame_path, "first"))
    if request.last_frame_path is not None:
        files.append(ensure_frame_exists(request.last_frame_path, "last"))

    if request.reference_urls:
        config.temp_dir.mkdir(parents=True, exist_ok=True)
        for idx, url in enumerate(request.reference_urls, start=1):
            parsed = urlparse(url)
            suffix = Path(parsed.path).suffix or ".jpg"
            target = config.temp_dir / f"{task_id}_ref{idx}{suffix}"
            files.append(_download_file(url, target))

    return tuple(files)


def _validate_local_inputs(request: GenerationRequest, compiled_prompt: str) -> None:
    """Validate local inputs before browser automation starts."""
    if not compiled_prompt.strip():
        raise PipelineError("Compiled prompt is empty")
    if not request.prompt.strip():
        raise PipelineError("Prompt cannot be empty")


def _download_target_path(output_dir: Path, suggested_name: str, task_id: int) -> Path:
    """Build deterministic per-task download path to avoid overwrite collisions."""
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate = output_dir / f"task_{task_id}_{suggested_name}"
    if not candidate.exists():
        return candidate
    return output_dir / f"{candidate.stem}_{int(time.time() * 1000)}{candidate.suffix}"


def _collect_diagnostics(
    controller: PageController,
    mode_label: str,
    upload_ok: bool,
    prompt_len: int,
    old_src: str,
    new_src: str,
    old_card_count: int,
    new_card_count: int,
) -> str:
    """Collect runtime diagnostics for accurate error reporting."""
    payload = {
        "mode_ui": mode_label,
        "upload_ok": upload_ok,
        "prompt_len": prompt_len,
        "old_src": old_src,
        "new_src": new_src,
        "old_card_count": old_card_count,
        "new_card_count": new_card_count,
        "toast": controller.toast_messages(),
        "form_errors": controller.form_errors(),
    }
    return json.dumps(payload, ensure_ascii=False)


def _wait_for_trigger_ack(
    controller: PageController,
    old_card_count: int,
    timeout_seconds: int,
) -> bool:
    """Confirm generate click truly triggered a new generation lifecycle."""
    deadline = time.time() + timeout_seconds
    trigger_keywords = ("生成中", "排队", "处理中", "queue", "generating", "processing")
    while time.time() < deadline:
        if controller.has_generate_busy_indicator():
            return True
        if controller.card_count() > old_card_count:
            return True
        toast_text = " ".join(controller.toast_messages()).lower()
        if any(keyword.lower() in toast_text for keyword in trigger_keywords):
            return True
        time.sleep(0.5)
    return False


def _wait_for_completed_video(
    inspector: VideoInspector,
    controller: PageController,
    validator: VideoValidator,
    old_src: str,
    previous_video_src: str | None,
    timeout_seconds: int,
    poll_interval_seconds: float,
) -> VideoMetadata:
    """Wait until new src appears and metadata becomes valid (excluding 00:00 placeholder)."""
    deadline = time.time() + timeout_seconds
    last_error = "Timed out waiting for completed video metadata"
    while time.time() < deadline:
        time.sleep(poll_interval_seconds)
        try:
            metadata = inspector.latest_metadata()
        except VideoInspectionError as exc:
            last_error = str(exc)
            continue

        if inspector.is_loading_src(metadata.src):
            last_error = f"src still loading-like: {metadata.src}"
            continue
        if old_src and metadata.src == old_src:
            last_error = "src unchanged from pre-generate snapshot"
            continue
        if controller.has_zero_duration_marker(src_hint=metadata.src):
            last_error = "UI duration still 00:00 placeholder"
            continue

        result = validator.validate(metadata, previous_video_src)
        if result.ok:
            return metadata
        last_error = result.reason

    raise PipelineError(last_error)


def _download_with_fallback(
    page_controller: PageController,
    inspector: VideoInspector,
    save_path: Path,
    timeout_ms: int,
    new_src: str,
    old_src: str,
) -> None:
    """Download scoped to new card; fallback to direct URL when browser event fails."""
    if not new_src or (old_src and new_src == old_src):
        raise PipelineError("未检测到新视频生成，禁止下载")

    page = page_controller.page
    try:
        with page.expect_download(timeout=timeout_ms) as dl:
            page_controller.click_scoped_download(src_hint=new_src)
        dl.value.save_as(str(save_path))
        return
    except PlaywrightTimeoutError:
        pass

    src = inspector.latest_src()
    if src != new_src:
        src = new_src
    if inspector.is_loading_src(src):
        raise PipelineError("下载兜底失败：最新视频地址仍是占位/加载态")

    try:
        import requests
    except ImportError as exc:
        raise PipelineError("下载兜底依赖 requests，请安装后重试") from exc

    response = requests.get(src, timeout=60)
    response.raise_for_status()
    save_path.write_bytes(response.content)


def _ffprobe_summary(path: Path) -> dict[str, object]:
    """Return ffprobe summary for downloaded file."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_name,width,height",
        "-of",
        "json",
        str(path),
    ]
    try:
        return json.loads(subprocess.check_output(cmd, text=True))
    except Exception as exc:  # noqa: BLE001
        return {"warning": f"ffprobe unavailable or failed: {exc}"}


def run_single_generation(
    config: PipelineConfig,
    request: GenerationRequest,
    task_id: int,
    previous_video_src: str | None = None,
) -> GenerationOutput:
    """Run one validated generation task and return structured output."""
    plan_id = f"plan-{task_id}-{uuid4().hex[:8]}"
    logging.info("[plan=%s] start mode=%s", plan_id, request.mode.value)

    planner = SeedancePlanner()
    plan = planner.build_plan(request)
    _validate_local_inputs(request, plan.compiled_prompt)
    reference_files = _prepare_reference_files(config=config, request=request, task_id=task_id)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        _load_cookies(context, config.cookies_path)
        page = context.new_page()
        controller = PageController(page=page, config=config)
        inspector = VideoInspector(page=page, config=config)
        validator = VideoValidator(config.thresholds)

        controller.navigate()
        controller.preflight_selectors()
        mode_label = controller.current_mode_label()

        controller.set_prompt_with_verification(plan.compiled_prompt)
        controller.ensure_option_selected("model", request.model)
        controller.ensure_option_selected("ratio", request.ratio)
        controller.ensure_option_selected("duration", request.duration)

        upload_ok = controller.set_reference_files(reference_files)
        logging.info(
            "[plan=%s] preflight mode_ui=%s mode_req=%s upload_ok=%s prompt_len=%d",
            plan_id,
            mode_label,
            request.mode.value,
            upload_ok,
            len(plan.compiled_prompt),
        )
        if request.mode == GenerationMode.TEXT2VIDEO and "首" in mode_label:
            logging.warning("[plan=%s] 预期纯文生，但UI当前模式为 %s；允许继续", plan_id, mode_label)

        old_src = ""
        try:
            old_src = inspector.latest_src()
        except VideoInspectionError:
            old_src = ""
        old_card_count = controller.card_count()
        logging.info("[plan=%s] baseline old_src=%s old_card_count=%d", plan_id, old_src, old_card_count)

        controller.click_generate()
        if not _wait_for_trigger_ack(controller, old_card_count=old_card_count, timeout_seconds=config.trigger_timeout_seconds):
            controller.ensure_generate_clickable()
            controller.click_generate()
            if not _wait_for_trigger_ack(controller, old_card_count=old_card_count, timeout_seconds=config.trigger_timeout_seconds):
                diagnostics = _collect_diagnostics(
                    controller=controller,
                    mode_label=mode_label,
                    upload_ok=upload_ok,
                    prompt_len=len(plan.compiled_prompt),
                    old_src=old_src,
                    new_src="",
                    old_card_count=old_card_count,
                    new_card_count=controller.card_count(),
                )
                raise PipelineError(f"未检测到生成触发成功（可能没点到或被遮挡）: {diagnostics}")

        metadata = _wait_for_completed_video(
            inspector=inspector,
            controller=controller,
            validator=validator,
            old_src=old_src,
            previous_video_src=previous_video_src,
            timeout_seconds=config.max_wait_seconds,
            poll_interval_seconds=config.poll_interval_seconds,
        )
        logging.info(
            "[plan=%s] new_src=%s metadata={duration:%.3f,width:%d,height:%d}",
            plan_id,
            metadata.src,
            metadata.duration,
            metadata.width,
            metadata.height,
        )

        time.sleep(config.post_success_wait_seconds)
        save_path = _download_target_path(config.output_dir, "generated.mp4", task_id)
        _download_with_fallback(
            page_controller=controller,
            inspector=inspector,
            save_path=save_path,
            timeout_ms=config.default_timeout_ms,
            new_src=metadata.src,
            old_src=old_src,
        )

        probe = _ffprobe_summary(save_path)
        logging.info("[plan=%s] ffprobe=%s", plan_id, json.dumps(probe, ensure_ascii=False))
        browser.close()
        return GenerationOutput(task_id=task_id, video_src=metadata.src, download_path=save_path)


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

    task_outputs: dict[int, GenerationOutput] = {}
    with ThreadPoolExecutor(max_workers=min(concurrency, count)) as pool:
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
            try:
                task_outputs[task_id] = future.result()
            except (PreflightError, PageControlError, PipelineError) as exc:
                raise PipelineError(f"Task {task_id} failed: {exc}") from exc
    return [task_outputs[idx] for idx in sorted(task_outputs)]


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
    parser.add_argument("--end-state")
    parser.add_argument("--previous-shot-summary")
    parser.add_argument("--previous-video-src")
    parser.add_argument("--reference-path", action="append", default=[])
    parser.add_argument("--reference-url", action="append", default=[])
    parser.add_argument("--output-dir", default="downloads")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--concurrency", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint for external orchestrators."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
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
        end_state_hint=args.end_state,
        reference_paths=tuple(Path(p) for p in args.reference_path),
        reference_urls=tuple(args.reference_url),
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
    print(json.dumps([{"task_id": o.task_id, "video_src": o.video_src, "download_path": str(o.download_path)} for o in outputs], ensure_ascii=False))


if __name__ == "__main__":
    main()
