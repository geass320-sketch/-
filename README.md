# Jimeng Web Automation Pipeline

This repository provides a production-oriented Playwright pipeline for **即梦网页版（Jimeng Web）** video generation.

## What was changed from the old Seedance-style template

- Updated terminology and docs to Jimeng web.
- Added Jimeng-oriented selector defaults in `config.py` (Chinese UI labels included).
- Kept backwards compatibility in planner naming (`SeedancePlanner` alias) so old imports still work.

## Run the pipeline

Requirements:
- Python 3.11+
- `playwright` installed and browser binaries available
- Valid Jimeng/Jianying web cookies

Single video:

```bash
python auto_gen.py \
  --base-url "https://jimeng.jianying.com" \
  --cookies ./cookies.json \
  --prompt "一只机械狐狸在霓虹雨夜中奔跑，电影级跟拍镜头" \
  --model "Seedance 2.0" \
  --ratio "16:9" \
  --duration "5s" \
  --mode text2video \
  --output-dir ./downloads
```

Multiple videos (wait until all tasks complete and return results):

```bash
python auto_gen.py \
  --base-url "https://jimeng.jianying.com" \
  --cookies ./cookies.json \
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

`auto_gen.py` remains the main entrypoint for external orchestrators and only downloads videos after validation gates pass.
