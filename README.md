# 🌦️ Weather Chart → Forecast → Salesforce

This is a personal PoC built to explore what a MacBook Air can actually do. It ingests a Japan Meteorological Agency (JMA) surface analysis PDF, runs it through LLaVA locally on Apple Silicon, and stores the results in Salesforce. No cloud AI, no GPU rental, no subscriptions. Just your Mac doing the work.

## 📋 Table of Contents

- [What It Does](#-what-it-does)
- [Architecture](#-architecture)
- [Project Status](#-project-status)
- [Delivery & Deployment](#-delivery--deployment)
- [Next Steps](#-next-steps)

## 🔍 What It Does

This project converts a JMA surface analysis PDF into structured content
and stores it in a Salesforce Developer Edition org:

1. **Ingest** a JMA weather chart PDF
2. **Convert** it to a standard PNG and a small preview image
3. **Extract** a short forecast summary using LLaVA (runs locally)
4. **Upload** everything to Salesforce: PDF hash, preview image, and forecast text

Small in scope, but it touches a real cross-section of skills:
PDF tooling, image conversion, local LLM inference,
orchestration design, and Salesforce REST integration.

> For setup and installation, see [SETUP.md](./SETUP.md).

## 🏗 Architecture

    JMA PDF
      → pdf2image       (PNG conversion)
      → LLaVA           (local inference on Apple Silicon)
      → forecast text + preview image
      → Salesforce REST API
      → WeatherReport__c (Developer Edition org)

---

## 📊 Project Status

Built and tested on an M1 MacBook Air with 8 GB RAM. It runs. Slowly. But it runs. That's kind of the point.

Current MVP version is **v0.4.1**.

| Feature | Status |
| --- | --- |
| PDF ingestion and PNG conversion | ✅ Done |
| LLaVA-based forecast extraction (local) | ✅ Done |
| Salesforce upload (hash, preview, forecast) | ✅ Done |
| Modular orchestration with execution guards | ✅ Done |
| Structured logging | ✅ Done |
| Unit tests for forecast and Salesforce client | ✅ Done |
| Versioned Salesforce metadata | ✅ Done |
| Standardized deployment scripts | ✅ Done |
| CI automation | ⏳ Deferred |

## 📦 Delivery & Deployment

This project uses a **manual Continuous Delivery** model.

### Continuous Delivery

- Deployment is triggered by a human operator
- Python and Salesforce deployments are handled independently
- Each deployment targets an explicit Git tag (e.g. `v0.4.1`)
- Environment setup (venv, Salesforce auth, secrets) is assumed complete before execution
- CI tooling is intentionally out of scope for now

Standardized deployment scripts are provided to keep releases repeatable and reduce operator error.

### Continuous Integration

Automated CI (tests, merge validation, pipeline orchestration)
is **intentionally deferred** and will be revisited once delivery practices are stabilized.

## 🔮 Next Steps

- Move secrets out of `.env` and `.key` files into environment variables
  so the Python side has no file dependencies for configuration
- Make the shell scripts responsible for loading secrets into the environment
- Work toward Docker-friendly deployment as the end goal
- Add a pipeline orchestrator for cleaner flow control

## 📎 References

- [SETUP.md](./SETUP.md)
- [CHANGELOG](./CHANGELOG.md)
- [VERSIONING](./VERSIONING.md)
- [JMA Surface Analysis Charts](https://www.jma.go.jp/bosai/map.html#contents=spas)
