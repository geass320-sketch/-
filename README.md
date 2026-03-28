# Jimeng Web Automation Pipeline

This repository provides a production-oriented Playwright pipeline for **即梦网页版（Jimeng Web）** video generation.

## Migration status

- Runtime terminology and defaults have been switched to Jimeng web.
- Selector defaults include Chinese UI labels.
- Planner keeps backward compatibility (`SeedancePlanner` alias still available).

## Authentication modes (important for Jimeng)

Jimeng often keeps auth in **localStorage token** rather than plain cookies. Use any of the following:

1. `--storage-state`: Playwright `storage_state.json` (recommended)
2. `--local-storage`: JSON object injected into localStorage before navigation
3. `--cookies`: old cookie-list mode (fallback only)

At least one auth source is required.

## Run the pipeline

Requirements:
- Python 3.11+
- `playwright` installed and browser binaries available
- A valid auth source (`--storage-state` / `--local-storage` / `--cookies`)

### Single video

```bash
python auto_gen.py \
  --base-url "https://jimeng.jianying.com" \
  --storage-state ./storage_state.json \
  --prompt "一只机械狐狸在霓虹雨夜中奔跑，电影级跟拍镜头" \
  --model "Seedance 2.0" \
  --ratio "16:9" \
  --duration "5s" \
  --mode text2video \
  --output-dir ./downloads
```

### Multiple videos (wait until all tasks complete and return results)

```bash
python auto_gen.py \
  --base-url "https://jimeng.jianying.com" \
  --local-storage ./jimeng_local_storage.json \
  --prompt "一只机械狐狸在霓虹雨夜中奔跑，电影级跟拍镜头" \
  --model "Seedance 2.0" \
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

## Upload reliability strategy for Jimeng UI

The pipeline now uses a two-step fallback:
1. direct file-input set + synthetic `input/change` events;
2. click upload UI and use Playwright file chooser.

If both fail, it raises an explicit upload error indicating likely anti-automation checks.

## Windows PowerShell note

If you need to run multiple commands in legacy PowerShell and `&&` fails, put them in a `.bat` file or run commands in separate lines.

`auto_gen.py` remains the main entrypoint for external orchestrators and only downloads videos after validation gates pass.


## Release checklist

Before publishing, run:

```bash
python -m compileall auto_gen.py config.py page_controller.py models.py seedance_planner.py video_inspector.py validator.py
python -m unittest tests/test_local_storage_payload.py
```
