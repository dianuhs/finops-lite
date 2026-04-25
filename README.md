# FinOps Lite

[![CI](https://github.com/cloudandcapital/finops-lite/actions/workflows/test.yml/badge.svg)](https://github.com/cloudandcapital/finops-lite/actions/workflows/test.yml)

**Part of the Visibility → Variance → Tradeoffs pipeline.**

| Tool | Role | Repo |
|------|------|------|
| **FinOps Lite** | Cost visibility — AWS/Azure/GCP spend, FOCUS 1.0 export | [cloudandcapital/finops-lite](https://github.com/cloudandcapital/finops-lite) |
| FinOps Watchdog | Anomaly detection — spend spikes from any cost CSV | [cloudandcapital/finops-watchdog](https://github.com/cloudandcapital/finops-watchdog) |
| Recovery Economics | Resilience modeling — backup/restore cost + scenario compare | [cloudandcapital/recovery-economics](https://github.com/cloudandcapital/recovery-economics) |
| AI Cost Lens | AI spend observability — model-level cost across OpenAI, Anthropic, Bedrock | [cloudandcapital/ai-cost-lens](https://github.com/cloudandcapital/ai-cost-lens) |
| SaaS Cost Analyzer | SaaS spend governance — unused licenses, per-seat costs, forecasting | [cloudandcapital/saas-cost-analyzer](https://github.com/cloudandcapital/saas-cost-analyzer) |
| Cloud Cost Guard | Dashboard — spend trends, savings coverage, rightsizing | [cloudandcapital/cloud-cost-guard](https://github.com/cloudandcapital/cloud-cost-guard) |
| Tech Spend Command Center | Executive summary — unified Cloud+AI+SaaS report | [cloudandcapital/tech-spend-command-center](https://github.com/cloudandcapital/tech-spend-command-center) |

Six tools. One pipeline. Full Cloud+AI+SaaS coverage for every scope the FinOps Foundation 2026 Framework defines.

---

FinOps Lite is a command-line tool that reads AWS Cost Explorer data and turns it into clear cost summaries, period comparisons, exports, and lightweight decision signals.

## What FinOps Lite Does

- Shows AWS spend over a time window
- Compares one period against another
- Exports FOCUS 1.0 compliant CSV from AWS Cost Explorer (`BilledCost`, `ResourceId`, `ServiceName`, `ChargePeriodStart`, `ChargePeriodEnd`, `ChargeType`)
- **Ingests and normalizes Azure Cost Management and GCP Billing CSV exports to FOCUS 1.0** — provider auto-detected from column names
- Produces simple, repeatable outputs for automation and reviews

## Cloud Provider Support

| Provider | Input | Command |
|----------|-------|---------|
| **AWS** | Cost Explorer API (live) | `finops export focus --days 30` |
| **Azure** | Cost Management CSV export | `finops ingest focus --file billing.csv` |
| **GCP** | Billing CSV export (BigQuery or Console) | `finops ingest focus --file billing.csv` |

Provider is auto-detected from CSV column signatures — no `--provider` flag needed.

## Requirements

- Python 3.9+ (project classifiers cover 3.9-3.12)
- **AWS:** account with Cost Explorer enabled; IAM with `ce:GetCostAndUsage` and `sts:GetCallerIdentity`
- **Azure/GCP:** billing CSV exported from Azure portal or GCP Console/BigQuery

## Install

### Option A: Install with `pipx` (recommended for CLI tools)

```bash
pipx install "git+https://github.com/cloudandcapital/finops-lite.git"
# or from a local clone:
pipx install .
```

### Option B: Install with `pip` in a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install .
```

After install, the CLI entry points are `finops` and `finops-lite`:

```bash
finops --help
```

## AWS Credentials Setup

Create and use a named AWS profile:

```bash
aws configure --profile finops-prod
export AWS_PROFILE=finops-prod
export AWS_DEFAULT_REGION=us-east-1
```

Then run commands either with environment variables:

```bash
finops cost overview --days 30
```

Or with explicit flags:

```bash
finops --profile finops-prod --region us-east-1 cost overview --days 30
```

## Quickstart

### 1) Cost analysis (overview/monthly/compare style)

```bash
finops --profile finops-prod --region us-east-1 cost compare --current 2026-01 --baseline 2025-12
```

### 2) Export FOCUS 1.0 CSV

```bash
finops --profile finops-prod --region us-east-1 export focus --days 30 > focus-export.csv
```

Output columns: `BilledCost`, `ResourceId`, `ServiceName`, `ChargePeriodStart`, `ChargePeriodEnd`, `ChargeType`, plus provider, currency, and usage metadata.

### 3) Feed exported CSV into FinOps Watchdog

The FOCUS export feeds directly into [FinOps Watchdog](https://github.com/cloudandcapital/finops-watchdog) for anomaly detection:

```bash
finops export focus --days 90 > focus-export.csv

finops-watchdog detect \
  --input focus-export.csv \
  --time-column ChargePeriodStart \
  --value-column BilledCost \
  --group-by ServiceName \
  --window 30d \
  --output-format json
```

## Current Limitation: `--group-by`

`finops cost overview --group-by` is intentionally SERVICE-only in v1.1.

Default behavior is `SERVICE`. `--group-by SERVICE` is accepted explicitly. Any other value fails fast with a clear error so behavior stays predictable.

## Selected Commands

- `finops cost overview --days 30`
- `finops cost monthly --month 2026-01`
- `finops cost compare --current 2026-01 --baseline 2025-12`
- `finops export focus --days 30 > focus-export.csv`
- `finops signals from-services --file services-rollup.csv --format table`
- `finops cache stats`

## Output Formats

Cost commands support table, JSON, CSV, YAML, and executive text output:

```bash
finops cost overview --days 30 --format json
finops cost monthly --month 2026-01 --format executive
```

## SQL Analysis

For a portfolio-facing SQL view of the same cost domain, see [`sql-analysis/`](sql-analysis/). It includes a compact cloud cost dataset, a portable schema, and analyst-style queries for service mix, spend trends, anomaly review, and period-over-period comparison.

## Pipeline

FinOps Lite is step one. From here:

- **[FinOps Watchdog](https://github.com/cloudandcapital/finops-watchdog)** — run anomaly detection on any cost CSV, including the FOCUS export above
- **[Recovery Economics](https://github.com/cloudandcapital/recovery-economics)** — model and compare backup/restore cost scenarios
- **[Cloud Cost Guard](https://github.com/cloudandcapital/cloud-cost-guard)** — full dashboard with spend trends, savings coverage, and rightsizing

## License

MIT
