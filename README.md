# FinOps Lite

FinOps Lite is a CLI-first cloud cost analysis engine built on AWS Cost Explorer.  
It turns raw spend data into clear, repeatable, decision-ready signals.

It is designed for practitioners who need to reason about cost, not just visualize it.

---

## Why FinOps Lite Exists

Most cloud cost tooling optimizes for dashboards.

Dashboards are good at answering what happened.  
They are weaker when the real work starts:

- Why did spend change during this window?
- What is the correct baseline to compare against?
- Is this movement meaningful or just noise?
- Can we reproduce this analysis next week, next quarter, or during an audit?

FinOps Lite exists to close that gap.

It produces deterministic outputs that can be inspected, exported, diffed over time, and embedded directly into workflows. Every number has an explicit window, comparison, and schema.

This is not a platform.  
It is a foundation layer.

---

## What FinOps Lite Does (and AWS Native Tools Don’t)

FinOps Lite does not replace AWS Cost Explorer, Budgets, or Anomaly Detection.  
It complements them by solving a different problem.

FinOps Lite provides:

- Explicit, documented time windows for every analysis  
- Period-over-period comparisons as a first-class concept  
- Stable, schema-aware outputs suitable for CI and automation  
- Deterministic behavior that can be reproduced from the same inputs  
- FOCUS-inspired exports designed for downstream FinOps tooling  

AWS native tools prioritize interactive exploration.  
FinOps Lite prioritizes repeatable reasoning.

---

## Core Capability: Rolling Cost Overview

The most common question in FinOps is deceptively simple:

“What changed, compared to what, and does it matter?”

FinOps Lite answers that directly.

```bash
finops cost overview --days 30
```

### Screenshot: rolling cost overview

![Rolling cost overview](docs/images/cost-overview.png)

---

## Automation-Ready Output Formats

Every FinOps Lite command can emit machine-readable output.

```bash
finops cost overview --days 30 --format json
```

The JSON output is:

- Stable across runs
- Explicit about time windows
- Suitable for pipelines, notebooks, and audits

### Screenshot: JSON output

![JSON output](docs/images/json-demo.png)

---

## Executive Summary Mode

For leadership and review decks, FinOps Lite can generate a compact, human-readable summary.

```bash
finops cost overview --days 30 --format executive
```

This mode is designed to:

- Surface only material changes
- Avoid noisy deltas
- Read cleanly in email, Slack, or a slide

### Screenshot: executive summary

![Executive summary](docs/images/executive-summary.png)

---

## FOCUS-Inspired (Lite) Cost Export

FinOps Lite supports a lightweight export aligned with the FinOps Open Cost and Usage Specification (FOCUS).

```bash
finops export focus --days 30
```

This makes it easier to:

- Share cost data across tools
- Normalize downstream analysis
- Keep internal schemas consistent

---

## Where FinOps Lite Fits

FinOps Lite is intentionally narrow.

It works best as:

- A reasoning layer before dashboards
- A deterministic input to automation
- A shared reference point during reviews and postmortems

It pairs naturally with:

- FinOps Watchdog for baseline-aware change detection  
- Recovery Economics for modeling the cost of failure and recovery  

Together, they form a small, composable FinOps toolkit focused on decisions, not visuals.

---

## Who This Is For

- FinOps practitioners who care about correctness and traceability  
- Cloud cost and infrastructure engineers  
- Teams preparing for audits, reviews, or cost governance discussions  
- Anyone translating between finance, engineering, and leadership  

FinOps Lite favors clarity over coverage.  
It is designed to be read, trusted, and reused.

---

## License

MIT
