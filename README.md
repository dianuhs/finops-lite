# FinOps Lite

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Cloud](https://img.shields.io/badge/cloud-AWS-orange)](https://github.com/cloudandcapital/finops-lite)
[![Contract](https://img.shields.io/badge/CCAC-1.0-blue)](https://github.com/cloudandcapital)

FinOps Lite is an open-source AWS cost visibility CLI and the canonical cloud-cost producer for the Cloud & Capital pipeline.

For the complete six-tool demo and roadmap, see [Tech Spend Command Center](https://github.com/cloudandcapital/tech-spend-command-center).

Its first CCAC release reads AWS Cost Explorer, calculates a complete service-level cost summary, reconciles the service and daily views, and emits a versioned `ccac/1.0.0` tool result for downstream analysis.

## Current scope

What works:

- AWS Cost Explorer cost summaries and equal-length period comparisons
- Service-level cost breakdowns
- Reconciled daily-by-service metrics for downstream anomaly attribution
- Calendar-month reports and month comparisons
- JSON, CSV, YAML, table, and executive output for legacy reporting commands
- Deterministic, credential-free illustrative CCAC output
- Real AWS CCAC output with source version, content hash, evidence, metrics, and reconciliation
- Fail-closed numeric parsing for canonical summaries
- Experimental CSV ingestion/normalization helpers for selected Azure and Google-shaped samples

What is not yet claimed:

- Native Azure or Google Cloud billing API integrations
- Resource-level multi-cloud normalization
- Official FOCUS conformance or FOCUS 1.4 export
- Verified savings or automated remediation
- Direct production feeding into Cloud Cost Guard

## Install

```bash
pipx install "git+https://github.com/cloudandcapital/finops-lite.git"
```

For development:

```bash
git clone https://github.com/cloudandcapital/finops-lite.git
cd finops-lite
uv sync --locked --extra dev
uv run pytest tests/ -q
```

Python 3.10 or newer is required.

## Five-minute credential-free demo

```bash
finops --no-cache ccac --demo --output finops-lite-result.json
```

The cross-repository acceptance suite validates this artifact against the shared CCAC reference schemas. The `ccac validate` command is available to contributors who install the separate Cloud & Capital CCAC reference package; it is not required to run this demo.

The demo is explicitly labeled `illustrative`, uses a fixed run ID and timestamp, and is byte-for-byte deterministic. It contains 21 consecutive daily observations and one deliberate final-day spend spike so the default FinOps Watchdog detector can be exercised end to end. It passes through the same FinOps Lite CCAC builder used for real summaries.

**Illustrative sample billing data. No customer accounts, credentials, or production resources are connected.**

## Real AWS CCAC output

Configure read-only AWS access:

```bash
aws configure --profile finops-prod
export AWS_PROFILE=finops-prod
export AWS_DEFAULT_REGION=us-east-1
```

Required permissions:

- `ce:GetCostAndUsage`
- `sts:GetCallerIdentity`

Generate a canonical result:

```bash
finops --no-cache ccac \
  --start 2026-07-01 \
  --end 2026-07-31 \
  --output finops-lite-result.json
```

`--end` is inclusive at the CLI boundary. The CCAC document converts it to an exclusive period end and records both semantics.

The command retrieves the complete service breakdown rather than truncating it to the top ten. It refuses to emit a canonical result when daily service rows, service totals, daily totals, and the reported total do not reconcile.

## Other cost commands

```bash
finops cost overview --days 30
finops cost overview --days 30 --format json
finops cost monthly --month 2026-07 --format json
finops cost compare --current 2026-07 --baseline 2026-06
finops summarize --start 2026-07-01 --end 2026-07-31
```

The compact `summarize` output is a legacy interface. New pipeline consumers should use `finops ccac`.

## FOCUS status

The official current specification is FOCUS 1.4. FinOps Lite does not yet claim FOCUS 1.4 conformance.

Older releases advertised an unofficial “FOCUS 2026” format. That name was incorrect. The `focus2026` command and internal module remain temporarily as clearly deprecated experimental compatibility paths; they are not evidence of official FOCUS conformance.

Use the FinOps Foundation's official validator for conformance testing. Official FOCUS adapters and representative AWS/Azure/Google fixtures are a later FinOps Lite migration milestone.

The existing `finops export focus` command emits a service-level working schema. It should be treated as a FinOps Lite compatibility export, not a certified FOCUS dataset.

## Trust behavior

- Invalid, missing, NaN, or infinite monetary values fail instead of becoming zero.
- Missing Cost Explorer dates fail closed; only an explicitly observed zero is emitted as zero spend.
- Illustrative output is labeled in the document itself.
- The producer emits observed and calculated metrics, not verified savings.
- Untagged spend is not converted into an opportunity.
- FinOps Lite emits no mutating cloud commands.
- Every canonical metric references evidence derived from a hashed source summary.
- Help, version, and credential-free demo commands do not create cache directories in the user's home.

## Pipeline position

```text
billing export or illustrative source
  -> FinOps Lite CCAC result
  -> FinOps Watchdog / domain tools
  -> Tech Spend Command Center trusted report
  -> Cloud Cost Guard
  -> Lumen
```

The v0.3 illustrative acceptance run connects this result through Watchdog and Tech Spend Command Center into a contract-valid trusted report. Cloud Cost Guard remains unchanged until its downstream adapter is reviewed separately.

| Component | Compatible version |
|---|---|
| FinOps Lite | `0.3.x` |
| CCAC | `ccac/1.0.0` |
| FinOps Watchdog | `0.4.x` |
| Tech Spend Command Center | `0.2.x` |

FinOps Lite is `0.3.x`, while FinOps Watchdog is independently versioned
at `0.4.x`. Compatible tools do not need identical application package
versions; their shared interchange contract remains `ccac/1.0.0`.

## License

MIT © 2026 Diana Molski, Cloud & Capital
