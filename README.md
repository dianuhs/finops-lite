## finops-lite

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)
[![Status](https://img.shields.io/badge/status-pre--alpha-blue.svg)](#project-status)

a simple CLI that shows your AWS spend right in the terminal.
month-to-date totals, last month fallback, and cost-by-service... all in seconds.

&nbsp;
### quick start

1. install Python 3.9+
2. turn on AWS Cost Explorer in your account
3. create a read-only IAM user (programmatic access only)
4. set up your AWS CLI profile to use that user (mine is called finops-lite)

&nbsp;
### install (local dev)
 ``` 
python3 -m pip install -e .
 ``` 

&nbsp;
### usage

month-to-date total (falls back to last month if CE is still warming up)

 ``` 
AWS_PROFILE=finops-lite python3 -m finops_lite.cli
 ``` 

&nbsp;
### last full month total

 ``` 
AWS_PROFILE=finops-lite python3 -m finops_lite.cli --last-month
 ``` 

&nbsp;
### cost by service (last 30 days)

 ``` 
AWS_PROFILE=finops-lite python3 -m finops_lite.cli services --days 30 --top 15
 ``` 

if you just enabled Cost Explorer, AWS might say “data is not available.”
that’s normal, try again in a few hours. AWS says it can take up to ~24h the first time.

&nbsp;
### project status
✅ totals (month-to-date + last month with fallback)

✅ cost by service (daily aggregate over N days)

⬜ audit: untagged/unused resources

⬜ tag hygiene score

⬜ csv/json/pdf export

&nbsp;
### why i built this
cloud bills can get messy fast.
sometimes you just want to know "what’s the damage?" without clicking through the AWS console.
this script does exactly that.

&nbsp;
### cost notes

this tool calls AWS Cost Explorer. AWS may charge about **$0.01 per API call**. keep runs small during testing.


&nbsp;
### screenshots

> real screenshots coming soon (once Cost Explorer finishes ingesting)

