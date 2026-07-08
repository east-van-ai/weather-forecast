# Setup Guide

This guide walks you through everything you need to get the project running on your Mac.

## Table of Contents

- L1: [Setup Guide](#setup-guide)
  - L5: [Table of Contents](#table-of-contents)
  - L24: [System Requirements](#system-requirements)
  - L39: [Platform](#platform)
  - L51: [1. Homebrew Dependencies](#1-homebrew-dependencies)
  - L70: [2. Clone the Repo](#2-clone-the-repo)
  - L79: [3. Python via pyenv](#3-python-via-pyenv)
  - L109: [4. Python Environment](#4-python-environment)
    - L120: [Verify Apple Silicon AI Support](#verify-apple-silicon-ai-support)
  - L130: [5. Hugging Face and LLaVA Model](#5-hugging-face-and-llava-model)
  - L154: [6. Salesforce CLI and npm](#6-salesforce-cli-and-npm)
  - L187: [7. Salesforce Custom Object](#7-salesforce-custom-object)
  - L203: [8. Verify in Salesforce](#8-verify-in-salesforce)
  - L210: [9. Setting Environment Variables](#9-setting-environment-variables)
  - L227: [10. Install](#10-install)
  - L246: [11. Execute Locally](#11-execute-locally)

## System Requirements

| Item | Requirement |
| --- | --- |
| Hardware | Apple Silicon Mac (M1 or later) |
| RAM | 8 GB minimum |
| macOS | Sequoia (15) or later |
| Python | 3.14 or later |
| Node.js | 18 or later (required for Salesforce CLI) |
| Salesforce | Developer Edition org (free) |
| Disk space | ~3 GB free (LLaVA model weights) |

> **Note:** M1 with 8 GB works, but LLaVA inference takes a few minutes per chart.
> Slow is fine. This is a PoC, not a production system.

## Platform

| Component | Details |
| --- | --- |
| Hardware | Apple Silicon Mac (M1 or later) |
| AI Inference | Apple MPS (Metal Performance Shaders) |
| LLM | LLaVA Interleave Qwen 0.5B (local, via Hugging Face) |
| Salesforce | Developer Edition org |

> This AI inference runs locally on Apple Silicon.
> No external AI APIs or GPU rentals required.

## 1. Homebrew Dependencies

If you don't have Homebrew installed:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then install the required packages:

```bash
brew install git pyenv poppler node pipx
```

`pyenv` manages your Python version.
`poppler` is required by `pdf2image` for PDF rendering.
`node` is required for the Salesforce CLI.
`pipx` installs the tool itself in an isolated environment (see step 10).

## 2. Clone the Repo

```bash
git clone https://github.com/east-van-ai/weather-forecast.git

# Go to the project directory
cd weather-forecast
```

## 3. Python via pyenv

Install Python 3.14:

```bash
pyenv install 3.14.3
pyenv global 3.14.3
```

Create or add to `~/.zshrc`:

```bash
# Initialize pyenv so this shell uses Python versions managed by pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

Reload shell:

```bash
source ~/.zshrc
```

Verify:

```bash
python --version
```

## 4. Python Environment

> This step is only needed if you're developing on the project itself. If
> you're just running the tool, skip ahead to step 10 and install with `pipx`.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Verify Apple Silicon AI Support

Confirm PyTorch can see your Apple Silicon GPU:

```bash
python -c "import torch; print(torch.backends.mps.is_available())"
```

This should print `True`. The pipeline detects MPS automatically at runtime and falls back to CPU if unavailable.

## 5. Hugging Face and LLaVA Model

This project uses **LLaVA Interleave Qwen 0.5B** running locally via Hugging Face. It's publicly available, so you don't need a Hugging Face account or authentication token to use it.

Run the following to download the model:

```bash
python -c "
from transformers import AutoProcessor, AutoModelForImageTextToText
model_id = 'llava-hf/llava-interleave-qwen-0.5b-hf'
AutoProcessor.from_pretrained(model_id)
AutoModelForImageTextToText.from_pretrained(model_id)
print('Model downloaded successfully.')
"
```

The model weights (~1.8 GB) are downloaded automatically on first run and cached at:

```bash
~/.cache/huggingface/hub/models--llava-hf--llava-interleave-qwen-0.5b-hf
```

Since the cache is shared across all projects on your machine, you only need to do this once. Make sure you have a stable internet connection and enough disk space before you start.

## 6. Salesforce CLI and npm

> **Note:** Salesforce CLI is distributed via npm only.
> Do not install it via Homebrew.

Install the Salesforce CLI via npm and verify:

```bash
npm install -g @salesforce/cli

sf --version
```

You should see something similar to

`@salesforce/cli/2.x.x darwin-arm64 node-vXX.x.x`

Then authenticate to your Salesforce Developer Edition org and check if it is properly authenticated. Make sure to use `--alias my-weather-forecast-de-org`; this alias is used in the deploy script in the next step.

```bash
sf org login web --alias my-weather-forecast-de-org

sf list org
```

```text
┌──┬────────────────────────────┬─────────────────────────┬────────────────────┬───────────┐
│  │ Alias                      │ Username                │ Org Id             │ Status    │
├──┼────────────────────────────┼─────────────────────────┼────────────────────┼───────────┤
│  │ my-weather-forecast-de-org │ my.username@example.com │ 00DgK0000000000000 │ Connected │
└──┴────────────────────────────┴─────────────────────────┴────────────────────┴───────────┘
```

## 7. Salesforce Custom Object

Run the Salesforce deploy

```bash
sf project deploy start --manifest salesforce/manifest/package.xml --target-org=my-weather-forecast-de-org
```

| Field | Type | Description |
| --- | --- | --- |
| `Forecast__c` | Long Text Area | AI-generated forecast text |
| `Chart_Image_Id__c` | Text | Deprecated (retained for reference only) |
| `PDF_Hash__c` | Text | PDF hash for deduplication |
| `PDF_Hash_4_4__c` | Text | Short hash variant for deduplication |
| `Import_Timestamp__c` | Date/Time | When the record was imported |

## 8. Verify in Salesforce

Log in to your Developer Edition org and confirm:

- The Weather_Report__c object exists under Setup > Object Manager
- At least one record has been created with a forecast in the Forecast__c field

## 9. Setting Environment Variables

Secrets for Salesforce connection with OAuth JWT options, assuming a `server.key` file is already generated.

```bash
# Enable automatic export of all variables
set -a

SF_USERNAME="my.username@example.com"
SF_CLIENT_ID="ThisIsMyClientID222..."
SF_AUDIENCE="https://login.salesforce.com"
SF_SERVER_KEY="$(cat "/path/to/server.key")"

# Disable automatic export
set +a
```

## 10. Install

```bash
pipx install "git+https://github.com/east-van-ai/weather-forecast.git@v0.8.0"
```

This registers a `weather-forecast` command in its own isolated environment.
Pin to a released version rather than `main`, since `main` can move between
releases. Check the
[releases page](https://github.com/east-van-ai/weather-forecast/releases) for
the latest tag.

Developing on the project itself instead? Use the editable install from
step 4 instead of this:

```bash
pip install -e .
```

## 11. Execute Locally

Execute the weather forecast app locally.

```bash
weather-forecast --run
```

If you installed with `pip install -e .` inside an activated venv, or with `pipx`,
this command is available directly. Explicit alternatives if you need them:

```bash
python -m weather_forecast --run

python src/weather_forecast/main.py --run
```

---

**East Van AI** · AI for the rest of us! · Vancouver, BC, Canada

[github.com/east-van-ai](https://github.com/east-van-ai) · <east-van-ai@proton.me>

Copyright (c) 2026 Go Nakamaru
