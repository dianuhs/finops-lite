# FinOps Lite 

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AWS Cost Explorer](https://img.shields.io/badge/AWS-Cost%20Explorer-orange)](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/)

> A simple CLI that shows your AWS spend right in the terminal. Month-to-date totals, last-month fallback, and cost-by-service... all in seconds.

Cloud bills can get messy fast. Sometimes you just want to know "what's the damage?" without clicking through the AWS console. **FinOps Lite** does exactly that - giving you instant cost visibility from your terminal.

## Quick Start

```bash
# Install
python3 -m pip install -e .

# Get month-to-date total
AWS_PROFILE=finops-lite python3 -m finops_lite.cli

# View top services for last 30 days
AWS_PROFILE=finops-lite python3 -m finops_lite.cli services --days 30 --top 15
```

## Table of Contents

- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Usage](#-usage)
- [CSV export (examples)](#csv-export-examples)
- [Examples](#-examples)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## Features

### Current Features
- ✅ **Month-to-date totals** - Current month spend with automatic last-month fallback
- ✅ **Cost by service** - Top N services over the last N days with daily aggregation
- ✅ **Fast execution** - Get results in seconds, not minutes

### Planned Features
- ⬜ **Resource audit** - Find untagged and unused resources
- ⬜ **Tag hygiene score** - Measure and improve your tagging strategy
- ⬜ **Export options** - CSV, JSON, and PDF export capabilities

## Prerequisites

Before you start, make sure you have:

1. **Python 3.9 or higher**
   ```bash
   python3 --version  # Should be 3.9+
   ```

2. **AWS Account with Cost Explorer enabled**
   - Go to [AWS Cost Explorer](https://console.aws.amazon.com/cost-reports/home?#/costexplorer)
   - Click "Enable Cost Explorer" if not already enabled
   - ⚠️ **Note**: It takes up to 24 hours for data to become available after first enabling

3. **AWS CLI configured**
   ```bash
   aws --version  # AWS CLI should be installed
   ```

## Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/dianuhs/finops-lite.git
cd finops-lite
```

### Step 2: Install the Package
```bash
python3 -m pip install -e .
```

### Step 3: Set Up AWS Credentials

Create a **read-only IAM user** for security:

1. **Create IAM User:**
   - Go to AWS Console → IAM → Users → Add User
   - Choose "Programmatic access" only
   - **Do not** give console access

2. **Attach the following IAM policy:**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "ce:GetCostAndUsage",
           "ce:GetUsageAndCosts",
           "ce:GetCostCategories",
           "ce:GetDimensionValues"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

3. **Configure AWS CLI profile:**
   ```bash
   aws configure --profile finops-lite
   # Enter your Access Key ID and Secret Access Key
   ```

4. **Test the setup:**
   ```bash
   AWS_PROFILE=finops-lite aws sts get-caller-identity
   ```

## Usage

### Basic Commands

```bash
# Month-to-date total (with fallback to last month)
AWS_PROFILE=finops-lite python3 -m finops_lite.cli

# Last month's total
AWS_PROFILE=finops-lite python3 -m finops_lite.cli --last-month

# Top 15 services for the last 30 days
AWS_PROFILE=finops-lite python3 -m finops_lite.cli services --days 30 --top 15
```
### CSV export (examples)

Write exactly what you see in the table to a CSV file.

```bash
# Services table → CSV
python3 -m finops_lite.cli services --days 30 --top 10 --csv out/services.csv

# Total summary → CSV
python3 -m finops_lite.cli total --days 30 --csv out/total.csv
```

**Example: `services.csv` (first few rows)**
```text
Service,Est. Cost,% of Total
Amazon Elastic Compute Cloud - Compute,$612.40,48.0%
Amazon Simple Storage Service,$241.00,18.9%
Amazon Relational Database Service,$182.30,14.3%
```

**Example: `total.csv`**
```text
Label,Estimated Total,Unit
Period: 2025-07-12 → 2025-08-11,1274.89,USD
```

> Notes:
> - Change the path after `--csv` to save wherever you like (e.g., `reports/services-2025-08.csv`).
> - The numbers above are sample values. Your actual output will vary by account.

### Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `cli` | Show month-to-date total | `python3 -m finops_lite.cli` |
| `cli --last-month` | Show last month's total | `python3 -m finops_lite.cli --last-month` |
| `cli services` | Show cost by service | `python3 -m finops_lite.cli services --days 7 --top 10` |

### Options

- `--days N`: Number of days to analyze (default: 30)
- `--top N`: Number of top services to show (default: 10)
- `--last-month`: Show last month instead of current month

## Examples

### Example Output: Month-to-Date Total
```
Month-to-Date AWS Spend: $1,234.56
Period: December 1-15, 2024
```

### Example Output: Top Services
```
Top 5 Services (Last 30 Days):
1. EC2-Instance          $456.78
2. S3                    $234.56
3. RDS                   $123.45
4. CloudFront            $67.89
5. Lambda                $23.45
```

## Troubleshooting

### Common Issues

#### "Data is not available"
**Problem**: You just enabled Cost Explorer  
**Solution**: Wait up to 24 hours for AWS to ingest your billing data, then try again.

#### "Access Denied"
**Problem**: IAM permissions are insufficient  
**Solution**: Ensure your IAM user has the Cost Explorer permissions listed above.

#### "Profile not found"
**Problem**: AWS profile isn't configured  
**Solution**: Run `aws configure --profile finops-lite` to set up your credentials.

#### "No data returned"
**Problem**: Your AWS account might have no spend in the time period  
**Solution**: Try `--last-month` or adjust the `--days` parameter.

## Pro Tips

1. **Minimize API costs**: AWS charges ~$0.01 per Cost Explorer API call. Keep runs small during testing.

2. **Set up aliases**: Add to your `.bashrc` or `.zshrc`:
   ```bash
   alias awscost="AWS_PROFILE=finops-lite python3 -m finops_lite.cli"
   alias awsservices="AWS_PROFILE=finops-lite python3 -m finops_lite.cli services"
   ```

3. **Regular monitoring**: Run this tool daily/weekly to stay on top of your AWS spend.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Show Your Support

If this tool helps you manage your AWS costs, please give it a star! It helps others discover the project.
