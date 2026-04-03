# Seedance Automation Pipeline

This repository provides a production-oriented refactor of a Jimeng/Seedance video generation workflow based on Playwright.

## Run the refactored pipeline

Requirements:
- Python 3.11+
- `playwright` installed and browser binaries available

Single video:

```bash
python auto_gen.py \
  --base-url "https://seedance.example.com/create" \
  --cookies ./cookies.json \
  --prompt "A cinematic tracking shot of a courier sprinting through neon rain" \
  --model "seedance-v1" \
  --ratio "16:9" \
  --duration "5s" \
  --mode text2video \
  --output-dir ./downloads
```

Multiple videos (wait until all tasks complete and return results):

```bash
python auto_gen.py \
  --base-url "https://seedance.example.com/create" \
  --cookies ./cookies.json \
  --prompt "A cinematic tracking shot of a courier sprinting through neon rain" \
  --model "seedance-v1" \
  --ratio "16:9" \
  --duration "5s" \
  --mode text2video \
  --count 3 \
  --concurrency 2 \
  --output-dir ./downloads
```

Continuation examples:
- `--mode first_frame --first-frame ./assets/frame0.png`
- `--mode first_last_frame --first-frame ./assets/frame0.png --last-frame ./assets/frame1.png`

`auto_gen.py` remains the main entrypoint for external orchestrators and only downloads videos after validation gates pass.

## OpenClaw Evolution Agent (daily self-evolution loop)

This repo also includes a minimum-viable daily evolution runner for video-generation knowledge/asset accumulation:

```bash
python openclaw_evolution_agent.py \
  --date 2026-04-03 \
  --root /path/to/repo
```

It creates/uses `openclaw_evolution/` and writes:
- `daily_briefs/YYYY-MM-DD.md`
- `inbox_sources/YYYY-MM-DD.links.md`
- 2-4 assets under `prompt_templates/`, `code_snippets/`, `knowledge_base/`
- `run_logs/YYYY-MM-DD.log`
