# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the versioning uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.11.3] - 2026-09-15

### Added

- GitHub Actions CI: ruff, black, and ShellCheck on Ubuntu, and the test suite on
  macOS

## [0.11.2] - 2026-09-14

### Added

- `scripts/cron-job.sh` and `scripts/setup-env-vars.sh`, a template for an hourly
  scheduled run
- `scripts/cleanup/`, which hard-deletes old uploaded files to free a Developer
  Edition org's file storage

### Changed

- README and `docs/SETUP.md` set the `SF_*` variables with `export` in place of
  `set -a`

## [0.11.1] - 2026-09-09

### Changed

- DESIGN.md moves to `docs/DESIGN.md`, and the command surface splits out into
  `docs/CLI.md`, which holds the grammar, the flags, and the exit codes
- README names the pipeline as local ETL, with worked environment examples and links
  to the other documents
- The banner and the `run` docstring carry the ETL framing, and note that a dry run
  checks the `SF_*` variables for presence, not validity

## [0.11.0] - 2026-09-03

### Added

- `weather-forecast run --commit`, the flag that makes a run real. One of `--commit`
  or `--dry-run` is required, and neither is a default
- `--dry-run` has a body now. It downloads, renders, and describes the chart, logs
  what would be written, and stops before Salesforce

### Changed

- `--dryrun` is respelled `--dry-run`. The old spelling is an unknown flag
- `--force` leaves the mutually exclusive pair and rides either mode
- `weather-forecast run` on its own prints the run command's documentation and exits
  0 rather than acting

### Removed

- The `torchaudio` and `python-dotenv` pins. Nothing in the project or its dependency
  graph reaches either one

## [0.10.0] - 2026-08-31

### Added

- `weather-forecast version` and `--version` both print the installed version and
  exit 0

### Changed

- The command line takes a command word: `weather-forecast run` replaces
  `weather-forecast --run`, and the flags `--force` and `--dryrun` follow it
- The vision model is now SmolVLM2 500M, replacing LLaVA Interleave Qwen 0.5B. The
  prompt is "What is this?", and the licence moves to Apache 2.0
- The prompt is built by the processor's chat template, and only the generated tail
  is decoded
- The banner's exit-code list now names argparse's own exit 2
- Dependencies are declared once, in `pyproject.toml`; the development install is now
  `pip install -e . --group dev`, which needs pip 25.1 or newer
- Test tooling moved to a `dev` dependency group, so a `pipx` install of the command
  no longer carries a test runner

### Removed

- `--run`. Executing takes the `run` command word
- `WF_VISION_MODEL`. It only ever accepted models that take a literal `<image>` in
  raw text, which the new model does not
- The title split. Only the description half was ever published
- `requirements.txt`, `requirements-dev.txt`, and `requirements-pinned.txt`

### Fixed

- README and SETUP.md installed from branch pins that do not exist on the public
  repo; both now install from the default branch

## [0.9.0] - 2026-08-21

### Added

- Bare `weather-forecast` invocation (no arguments) prints the banner docstring and
  exits 0 without touching anything
- Under a pipx install the data directory moves to `~/.cache/weather-forecast/data`;
  a normal install still uses `./data`
- MIT LICENSE file

### Changed

- Entry module renamed `main.py` to `cli.py` to match the East Van AI house style,
  with a banner docstring documenting usage, flags, environment, and exit codes
- The `cli/` package folds into `cli.py`, and `[project.scripts]` now points at
  `weather_forecast.cli:main`
- README trimmed to the user-facing pipx flow: development-only install and run
  instructions removed; project structure now lives in DESIGN.md

## [0.8.0] - 2026-07-08

### Added

- `pyproject.toml` declares `[build-system]` and `[tool.setuptools.packages.find]`,
  making the project properly installable
- `[project.scripts]` entry registers a `weather-forecast` command on install, so the
  pipeline can be run directly without `python -m` or a full file path
- `WF_VISION_MODEL` env var added, allows overriding the LLaVA vision model without
  touching source (falls back to the LLaVA default if unset)
- `pipx install` support: `weather-forecast` can now be installed and run directly
  from the GitHub repo, no cloning or manual pip install required

### Changed

- Fixed src-layout: `main.py` now lives inside `weather_forecast/`, and the old
  `src/__init__.py` was removed
- README and SETUP updated to reflect the new install and run instructions

## [0.7.0] - 2026-05-21

### Changed

- Dropped dotenv dependency: all secrets are now read from environment variables
- README updated to reflect current model and configuration approach
- Removed .env.example (no longer applicable)
- Added headers in source code files

## [0.6.0] - 2026-03-29

### Changed

- Cleaned up and standardized markdown documentation
- Updated example and metadata files

## [0.5.0] - Unreleased

### Notes

- Project paused. Planned features deferred
- Issues closed as part of project reset
- Development resumes under v0.6

## [0.4.1] - 2026-01-01

### Added

- Manual Continuous Delivery foundations
- Standardized deployment scripts for Python and Salesforce
- Clear separation of deployment responsibilities per system
- Documentation of delivery assumptions and boundaries

### Changed

- Deployment model formalized around tagged releases
- Cron execution clarified via script naming

### Deferred

- Continuous Integration (CI) automation

## [0.3.0] - 2025-12-24

### Added

- Salesforce metadata versioning for Weather Report object
- Manifest-based retrieve and deploy workflow (`package.xml`)
- Repository structure for Salesforce metadata (`salesforce/`)

### Changed

- Clarified architectural intent: Salesforce operates as a passive data store
- Deprecated fields retained in schema but explicitly documented as unused
- README updated to describe system layers and v0.3 scope

### Not Added

- No Apex classes or triggers
- No Flows or Process Builders
- No Reports, Page Layouts, or FlexiPages customized

## [0.2.4] - 2025-12-22

### Added

- End-to-end orchestration flow for weather pipeline execution
- Execution guards and `--force` override flag
- Structured logging and improved observability
- Unit tests for forecast generation and Salesforce client logic

### Changed

- Refactored pipeline into a central orchestration class
- Improved Salesforce publish logic (upsert behavior, logging, reliability)
- Cleaned up runtime directories and execution environment

### Fixed

- Missing weather images in Salesforce records
- Script naming inconsistencies

## [0.1.0] - 2025-12-11

### Added

- First working MVP of the Weather Chart -> Forecast -> Salesforce pipeline
- PDF ingestion + PNG conversion
- Preview image generation
- LLaVA-based forecast extraction
- Salesforce upload (PDF-hash, PNG-preview, forecast text)
