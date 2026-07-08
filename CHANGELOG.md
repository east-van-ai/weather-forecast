# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the versioning uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [v0.8.0] - 2026-07-08

### Added

- Real Python packaging: `pyproject.toml` now declares `[build-system]` and
  `[tool.setuptools.packages.find]`, making the project properly installable
  instead of relying on `pythonpath` workarounds
- `[project.scripts]` entry registers a `weather-forecast` command on install,
  so the pipeline can be run directly without `python -m` or a full file path
- `WF_VISION_MODEL` env var added, allows overriding the LLaVA vision model
  without touching source (falls back to the LLaVA default if unset)
- `pipx install` support: `weather-forecast` can now be installed and run
  directly from the GitHub repo, no cloning or manual pip install required

### Changed

- Fixed src-layout: `main.py` now lives inside `weather_forecast/` as the
  package's real entry point; the old `src/__init__.py` (which incorrectly
  made `src` itself importable) was removed
- README and SETUP updated to reflect the new install and run instructions

## [v0.7.0] - 2026-05-21

### Changed

- Dropped dotenv dependency: all secrets are now read from environment variables
- README updated to reflect current model and configuration approach
- Removed .env.example (no longer applicable)
- Added headers in source code files

## [v0.6.0] - 2026-03-29

### Changed

- Cleaned up and standardized markdown documentation
- Updated example and metadata files

## [v0.5.0] - Unreleased

### Notes

- Project paused. Planned features deferred
- Issues closed as part of project reset
- Development resumes under v0.6

## [v0.4.1] - 2026-01-01

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

## [v0.3.0] - 2025-12-24

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

## [v0.2.4] - 2025-12-22

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

## [v0.1.0] - 2025-12-11

### Added

- First working MVP of the Weather Chart -> Forecast -> Salesforce pipeline
- PDF ingestion + PNG conversion
- Preview image generation
- LLaVA-based forecast extraction
- Salesforce upload (PDF-hash, PNG-preview, forecast text)

---

**East Van AI** · AI for the rest of us! · Vancouver, BC, Canada

[github.com/east-van-ai](https://github.com/east-van-ai) · <east-van-ai@proton.me>

Copyright (c) 2026 Go Nakamaru
