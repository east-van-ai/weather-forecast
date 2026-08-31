# weather-forecast

Pulls a Japan Meteorological Agency (JMA) surface analysis PDF, runs it through
a local vision model on Apple Silicon, and stores the result in Salesforce.
No cloud AI. No GPU rental. No subscriptions. Just your Mac doing the work.

## What it does

1. Downloads the latest JMA surface analysis PDF
2. Converts it to PNG
3. Feeds it to SmolVLM2 500M running locally via Hugging Face Transformers
4. Uploads what the model says, plus a preview image, to a Salesforce
   Developer Edition org

The model runs on MPS (Apple Silicon unified memory) and falls back to CPU if MPS
is unavailable. Built and tested on an M1 MacBook Air with 8 GB RAM.

## Requirements

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

## Installing

```bash
pipx install "git+https://github.com/east-van-ai/weather-forecast.git"
```

That's it, no cloning, no manual `pip install`, no virtual environment to manage.
`weather-forecast` becomes available as a standalone command right away.

## Running

```bash
weather-forecast run
```

`weather-forecast` on its own prints what it can do and touches nothing.

## Model License

The vision model ([SmolVLM2 500M](https://huggingface.co/HuggingFaceTB/SmolVLM2-500M-Video-Instruct))
is Apache 2.0. The `-Video-Instruct` name is upstream. Still images are what
this project feeds it.

---

**East Van AI** · AI for the rest of us! · Vancouver, BC, Canada

[github.com/east-van-ai](https://github.com/east-van-ai) · <east-van-ai@proton.me>

Copyright (c) 2026 Go Nakamaru
