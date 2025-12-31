# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the versioning uses [Semantic Versioning](https://semver.org/).

## [v0.4.0] - 2025-12-31

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

---

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

---

## [v0.2.x] - 2025-12-21

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

---

## [v0.1.0] - 2025-12-11

### Added

- First working MVP of the Weather Chart -> Forecast -> Salesforce pipeline
- PDF ingestion + PNG conversion
- Preview image generation
- LLaVA-based forecast extraction
- Salesforce upload (PDF-hash, PNG-preview, forecast text)

---
