# FinOps Lite

**Professional AWS cost management in your terminal** — Lightning-fast cost visibility, optimization, and governance.

[![CI/CD Pipeline](https://github.com/dianuhs/finops-lite/actions/workflows/ci.yml/badge.svg)](https://github.com/dianuhs/finops-lite/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Transform complex AWS billing into clear, actionable insights — all from your command line.

## What Makes FinOps Lite Special

- **Lightning Fast** — Intelligent caching saves time and money on repeated queries
- **Beautiful Output** — Rich tables, charts, and progress bars that actually look good
- **Bulletproof Errors** — Helpful guidance when things go wrong (not cryptic AWS errors)
- **Cost Aware** — Tracks and minimizes your API costs while maximizing insights
- **Professional Grade** — Enterprise-ready reliability with comprehensive testing

## Demo

```bash
$ finops cost overview
```

```
╭────────────────────── Cost Summary ──────────────────────╮
│                                                          │
│ Period: Last 30 days                                     │
│ Total Cost: $2,847.23                                    │
│ Daily Average: $94.91                                    │
│ Trend: ↗ +12.3% vs previous period                       │
│ Currency: USD                                            │
│                                                          │
╰──────────────────────────────────────────────────────────╯

          Top AWS Services           
┏━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━┓
┃ Service    ┃      Cost ┃ % of Total ┃ Trend ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━┩
│ Amazon EC2 │ $1,234.56 │      43.4% │   ↗   │
│ Amazon RDS │   $543.21 │      19.1% │   ↘   │
│ Amazon S3  │   $321.45 │      11.3% │   →   │
│ AWS Lambda │   $198.76 │       7.0% │   ↘   │
│ CloudWatch │    $87.65 │       3.1% │   ↗   │
└────────────┴───────────┴────────────┴───────┘
```

```bash
$ finops cache stats
```

```
     Cache Statistics     
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric            ┃ Value ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Cache Entries     │ 12    │
│ Cache Size        │ 0.3MB │
│ Hit Rate          │ 67%   │
│ API Calls Saved   │ 23    │
│ Est. Cost Savings │ $0.23 │
│ Cache Hits        │ 23    │
│ Cache Misses      │ 11    │
└───────────────────┴───────┘
Good cache performance! Your repeated queries are much faster.
```

## Quick Start

```bash
# Install
pip install finops-lite

# Set up AWS credentials (read-only IAM user recommended)
aws configure --profile finops-lite

# Get your cost overview
finops cost overview

# See what's available
finops --help
```

## Key Features

### Cost Analysis
- **Month-to-date totals** with intelligent fallback to last month
- **Cost by service** breakdown with trend analysis
- **Multiple output formats** (table, JSON, CSV, YAML, executive summary)
- **Smart caching** to avoid duplicate API calls

### Tag Governance
- **Tag compliance** reporting across all resources
- **Cost impact** analysis for untagged resources
- **Bulk tagging** recommendations (coming soon)

### Cost Optimization
- **EC2 rightsizing** recommendations with confidence scores
- **Reserved Instance** opportunity analysis
- **Unused resource** detection (coming soon)
- **Trend alerts** for cost spikes

### Performance & Caching
- **Intelligent caching** saves money on API calls
- **Performance tracking** with detailed metrics
- **Cache management** commands for full control
- **Cost savings** reporting (tracks money saved from caching)

## Advanced Usage

### Cost Analysis
```bash
# Basic cost overview
finops cost overview

# Different time periods
finops cost overview --days 7
finops cost overview --days 90

# Export reports
finops cost overview --export report.json
finops cost overview --format csv --export costs.csv

# Force refresh (bypass cache)
finops cost overview --force-refresh
```

### Cache Management
```bash
# Check cache performance
finops cache stats

# Clear cache
finops cache clear

# Disable cache for one command
finops --no-cache cost overview
```

### Performance Tracking
```bash
# See detailed performance metrics
finops --performance cost overview

# Verbose output with optimization tips
finops --verbose cost overview
```

### Output Formats
```bash
# Beautiful terminal tables (default)
finops cost overview

# Machine-readable formats
finops cost overview --format json
finops cost overview --format csv
finops cost overview --format yaml

# Executive summary
finops cost overview --format executive
```

## Prerequisites

- **Python 3.9+**
- **AWS CLI configured** with appropriate credentials
- **AWS Cost Explorer enabled** (may take 24-48 hours for first-time setup)

### Recommended IAM Permissions

Create a read-only IAM user with these policies:
- `ReadOnlyAccess` (AWS managed policy)
- Custom policy for Cost Explorer:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ce:GetCostAndUsage",
                "ce:GetRightsizingRecommendation",
                "ce:GetReservationCoverage",
                "ce:GetUsageReport"
            ],
            "Resource": "*"
        }
    ]
}
```

## Cost Awareness

FinOps Lite calls AWS Cost Explorer APIs, which cost approximately $0.01 per call. The tool includes:
- **Intelligent caching** to minimize API calls
- **Cost tracking** to show you exactly how much you're saving
- **API call optimization** to get maximum value per request

Typical usage costs less than $1/month even with frequent queries.

## Installation & Setup

### Option 1: From PyPI (Recommended)
```bash
pip install finops-lite
```

### Option 2: From Source
```bash
git clone https://github.com/dianuhs/finops-lite.git
cd finops-lite
pip install -e .
```

### AWS Setup
```bash
# Create AWS profile (recommended)
aws configure --profile finops-lite

# Enable Cost Explorer in AWS Console
# Go to: AWS Cost Management → Cost Explorer → Enable

# Test installation
finops --help
```

## Examples

### Daily Cost Monitoring
```bash
# Quick daily check
finops cost overview --days 1

# Weekly trend analysis
finops cost overview --days 7 --verbose
```

### Monthly Reporting
```bash
# Executive summary for stakeholders
finops cost overview --format executive --export monthly_report.json

# Detailed CSV for analysis
finops cost overview --format csv --export detailed_costs.csv
```

### Performance Optimization
```bash
# Check what's cached
finops cache stats

# Analyze performance
finops --performance cost overview

# Find optimization opportunities
finops optimize rightsizing --savings-threshold 50
```

## Error Handling

FinOps Lite provides helpful guidance when things go wrong:

```bash
$ finops cost overview
╭──────────────────────── AWS Credentials ────────────────────────╮
│ AWS Credentials Not Found                                       │
│                                                                 │
│ Quick Fixes:                                                    │
│   1. Configure AWS CLI:                                         │
│      aws configure                                              │
│                                                                 │
│   2. Use named profile:                                         │
│      export AWS_PROFILE=your-profile-name                       │
│      # or use: finops --profile your-profile-name               │
│                                                                 │
│   3. Use environment variables:                                 │
│      export AWS_ACCESS_KEY_ID=your-key                          │
│      export AWS_SECRET_ACCESS_KEY=your-secret                   │
│                                                                 │
│ Cost Note: Cost Explorer API calls cost ~$0.01 each             │
╰─────────────────────────────────────────────────────────────────╯
```

## What's Coming

- Real-time cost alerts with Slack/email integration
- Budget tracking and forecasting
- Multi-account support for organizations
- Custom dashboards and reporting
- API integration for programmatic access

## Development

```bash
# Clone repository
git clone https://github.com/dianuhs/finops-lite.git
cd finops-lite

# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Check code quality
black finops_lite/
flake8 finops_lite/
```

## Documentation

- **Command Reference**: `finops --help` and `finops <command> --help`
- **Configuration**: See `config/templates/finops.yaml`
- **API Reference**: Coming soon

## Contributing

Contributions welcome! Please read our contributing guidelines and submit PRs.

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Built with care for cloud cost optimization**

*FinOps Lite helps teams understand and optimize their AWS spending without the complexity of enterprise tools.*


