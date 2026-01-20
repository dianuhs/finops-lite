# FinOps Lite

[![Tests](https://github.com/dianuhs/finops-lite/actions/workflows/ci.yml/badge.svg)](https://github.com/dianuhs/finops-lite/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://codecov.io/gh/dianuhs/finops-lite/branch/main/graph/badge.svg)](https://codecov.io/gh/dianuhs/finops-lite)

A CLI-first cloud cost analysis engine built on AWS Cost Explorer, designed to turn raw spend data into clear, decision-ready signals.

---

## Why FinOps Lite Exists

Most cloud cost tooling optimizes for visualization. FinOps Lite optimizes for reasoning.

Instead of dashboards that passively refresh, FinOps Lite produces deterministic cost reports that can be inspected, exported, diffed across time, and embedded directly into workflows. It is designed for practitioners who want to understand *why* spend changes, not just *that* it did.

FinOps Lite intentionally focuses on correctness, portability, and signal quality. It is a foundation layer for higher-order FinOps automation rather than an all-in-one platform.

---

## Core Capabilities

### Rolling Cost Overview
Analyze the last N days of cloud spend and compare it to the previous period.

Includes:
- total spend
- daily average
- period-over-period trend
- top services by cost and concentration

Command:
finops cost overview --days 7

[screenshot of rolling cost overview CLI output here]

---

### Calendar Month Reporting
Analyze a full calendar month using Cost Explorer’s native month boundaries and compare it to the prior month.

Command:
finops cost monthly --month 2026-01

[screenshot of monthly cost report here]

---

### Month-over-Month Comparison
Compare two calendar months directly to identify deltas and service-level cost drivers.

Command:
finops cost compare --current 2026-01 --baseline 2025-12

[screenshot of month comparison output here]

---

## Output Formats

All reports can be rendered in multiple formats depending on the audience or downstream use case:

- table – rich CLI output
- json – stable, machine-readable schema
- csv – spreadsheet-friendly
- yaml – configuration and pipeline friendly
- executive – narrative summary with recommendations

[screenshot of executive summary output here]  
[screenshot of JSON report schema here]

---

## Executive Summary Mode

Executive output translates raw cost data into decision-oriented language, including:
- monthly run-rate estimates
- spend concentration analysis
- targeted optimization prompts

This format is designed to be shared directly with leadership or embedded in written reports.

---

## Reporting Examples

[screenshot of CLI table output here]  
[screenshot of CSV export opened in spreadsheet here]  
[screenshot of YAML output here]

---

## Report Schema (Stable by Design)

All structured outputs follow a consistent schema:
- metadata (version, generated_at, report_type)
- reporting window (rolling or calendar)
- summary (total_cost, daily_average, trend)
- services (per-service cost, percentage of total, daily average, trend)

Schema stability is intentional. It allows FinOps Lite to act as a reliable upstream source for automation, analytics pipelines, and future tooling.

---

## Demo & Fixture Mode

FinOps Lite can operate without live AWS spend.

If a Cost Explorer fixture exists in:
finops_lite/fixtures/

the CLI will automatically use it instead of calling AWS.

This enables:
- demos without AWS credentials
- development on zero-spend accounts
- deterministic testing
- CI pipelines without Cost Explorer API usage

[screenshot of fixture-based run here]

---

## Installation

Clone the repository and install in editable mode:

pip install -e .

---

## AWS Configuration

FinOps Lite uses standard AWS authentication methods:
- aws configure
- named profiles
- environment variables
- STS-based credentials

Live data requires permission to access AWS Cost Explorer.

> AWS Cost Explorer API calls cost approximately $0.01 per request.  
> FinOps Lite includes caching to minimize unnecessary calls.

---

## Error Handling

FinOps Lite provides clear, actionable guidance when things go wrong.

[screenshot of AWS credentials error output here]

---

## Design Principles

FinOps Lite is intentionally narrow and composable.

It emphasizes:
- correct cost windows
- transparent aggregation logic
- repeatable outputs
- portability across teams and environments

This makes it suitable both as a standalone analysis tool and as a foundation layer for more advanced FinOps systems.

---

## Roadmap

FinOps Lite is the base layer for upcoming tooling, including:
- Guard Dog – automated cost hygiene and anomaly detection
- Recovery Economics – cost-to-value analysis and optimization modeling
- scheduled reporting and alerting

Each builds directly on the report schema produced by FinOps Lite.

---

## License

MIT
