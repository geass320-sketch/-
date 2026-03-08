# Seedance Automation Pipeline

This repository provides a production-oriented refactor of a Jimeng/Seedance video generation workflow based on Playwright.

## Run the refactored pipeline

Requirements:
- Python 3.11+
- `playwright` installed and browser binaries available

Example:

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

Continuation examples:
- `--mode first_frame --first-frame ./assets/frame0.png`
- `--mode first_last_frame --first-frame ./assets/frame0.png --last-frame ./assets/frame1.png`

`auto_gen.py` remains the main entrypoint for external orchestrators and only downloads videos after validation gates pass.
