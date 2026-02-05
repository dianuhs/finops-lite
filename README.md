# FinOps Lite

FinOps Lite is a command-line tool that reads AWS Cost Explorer data and turns it into clear cost summaries, period comparisons, exports, and lightweight decision signals.

## What FinOps Lite Does

- Shows AWS spend over a time window
- Compares one period against another
- Exports normalized CSV for downstream analysis
- Produces simple, repeatable outputs for automation and reviews

## Requirements

- Python 3.9+ (project classifiers cover 3.9-3.12)
- AWS account with Cost Explorer enabled
- IAM access that includes `ce:GetCostAndUsage` and `sts:GetCallerIdentity`

## Install

### Option A: Install with `pipx` (recommended for CLI tools)

```bash
pipx install "git+https://github.com/dianuhs/finops-lite.git"
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

### 2) Export FOCUS-lite CSV

```bash
finops --profile finops-prod --region us-east-1 export focus --days 30 > focus-lite.csv
```

### 3) Flow exported CSV into `signals from-services`

`signals from-services` expects a service-rollup CSV shape. The sequence below converts `focus-lite.csv` into that shape, then runs signals:

```bash
python3 - <<'PY'
import csv
from collections import defaultdict

source = "focus-lite.csv"
target = "services-rollup.csv"

totals = defaultdict(float)
days_seen = defaultdict(set)

with open(source, "r", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):
        service = (row.get("service") or "Unknown").strip()
        cost = float(row.get("cost") or 0.0)
        totals[service] += cost
        days_seen[service].add(row.get("time_window_start"))

grand_total = sum(totals.values()) or 1.0

with open(target, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "service_name",
            "total_cost",
            "percentage_of_total",
            "daily_average",
            "trend_direction",
            "trend_percentage",
            "trend_amount",
        ],
    )
    writer.writeheader()

    for service, total in sorted(totals.items(), key=lambda kv: kv[1], reverse=True):
        day_count = max(len(days_seen[service]), 1)
        writer.writerow(
            {
                "service_name": service,
                "total_cost": f"{total:.2f}",
                "percentage_of_total": f"{(total / grand_total) * 100:.2f}",
                "daily_average": f"{total / day_count:.2f}",
                # Quickstart defaults until multi-period trend input is provided:
                "trend_direction": "stable",
                "trend_percentage": "0.0",
                "trend_amount": "0.0",
            }
        )

print(f"Wrote {target}")
PY

finops signals from-services --file services-rollup.csv --period "Last 30 days" --format table
```

## Current Limitation: `--group-by`

`finops cost overview --group-by` is intentionally SERVICE-only in v1.1.

Default behavior is `SERVICE`. `--group-by SERVICE` is accepted explicitly. Any other value fails fast with a clear error so behavior stays predictable.

## Selected Commands

- `finops cost overview --days 30`
- `finops cost monthly --month 2026-01`
- `finops cost compare --current 2026-01 --baseline 2025-12`
- `finops export focus --days 30 > focus-lite.csv`
- `finops signals from-services --file services-rollup.csv --format table`
- `finops cache stats`

## Output Formats

Cost commands support table, JSON, CSV, YAML, and executive text output:

```bash
finops cost overview --days 30 --format json
finops cost monthly --month 2026-01 --format executive
```

## License

MIT
