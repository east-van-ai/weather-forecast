# weather-forecast

Pulls a Japan Meteorological Agency (JMA) surface analysis PDF, runs it through
a local vision model on Apple Silicon, and stores the result in Salesforce.
No cloud AI. No GPU rental. No subscriptions. Just your Mac doing the work.

## Table of Contents

- L1: [weather-forecast](#weather-forecast)
  - L7: [Table of Contents](#table-of-contents)
  - L20: [What it does](#what-it-does)
  - L30: [Requirements](#requirements)
  - L39: [Configuration](#configuration)
  - L58: [Installing](#installing)
  - L81: [Running](#running)
  - L96: [Project structure](#project-structure)
  - L113: [Running tests](#running-tests)
  - L119: [License](#license)

## What it does

1. Downloads the latest JMA surface analysis PDF
2. Converts it to PNG
3. Feeds it to LLaVA Interleave Qwen 0.5B running locally via Hugging Face Transformers
4. Uploads the forecast text and a preview image to a Salesforce Developer Edition org

The model runs on MPS (Apple Silicon unified memory) and falls back to CPU if MPS
is unavailable. Built and tested on an M1 MacBook Air with 8 GB RAM.

## Requirements

- [pipx](https://pipx.pypa.io) — installs and runs the tool in its own isolated environment
- Python 3.14+ (pipx needs this available on your system to build that environment;
  install via [python.org](https://www.python.org/downloads/) or `brew install python@3.14`)
- macOS with Apple Silicon (M1 or later recommended)
- poppler (`brew install poppler`), required by `pdf2image` for PDF rendering
- A Salesforce Developer Edition org with JWT Bearer auth configured

## Configuration

All secrets are read from environment variables. No `.env` file is required.
Set the following before running:

```text
SF_USERNAME
SF_CLIENT_ID
SF_AUDIENCE
SF_SERVER_KEY
```

Optional:

```text
WF_VISION_MODEL   # HuggingFace model id for the vision model. Defaults to
                  # llava-hf/llava-interleave-qwen-0.5b-hf if not set.
```

## Installing

```bash
pipx install "git+https://github.com/east-van-ai/weather-forecast.git@v0.8.0"
```

That's it, no cloning, no manual `pip install`, no virtual environment to manage.
`weather-forecast` becomes available as a standalone command right away.

Pin to a released version (`@v0.8.0` above) rather than installing from `main`,
since `main` can move between releases. Check the
[releases page](https://github.com/east-van-ai/weather-forecast/releases) for
the latest tag.

Developing on the project itself, rather than just running it? Clone and
install in editable mode instead:

```bash
git clone https://github.com/east-van-ai/weather-forecast.git
cd weather-forecast
pip install -e .
```

## Running

```bash
weather-forecast --run
```

If you installed with `pip install -e .` inside an activated venv, or with `pipx`,
this command is available directly. Explicit alternatives if you need them:

```bash
python -m weather_forecast --run

python src/weather_forecast/main.py --run
```

## Project structure

```text
src/
  weather_forecast/
    main.py       entry point, registered as the `weather-forecast` command via
                   [project.scripts] in pyproject.toml
    cli/          command-line argument parsing
    chart/        PDF download, PNG conversion, image resizing
    forecast/     LLaVA inference (WeatherVision)
    orchestration/ pipeline coordinator (WeatherPipeline)
    salesforce/   Salesforce JWT auth and Weather_Report__c upsert
tests/
poc/              standalone proof-of-concept scripts (not part of the pipeline)
salesforce/       Salesforce metadata for deployment
```

## Running tests

```bash
pytest
```

## License

MIT License

The vision model ([LLaVA Interleave Qwen 0.5B](https://huggingface.co/llava-hf/llava-interleave-qwen-0.5b-hf))
is subject to the Tongyi Qianwen Research License and is restricted to non-commercial use.

---

**East Van AI** · AI for the rest of us! · Vancouver, BC, Canada

[github.com/east-van-ai](https://github.com/east-van-ai) · <east-van-ai@proton.me>

Copyright (c) 2026 Go Nakamaru
