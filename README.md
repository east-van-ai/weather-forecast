# weather-forecast

Pulls a Japan Meteorological Agency (JMA) surface analysis PDF, runs it through
a local vision model on Apple Silicon, and stores the result in Salesforce.
No cloud AI. No GPU rental. No subscriptions. Just your Mac doing the work.

## What it does

1. Downloads the latest JMA surface analysis PDF
2. Converts it to PNG
3. Feeds it to LLaVA Interleave Qwen 0.5B running locally via Hugging Face Transformers
4. Uploads the forecast text and a preview image to a Salesforce Developer Edition org

The model runs on MPS (Apple Silicon unified memory) and falls back to CPU if MPS
is unavailable. Built and tested on an M1 MacBook Air with 8 GB RAM.

## Requirements

- Python 3.14+
- macOS with Apple Silicon (M1 or later recommended)
- A Salesforce Developer Edition org with JWT Bearer auth configured
- poppler (for pdf2image)

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

All secrets are read from environment variables. No `.env` file is required.
Set the following before running:

```text
SF_USERNAME
SF_CLIENT_ID
SF_AUDIENCE
SF_SERVER_KEY
```

## Running

```bash
python -m src.main --run
```

## Project structure

```text
src/
  main.py
  weather_forecast/
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

East Van AI -- AI for the Rest of Us
<https://github.com/east-van-ai>
