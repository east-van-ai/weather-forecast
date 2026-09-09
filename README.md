# weather-forecast

A local ETL pipeline. Extract a Japan Meteorological Agency (JMA) surface analysis
PDF, transform it with a vision-language model running on Apple Silicon, load the
result into Salesforce. The transform step is the interesting one: the model looks
at a weather chart and says what it sees.

No cloud AI. No GPU rental. No subscriptions. Just a Mac doing the work.

## What it does

1. Downloads the latest JMA surface analysis PDF
2. Renders page one to PNG
3. Feeds the PNG to SmolVLM2 500M, running locally on Hugging Face Transformers
4. Uploads what the model says, plus a preview image, to a Salesforce org

The model runs on MPS (Apple Silicon unified memory) and falls back to CPU if MPS
is unavailable. Built and tested on an M1 MacBook Air with 8 GB RAM.

The name promises more than the tool delivers. Nothing here forecasts anything.
Meteorologists at the JMA draw the chart, and the model reads it back.

## Why it runs on your own machine

The whole point is that the hard part fits on a laptop. SmolVLM2 500M is about
two gigabytes of weights on disk. It loads once, answers in under a minute, and
costs nothing per image.

That changes what the project is allowed to be. There is no API key to rotate,
no per-call bill to watch, and no rate limit to design around. The chart never
leaves the machine that downloads it. A cron job can run this every morning for
years and the running cost stays at zero.

## Requirements

- macOS on Apple Silicon, or any machine that can run PyTorch on CPU
- Python 3.14 or newer
- poppler (`brew install poppler`), required by `pdf2image` for PDF rendering
- A Salesforce Developer Edition org with JWT Bearer auth configured

## Installing

```bash
pipx install "git+https://github.com/east-van-ai/weather-forecast.git"
```

That's it, no cloning, no manual `pip install`, no virtual environment to manage.
`weather-forecast` becomes available as a standalone command right away.

The model downloads itself on the first run, straight from Hugging Face. No
account and no token are needed for it.

## Configuration

All secrets are read from environment variables. No `.env` file is required,
and the application never reads one. Set these four before running:

```bash
set -a
SF_USERNAME="agentforce@example.com"
SF_CLIENT_ID="3MVG8szVa2RxsrPnFaxLwCg..."
SF_AUDIENCE="https://login.salesforce.com"
SF_SERVER_KEY="$(cat "/path/to/server.key")"
set +a
```

`SF_USERNAME` is the Salesforce user the run acts as. `SF_CLIENT_ID` is the
connected app's consumer key, a long string that starts `3MVG`. `SF_AUDIENCE`
is the login host. `SF_SERVER_KEY` is the private key that signs the JWT, in
PEM form, header and footer included:

```text
-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCxMVFkLosHn18M
... more lines of base64 ...
-----END PRIVATE KEY-----
```

Read that one from its file rather than pasting it inline. The line breaks are
part of the key. A key whose newlines have collapsed into a literal `\n` fails
with `InvalidKeyError: Could not parse the provided public key`, and that
message says public where it means private, so it sends the reader looking in
the wrong place.

weather-forecast reads all four from the environment and keeps no credential
of its own.

## Running

Start with a preview:

```bash
weather-forecast run --dry-run
```

That checks the four `SF_*` variables are set, downloads today's chart, describes
it, and prints what it would send. Neither the text nor the image reaches Salesforce.
The check is for presence alone, so a preview proves the variables are there and not
that they work.

When the description looks right, send it:

```bash
weather-forecast run --commit
```

Nothing is written unless `--commit` is there. The two flags are the run's mode, they
are mutually exclusive, and one of them is required. A `run` carrying neither is an
error rather than a guess.

Bare `weather-forecast` prints what it can do and touches nothing. So does a
bare `weather-forecast run`, which answers with its own documentation.

## When the chart has not changed

Each run keeps the PDF it downloaded and compares it against the previous one by
hash. A chart that has not moved is not worth a second description, so the run
reports the match and stops early.

`--force` overrides that and works against either mode:

```bash
weather-forecast run --commit --force
```

One wrinkle worth knowing. A dry run consumes the update it previewed, because it
rotates the downloaded PDF either way. Committing straight after a preview therefore
takes `--force`.

## What a run prints

There are no log files. Progress goes to standard error, one line per stage,
and that is the whole record of a run:

```text
2026-08-31 10:02:18,143 INFO weather_forecast.cli_run - Execution started (mode=commit, force=True)
2026-08-31 10:02:18,143 INFO weather_forecast.orchestration.pipeline - Pipeline run started
2026-08-31 10:02:18,362 INFO weather_forecast.orchestration.pipeline - Preparing images
2026-08-31 10:02:20,146 INFO weather_forecast.orchestration.pipeline - Generating forecast via AI
2026-08-31 10:03:13,968 INFO weather_forecast.orchestration.pipeline - Publishing results to Salesforce
2026-08-31 10:03:16,821 INFO weather_forecast.orchestration.pipeline - Salesforce publish completed: record_id=a00gK00001EFOh8QaH created=False
2026-08-31 10:03:16,821 INFO weather_forecast.orchestration.pipeline - Pipeline run completed successfully
2026-08-31 10:03:16,829 INFO weather_forecast.cli_run - Pipeline executed successfully
```

The slow line is the model. Everything either side of it is seconds.

## Model Licence

The vision model ([SmolVLM2 500M](https://huggingface.co/HuggingFaceTB/SmolVLM2-500M-Video-Instruct))
is Apache 2.0. The `-Video-Instruct` name is upstream. Still images are what
this project feeds it.

## Documentation

- [docs/CLI.md](docs/CLI.md) is the command surface: the grammar, the flags,
  the exit codes, and what each command prints.
- [docs/DESIGN.md](docs/DESIGN.md) holds the model and the reasoning under the
  decisions, including why the prompt is one short question.
- [docs/SETUP.md](docs/SETUP.md) walks through the Salesforce org, the
  connected app, and the certificate.
- [CHANGELOG.md](CHANGELOG.md) records what shipped in each version.

## Use of AI

This project is built with Artificial Intelligence (AI), deliberately
and in the open. Code and documentation are written in collaboration
with remote and local AI; design decisions, code review, and final
judgement stay human.

---

**East Van AI** · AI for the rest of us! · Vancouver, BC, Canada

[github.com/east-van-ai](https://github.com/east-van-ai) · <east-van-ai@proton.me>

Copyright (c) 2026 Go Nakamaru
