# FinOps Lite

Minimal, fast CLI to peek at your AWS spend:
- **Total cost** over a period
- **Top services** by cost
- **CSV export** of whatever you see
- Works with your existing **AWS_PROFILE / AWS_REGION**

---

## Quickstart (zero to output in ~60s)

```bash
# install (editable so you can hack on it)
pip install -e .

# run a couple commands (uses AWS_PROFILE / AWS_REGION if set)
finops-lite total --days 30
finops-lite services --days 30 --top 10

# optional: export what you see to CSV
finops-lite services --days 30 --top 10 --csv services.csv
```

**Don’t have AWS set up yet?** No problem — here’s what the output looks like:

**Example:** `finops-lite total --days 30`

```text
Period: last 30 days
Estimated total: $1,274.89
Top services: EC2 ($612.40), S3 ($241.00), RDS ($182.30), CloudWatch ($97.20), EBS ($89.99)
```

**Example:** `finops-lite services --days 30 --top 5`

```text
Service     Est. Cost   % of Total
EC2         $612.40     48.0%
S3          $241.00     18.9%
RDS         $182.30     14.3%
CloudWatch  $97.20      7.6%
EBS         $89.99      7.1%
```

---

## Connect to your AWS (prereqs)

1) **Install Python 3.9+**

2) **Turn on AWS Cost Explorer** in your account  
   *Billing → Cost Management → Cost Explorer → Enable.*

3) **Create a read-only IAM user (programmatic access only)**  
   Attach a minimal policy (least privilege) for Cost Explorer:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "ce:GetCostAndUsage",
           "ce:GetDimensionValues"
         ],
         "Resource": "*"
       }
     ]
   }
   ```
   > Planning to use **Audit mode** later? You’ll also need EC2 read-only:
   > `ec2:DescribeInstances`, `ec2:DescribeVolumes`, `ec2:DescribeAddresses`, `ec2:DescribeTags`.

4) **Configure your AWS CLI profile** (example: `finops-lite`)

```bash
aws configure --profile finops-lite
# paste Access key & Secret
# choose a default region, e.g., us-east-1
```

5) **Run with that profile**

```bash
finops-lite total --days 30 --profile finops-lite
finops-lite services --days 30 --top 10 --profile finops-lite
```

---

## Usage

Global flags (available on all commands):
- `--profile` — AWS config profile (defaults to `AWS_PROFILE` if set)
- `--region` — AWS region (defaults to `AWS_REGION`/`AWS_DEFAULT_REGION` if set)
- `--csv PATH` — write the displayed table to a CSV at `PATH`

Commands:

### `total` — estimated total for a period

```bash
# last 30 days
finops-lite total --days 30

# custom date range
finops-lite total --from 2025-01-01 --to 2025-01-31
```

### `services` — top-N services by cost for a period

```bash
# top 10 services in the last 30 days
finops-lite services --days 30 --top 10

# last 7 days, top 5
finops-lite services --days 7 --top 5
```

### CSV export (any command)

```bash
# export what you're seeing to CSV
finops-lite services --days 30 --top 10 --csv out/services.csv
finops-lite total --days 30 --csv out/total.csv
```

---

## Project status / roadmap

- [ ] CSV export for totals
- [ ] CSV export for services
- [ ] Audit mode: flag waste (stopped EC2, unattached EBS, unused EIPs, untagged)
- [ ] 6-month trend view (group by month)
- [ ] Better `--help` UX (clear subcommands & flags)
- [ ] Config file support (e.g., `~/.finops-lite.toml` for defaults)
- [ ] Unit tests with botocore stubs

> Tip: link each item above to its GitHub Issue once created.

---

## Development

```bash
# install dev copy
pip install -e .

# run tests (CI uses this too)
pytest -q

# try the CLI
finops-lite --help
```

---

## Notes

- This is a **lite** helper aimed at fast feedback and simple exports.
- Numbers are estimates; always confirm against AWS Billing.
- Contributions welcome — open an Issue or PR.

---

## License

This project is licensed under the terms of the license in `LICENSE`.
