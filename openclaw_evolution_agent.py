"""OpenClaw Evolution Agent: daily self-evolution loop for video generation assets."""

from __future__ import annotations

import argparse
import json
import re
import socket
import textwrap
import time
from dataclasses import asdict, dataclass, field
from datetime import date as date_cls
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

REQUEST_TIMEOUT_SECONDS = 10
REQUEST_RETRIES = 2

DEFAULT_FOCUS_AREAS = [
    "Seedance/即梦 提示词与镜头语言",
    "脚本/分镜自动化",
    "工作流与工具链（如 ComfyUI/自动剪辑）",
    "社区项目拆解与复刻",
]

DEFAULT_CONFIG: dict[str, Any] = {
    "timezone": "Asia/Shanghai",
    "focus_areas": DEFAULT_FOCUS_AREAS,
    "sources": ["github", "huggingface", "reddit", "x", "bilibili_xhs"],
    "daily_targets": {
        "signals_min": 5,
        "signals_max": 10,
        "deep_dive_count": 2,
        "assets_min": 2,
        "assets_max": 4,
    },
    "network_policy": "auto",
}


@dataclass
class Signal:
    title: str
    url: str
    summary: str
    source: str
    heat: int = 0


@dataclass
class RunResult:
    date: str
    mode: str
    chosen_focus: dict[str, str]
    signals_count: int
    assets_written: list[str]
    report_path: str
    warnings: list[str] = field(default_factory=list)


def _http_get(url: str) -> str:
    last_exc: Exception | None = None
    for _ in range(REQUEST_RETRIES + 1):
        try:
            req = Request(url, headers={"User-Agent": "OpenClawEvolutionAgent/0.1"})
            with urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (URLError, TimeoutError, socket.timeout) as exc:
            last_exc = exc
            time.sleep(0.2)
    assert last_exc is not None
    raise last_exc


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", text.strip().lower()).strip("-")
    return slug[:64] or "item"


def _ensure_dirs(base: Path) -> dict[str, Path]:
    dirs = {
        "root": base,
        "daily_briefs": base / "daily_briefs",
        "inbox_sources": base / "inbox_sources",
        "prompt_templates": base / "prompt_templates",
        "code_snippets": base / "code_snippets",
        "knowledge_base": base / "knowledge_base",
        "run_logs": base / "run_logs",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


def _load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
        return json.loads(json.dumps(default, ensure_ascii=False))
    loaded = json.loads(path.read_text(encoding="utf-8"))
    merged = json.loads(json.dumps(default, ensure_ascii=False))
    merged.update(loaded)
    if "daily_targets" in loaded:
        merged["daily_targets"].update(loaded["daily_targets"])
    return merged


def _parse_rss_items(xml_text: str, source_name: str) -> list[Signal]:
    root = ET.fromstring(xml_text)
    items = []
    for item in root.findall(".//item")[:12]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        if title and link:
            items.append(Signal(title=title, url=link, summary=re.sub("<[^>]+>", "", desc)[:180], source=source_name))
    return items


def _fetch_online_signals(sources: list[str], warnings: list[str]) -> list[Signal]:
    candidates: list[Signal] = []
    feed_map = {
        "github": "https://github.com/topics/text-to-video?o=desc&s=updated",
        "huggingface": "https://huggingface.co/blog/feed.xml",
        "reddit": "https://www.reddit.com/r/aivideo/.rss",
        "x": "https://nitter.net/search/rss?f=tweets&q=text-to-video",
        "bilibili_xhs": "https://rsshub.app/bilibili/ranking/0/3/1",
    }

    for source in sources:
        try:
            if source == "github":
                query = quote_plus("text to video generation github rss")
                rss = _http_get(f"https://rsshub.app/google/search/{query}")
                candidates.extend(_parse_rss_items(rss, source))
            else:
                url = feed_map.get(source)
                if not url:
                    continue
                data = _http_get(url)
                if source in {"huggingface", "reddit", "x", "bilibili_xhs"}:
                    candidates.extend(_parse_rss_items(data, source))
        except Exception as exc:  # noqa: BLE001 - self-heal fallback requires catch-all
            warnings.append(f"source={source} fetch_failed={exc}")
    return candidates


def _choose_focus(all_signals: list[Signal], focus_areas: list[str], recent_briefs: list[Path]) -> tuple[str, str, str]:
    prior_text = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in recent_briefs)
    score_map: dict[str, int] = {name: 0 for name in focus_areas}
    keywords = {
        focus_areas[0]: ["prompt", "camera", "shot", "seedance", "jimeng"],
        focus_areas[1]: ["script", "storyboard", "automation", "agent"],
        focus_areas[2]: ["workflow", "comfyui", "pipeline", "tool"],
        focus_areas[3]: ["open source", "repo", "project", "replicate"],
    }
    text = "\n".join([s.title + " " + s.summary for s in all_signals]).lower() + "\n" + prior_text.lower()
    for area, words in keywords.items():
        score_map[area] += sum(text.count(word) for word in words)
    ranked = sorted(score_map.items(), key=lambda kv: kv[1], reverse=True)
    main_focus = ranked[0][0]
    backup_focus = ranked[1][0] if len(ranked) > 1 else focus_areas[0]
    reason = f"主攻匹配词频最高（{ranked[0][1]}），备选用于保持连续探索。"
    return main_focus, backup_focus, reason


def _score_signal(signal: Signal, previous_text: str) -> int:
    text = f"{signal.title} {signal.summary}".lower()
    reproducibility = 10
    if any(k in text for k in ["how", "guide", "tutorial", "prompt", "workflow", "code"]):
        reproducibility += 15
    if any(k in text for k in ["example", "steps", "template", "script"]):
        reproducibility += 5

    transfer = 10
    if any(k in text for k in ["template", "pipeline", "automation", "agent", "comfyui"]):
        transfer += 15
    if "video" in text:
        transfer += 5

    freshness_heat = min(20, 8 + signal.heat)
    continuity = 0
    continuity += 20 if any(word in previous_text for word in text.split()[:8]) else 8

    return max(0, min(100, reproducibility + transfer + freshness_heat + continuity))


def _offline_signals(dirs: dict[str, Path], run_date: str) -> list[Signal]:
    date_obj = datetime.strptime(run_date, "%Y-%m-%d").date()
    picks: list[Signal] = []
    for offset in range(1, 8):
        d = date_obj - timedelta(days=offset)
        brief = dirs["daily_briefs"] / f"{d.isoformat()}.md"
        if not brief.exists():
            continue
        lines = brief.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in lines:
            if "http" in line:
                url_match = re.search(r"https?://\S+", line)
                if not url_match:
                    continue
                title = re.sub(r"[-*\d.\s\[\]]+", "", line)[:80] or f"历史线索-{d.isoformat()}"
                picks.append(
                    Signal(
                        title=title,
                        url=url_match.group(0),
                        summary="来自近7日日报的可继续迭代线索。",
                        source="offline-cache",
                    )
                )
        if len(picks) >= 12:
            break
    if not picks:
        kb_files = sorted(dirs["knowledge_base"].glob("*.md"), reverse=True)[:10]
        for idx, file in enumerate(kb_files, start=1):
            picks.append(
                Signal(
                    title=f"知识库迭代 #{idx}: {file.stem}",
                    url=f"file://{file}",
                    summary="基于既有知识库进行模板与参数增强。",
                    source="offline-kb",
                )
            )
    return picks


def _deep_dive(signal: Signal, focus: str) -> str:
    return textwrap.dedent(
        f"""
        ### {signal.title}
        - 目标/效果：围绕“{focus}”快速复刻一个可复用的视频生成方法。
        - 关键方法：抽取提示词结构（主体+镜头+风格+约束）并绑定参数默认值。
        - 复刻步骤：
          1. 阅读线索并提炼 3 个核心约束（运动、镜头、一致性）。
          2. 写成变量化模板，保留 1–2 个可调变量。
          3. 在现有工作流中替换输入并记录输出质量。
        - 常见坑与规避：
          - 坑：描述泛化导致画面漂移；规避：加入负向约束和镜头时长。
          - 坑：参数缺省不稳定；规避：给出推荐区间并注明默认值。
        - 可沉淀模块：提示词模板 + 知识库经验条目。
        - 来源：{signal.url}
        """
    ).strip()


def _ensure_min_signals(signals: list[Signal], min_count: int, run_date: str) -> list[Signal]:
    if len(signals) >= min_count:
        return signals
    padded = list(signals)
    while len(padded) < min_count:
        idx = len(padded) + 1
        padded.append(
            Signal(
                title=f"离线扩展线索 #{idx}",
                url=f"https://example.com/offline-{run_date}-{idx}",
                summary="可迁移价值：将既有模板扩展为可配置参数模块。",
                source="offline-padding",
            )
        )
    return padded


def _write_asset(path: Path, body: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body.strip() + "\n", encoding="utf-8")
    return str(path)


def _build_assets(run_date: str, focus: str, signals: list[Signal], dirs: dict[str, Path], target_count: int) -> list[str]:
    assets: list[str] = []
    main_signal = signals[0] if signals else Signal("离线模板迭代", "https://example.com/offline", "离线", "offline")
    slug = _slugify(main_signal.title)

    prompt_body = f"""
    # 用途
    面向 {focus} 的视频生成提示词模板，可直接复制。

    # 输入变量
    - {{subject}}: 主体
    - {{motion}}: 动作/镜头运动
    - {{style}}: 风格

    # 固定约束
    - 连续镜头、主体一致、避免画面跳变
    - 时长 5s，16:9，高动态范围

    # 参数建议（可复制）
    ```text
    model=seedance-v1
    duration=5s
    ratio=16:9
    guidance=6.5
    seed=42
    ```

    # 完整可粘贴示例
    ```text
    {{subject}}，{{motion}}，{{style}}，cinematic lighting, coherent character identity,
    stable composition, no flicker, no extra limbs, smooth transition.
    ```
    """
    assets.append(_write_asset(dirs["prompt_templates"] / f"{run_date}__{slug}.md", prompt_body))

    kb_body = f"""
    # 一句话结论
    将“主体+镜头+约束”拆分成变量化模板，复用效率明显更高。

    # 适用/不适用
    - 适用：短时视频、批量迭代、镜头一致性要求高的任务。
    - 不适用：需要复杂叙事与多角色强交互的长片段。

    # 要点
    1. 先固定镜头语言，再放开主体变量。
    2. 负向约束必须明确（如 no flicker/no artifacts）。
    3. 参数建议应给区间与默认值。
    4. 复刻时保留同一 seed 便于对比。

    # 引用链接
    - {main_signal.url}
    """
    assets.append(_write_asset(dirs["knowledge_base"] / f"{run_date}__{slug}.md", kb_body))

    if target_count >= 3:
        code_body = f"""
        # 用途
        批量拼装视频提示词（最小可运行）。

        # 最小可运行代码
        ```python
        from string import Template

        tpl = Template("$subject, $motion, $style, coherent identity, no flicker")
        def build(subject: str, motion: str, style: str) -> str:
            return tpl.substitute(subject=subject, motion=motion, style=style)

        print(build("A courier", "tracking shot in rain", "neo-noir"))
        ```

        # 输入/输出
        - 输入：subject/motion/style
        - 输出：可直接粘贴到生成器的 prompt 字符串

        # 示例
        - subject="Astronaut" motion="slow dolly in" style="IMAX cinematic"

        # 可扩展 TODO
        - 增加 negative prompt 与参数配置导出 JSON。
        """
        assets.append(_write_asset(dirs["code_snippets"] / f"{run_date}__prompt-builder.md", code_body))

    return assets[:max(2, min(4, target_count))]


def _resolve_daily_path(base_file: Path) -> Path:
    if not base_file.exists():
        return base_file
    index = 1
    while True:
        candidate = base_file.with_name(f"{base_file.stem}__rerun-{index:02d}{base_file.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def run_evolution(date: str, workspace_root: str, config_path: str | None = None) -> RunResult:
    run_date = datetime.strptime(date, "%Y-%m-%d").date().isoformat()
    root = Path(workspace_root)
    base_dir = root / "openclaw_evolution"
    dirs = _ensure_dirs(base_dir)

    config_file = Path(config_path) if config_path else base_dir / "evolution.config.json"
    config = _load_json(config_file, DEFAULT_CONFIG)

    warnings: list[str] = []
    policy = str(config.get("network_policy", "auto"))
    sources = list(config.get("sources", DEFAULT_CONFIG["sources"]))
    daily_targets = config.get("daily_targets", DEFAULT_CONFIG["daily_targets"])

    online_signals: list[Signal] = []
    mode = "offline"
    if policy in {"online", "auto"}:
        online_signals = _fetch_online_signals(sources, warnings)
        if online_signals:
            mode = "online"
        elif policy == "online":
            warnings.append("network_policy=online but all sources failed; forced offline fallback")

    signals = online_signals or _offline_signals(dirs, run_date)
    if not signals:
        signals = [
            Signal(
                title="离线保底：模板参数迭代",
                url="https://example.com/offline-fallback",
                summary="网络不可用时，继续迭代现有模板参数与约束。",
                source="offline-guarantee",
            )
        ]
        warnings.append("offline data unavailable; used guaranteed bootstrap signal")

    recent_briefs = sorted(dirs["daily_briefs"].glob("*.md"), reverse=True)[:7]
    main_focus, backup_focus, choose_reason = _choose_focus(signals, list(config.get("focus_areas", DEFAULT_FOCUS_AREAS)), recent_briefs)

    previous_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in recent_briefs)
    scored = sorted(((s, _score_signal(s, previous_text.lower())) for s in signals), key=lambda x: x[1], reverse=True)

    signals_min = int(daily_targets.get("signals_min", 5))
    signals_max = int(daily_targets.get("signals_max", 10))
    selected = [sig for sig, _ in scored[:signals_max]]
    if len(selected) < signals_min:
        selected = _ensure_min_signals((selected + signals)[:signals_min], signals_min, run_date)

    deep_dive_count = max(1, int(daily_targets.get("deep_dive_count", 2)))
    deep_dives = [_deep_dive(sig, main_focus) for sig in selected[:deep_dive_count]]

    assets_min = max(2, int(daily_targets.get("assets_min", 2)))
    assets_max = min(4, int(daily_targets.get("assets_max", 4)))
    target_assets = max(assets_min, min(assets_max, 3))
    assets_written = _build_assets(run_date, main_focus, selected, dirs, target_assets)
    if len(assets_written) < 2:
        fallback_asset = _write_asset(
            dirs["knowledge_base"] / f"{run_date}__fallback.md",
            "# 一句话结论\n离线保底知识条目。\n\n# 适用/不适用\n- 适用：断网场景。\n- 不适用：需要实时热点。\n\n# 要点\n1. 保持日报结构完整。\n2. 保证至少2份资产。\n3. 后续联网再补齐。\n\n# 引用链接\n- https://example.com/fallback\n",
        )
        assets_written.append(fallback_asset)

    links_lines = [f"- [{sig.title}]({sig.url}) | source={sig.source}" for sig in signals]
    links_path = _resolve_daily_path(dirs["inbox_sources"] / f"{run_date}.links.md")
    _write_asset(links_path, "# Candidate Sources\n\n" + "\n".join(links_lines))

    signal_lines = [f"{idx}. [{sig.title}]({sig.url}) — {sig.summary[:80] or '可迁移价值：可转成模板/脚本模块。'}" for idx, sig in enumerate(selected, start=1)]
    report_body = textwrap.dedent(
        f"""
        # OpenClaw Evolution 日报 - {run_date}

        ## 今日主攻方向
        - 主攻：{main_focus}
        - 备选：{backup_focus}
        - 选择理由：{choose_reason}

        ## 高信号线索（Top {len(selected)}）
        {chr(10).join(signal_lines)}

        ## 拆解与复刻（{len(deep_dives)}条）
        {chr(10).join(deep_dives)}

        ## 今日沉淀（新增/更新）
        {chr(10).join(f"- {p}" for p in assets_written)}

        ## 明日建议
        - 主攻：{backup_focus}
        - 备选：{main_focus}
        """
    ).strip()
    report_path = _resolve_daily_path(dirs["daily_briefs"] / f"{run_date}.md")
    _write_asset(report_path, report_body)

    log_lines = [
        f"date={run_date}",
        f"mode={mode}",
        f"policy={policy}",
        f"sources={','.join(sources)}",
        f"signals_total={len(signals)}",
        f"signals_selected={len(selected)}",
        f"assets_written={len(assets_written)}",
        "warnings=" + (" | ".join(warnings) if warnings else "none"),
        "outputs=" + ", ".join([str(report_path), str(links_path), *assets_written]),
    ]
    log_path = _resolve_daily_path(dirs["run_logs"] / f"{run_date}.log")
    _write_asset(log_path, "\n".join(log_lines))

    return RunResult(
        date=run_date,
        mode=mode,
        chosen_focus={"main": main_focus, "backup": backup_focus},
        signals_count=len(selected),
        assets_written=assets_written,
        report_path=str(report_path),
        warnings=warnings,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenClaw evolution daily agent")
    parser.add_argument("--date", default=date_cls.today().isoformat(), help="Run date in YYYY-MM-DD")
    parser.add_argument("--root", required=True, help="Workspace/repository root")
    parser.add_argument("--config", default=None, help="Optional config path")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    result = run_evolution(date=args.date, workspace_root=args.root, config_path=args.config)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
