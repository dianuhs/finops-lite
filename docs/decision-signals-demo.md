# Decision Signals (Demo)

FinOps Lite now supports a “decision layer” that turns service-level cost trends into actionable signals.

## Input (services rollup)

Expected columns:

- service_name
- total_cost
- percentage_of_total
- daily_average
- trend_direction
- trend_percentage
- trend_amount

Example rows:

| service_name | total_cost | % total | trend | trend % | trend $ |
|---|---:|---:|---|---:|---:|
| Amazon Elastic Compute Cloud | 1234.56 | 43.4 | up | 15.2 | 163.45 |
| Amazon RDS | 543.21 | 19.1 | down | -8.7 | -51.23 |
| Amazon S3 | 321.45 | 11.3 | stable | 2.1 | 6.78 |

## Output (signals)

### 1) Concentration risk
**Signal:** Concentration risk: Amazon Elastic Compute Cloud is 43.4% of spend  
**Severity:** WARN / HIGH (depending on threshold)  
**Owner:** Shared (FinOps + Engineering)  
**Why it matters:** When one service dominates spend, small changes swing the bill. It’s also the highest-leverage optimization target.  
**Recommended action:** Confirm whether the increase is usage-driven (expected) or configuration drift (fixable). Choose one lever: rightsizing, commitments, scheduling, or lifecycle policies.

### 2) Spend spike drivers
**Signal:** Spend spike drivers: services increasing the bill  
**Evidence:** top drivers by trend dollars and trend %  
**Recommended action:** Identify which workload/account/tag is behind each increase. Validate whether it’s expected demand or an unplanned change.

### 3) Rising services watchlist
**Signal:** Rising services watchlist  
**Why it matters:** Catching trends early reduces decision latency and lowers the cost of fixes.  
**Recommended action:** Map increases to launches/migrations/traffic. If unexplained, assign an engineering owner within 48 hours.

## Roadmap
- Wire into CLI: `finops-lite signals from-services --file <report.csv>`
- Export formats: table (terminal), JSON (automation), executive (one-pager)
- Expand to tag compliance + rightsizing + anomaly detection
