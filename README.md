# 📘 Weather Chart → Forecast → Salesforce

A compact proof-of-concept that ingests JMA surface analysis PDFs, extracts a forecast using LLaVA, and stores the results in Salesforce.

---

## 🌤️ Project Overview

This project converts a single JMA weather chart PDF into structured content that can be stored inside Salesforce Developer Edition:

1. **Process the input PDF**
2. **Generate a standard and a small preview PNG**
3. **Extract a short forecast summary using LLaVA**
4. **Upload everything into Salesforce** (original PDF hash, preview PNG, forecast text)

It’s a small script, but touches a wide range of skills:
PDF tooling, image conversion, LLM usage, orchestration design, and Salesforce REST integration.

---

## 🧩 Project Goals

- Keep the architecture modular and testable
- Maintain a clean separation of concerns
- Store outputs efficiently to stay within Salesforce limits
- Make the code easy to extend as new ideas come up
- Keep the repo tidy and versioned with meaningful git tags

---

## 🏗 Current State (MVP)

The script runs end-to-end and performs all major tasks:

- Downloads or ingests the PDF
- Converts page to PNG producing a standard and a small preview version
- Gets a forecast summary from LLaVA
- Pushes the results into Salesforce

This marked the initial versioning point (`v0.1.0`).

---

## 📦 Delivery & Deployment (v0.4)

This project currently uses a **manual Continuous Delivery** model.

### Continuous Delivery

- Deployment is initiated by a human operator
- Python and Salesforce deployments are independent
- Deployment targets an explicit Git tag (e.g. v0.4.0)
- Environment setup (venv, Salesforce auth, secrets) is assumed to be complete before execution
- CI tooling and automated validation are out of scope for v0.4 by design

Standardized deployment scripts are provided to ensure repeatability and reduce operator error.

### Continuous Integration

Automated CI (tests, merge validation, pipeline orchestration) is **intentionally deferred**.
This will be revisited in a future milestone once delivery practices are stabilized.

---

## 🚀 Next Steps

- Add pipeline orchestrator for clearer flow

---
