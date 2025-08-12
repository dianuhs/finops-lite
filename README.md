# 💰 FinOps Lite

**Professional AWS cost management CLI for cost visibility, optimization, and governance.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 📊 **Cost Overview** - Beautiful terminal cost analysis with trend indicators
- 🏷️ **Tag Compliance** - Governance and compliance monitoring across resources  
- 🚀 **Rightsizing** - EC2 optimization recommendations with savings projections
- 📋 **Multiple Formats** - JSON, CSV, YAML, and Executive summary reports
- 🔧 **Professional CLI** - Rich formatting, progress bars, and error handling
- ⚡ **Demo Mode** - Test all features without AWS credentials

## 🚀 Quick Start

```bash
# Install dependencies
pip install -e .

# Get beautiful cost overview
finops cost overview

# JSON output for automation
finops cost overview --format json

# Executive summary for management
finops cost overview --format executive

# Export to CSV for analysis
finops cost overview --format csv --export costs.csv

# Test without AWS credentials
finops --dry-run cost overview
```

## 📋 Available Commands

### Cost Analysis
```bash
# Cost overview with trend analysis
finops cost overview
finops cost overview --days 7 --format json
finops cost overview --group-by REGION
```

### Governance & Compliance
```bash
# Tag compliance monitoring
finops tags compliance
finops tags compliance --service ec2 --fix
```

### Optimization
```bash
# Rightsizing recommendations
finops optimize rightsizing
finops optimize rightsizing --service rds --savings-threshold 50
```

## 📊 Output Formats

### Table Format (Default)
Beautiful Rich-formatted tables with colors and trend indicators.

### JSON Format
```json
{
  "finops_lite_report": {
    "summary": {
      "total_cost": 2847.23,
      "daily_average": 94.91,
      "trend": {
        "direction": "up",
        "change_percentage": 12.3
      }
    },
    "services": [...]
  }
}
```

### Executive Summary
Professional management reports with key insights and recommendations.

## ⚙️ Configuration

Create `finops.yaml` in your project directory:

```yaml
aws:
  profile: "default"
  region: "us-east-1"

output:
  format: "table"
  currency: "USD"
  
cost:
  default_days: 30
  cost_threshold: 0.01

tagging:
  required_tags:
    - "Environment"
    - "Owner"
    - "Project"
```

## 🛠️ Built With

- **Python 3.9+** - Modern Python development
- **Rich** - Beautiful terminal output with colors and formatting
- **Click** - Professional CLI framework
- **AWS Cost Explorer API** - Real AWS cost data integration
- **PyYAML** - Configuration management
- **Pydantic** - Data validation and settings management

## 🏗️ Architecture

```
finops_lite/
├── cli.py              # Main CLI interface
├── core/               # AWS service integrations
│   ├── cost_explorer.py
│   └── __init__.py
├── reports/            # Output formatters
│   ├── formatters.py
│   └── __init__.py
├── utils/              # Utilities and helpers
│   ├── config.py       # Configuration management
│   ├── logger.py       # Logging setup
│   ├── aws_client.py   # AWS client utilities
│   └── errors.py       # Error handling
└── __init__.py
```

## 🔧 Development

```bash
# Setup development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .

# Run tests
python -m pytest tests/ -v

# Test CLI functionality
python -m finops_lite.cli --dry-run cost overview
```

## 📖 Examples

### Basic Cost Analysis
```bash
# Get 30-day cost overview
finops cost overview

# Last 7 days with JSON output
finops cost overview --days 7 --format json

# Export to spreadsheet
finops cost overview --format csv --export monthly-costs.csv
```

### Automation & Integration
```bash
# JSON for scripts/automation
finops --output-format json cost overview > costs.json

# Executive report for management
finops cost overview --format executive > executive-summary.txt

# Tag compliance monitoring
finops tags compliance --service ec2 > compliance-report.txt
```

### Demo Mode (No AWS Required)
```bash
# Try all features without AWS credentials
finops --dry-run cost overview
finops --dry-run cost overview --format json
finops --dry-run tags compliance
finops --dry-run optimize rightsizing
```

## 🚀 Business Value

- **Cost Visibility** - Instant insights into AWS spending patterns
- **Governance** - Automated tag compliance monitoring
- **Optimization** - Rightsizing recommendations with savings projections  
- **Reporting** - Executive summaries and detailed analysis
- **Automation** - JSON/CSV outputs for integration with other tools

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details.

---

**Built with ❤️ for cloud cost optimization**

*Professional AWS FinOps made simple.*
