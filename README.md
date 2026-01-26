# FinOps Lite

A CLI-first cloud cost analysis engine built on AWS Cost Explorer, designed to turn raw spend data into clear, decision ready signals.

---

## Why FinOps Lite Exists

Most cloud cost tooling optimizes for visualization. FinOps Lite optimizes for reasoning.

AWS Cost Explorer, Budgets, and Anomaly Detection are useful for answering *what happened*. They are less helpful when the real questions show up in reviews, postmortems, or planning discussions:

- Why did spend change during this window?
- What is the correct baseline to compare against?
- Is this movement meaningful or just noise?
- Can we reproduce this analysis next week or next quarter?

FinOps Lite is built for that gap.

It produces deterministic cost outputs that can be inspected, exported, diffed over time, and embedded directly into workflows. It is designed for practitioners who care about correctness, traceability, and calm decision-making under uncertainty.

This is not a platform. It is a foundation layer.

---

## What FinOps Lite Does (and AWS Native Tools Don’t)

FinOps Lite does not replace AWS Cost Explorer or Budgets. It sits alongside them and solves a different problem.

Specifically, FinOps Lite provides:

- Explicit, documented time windows for every analysis  
- Period-over-period comparisons as a first-class concept  
- Stable, schema-aware outputs suitable for CI, automation, and audits  
- Deterministic behavior that can be reproduced from the same inputs  
- FOCUS-inspired exports designed for downstream FinOps tooling  

AWS native tools prioritize interactive exploration. FinOps Lite prioritizes repeatable reasoning.

---

## Core Capability: Rolling Cost Overview

```bash
finops cost overview --days 30
```

![Rolling cost overview](docs/images/cost-overview.png)

---

## Automation-Ready Output Formats

```bash
finops cost overview --days 30 --format json
```

![JSON output](docs/images/json-demo.png)

---

## Executive Summary Mode

```bash
finops cost overview --days 30 --format executive
```

![Executive summary](docs/images/executive-summary.png)

---

## FOCUS-Inspired (Lite) Cost Export

```bash
finops export focus --days 30
```

---

## License

MIT

