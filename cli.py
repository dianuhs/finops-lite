#!/usr/bin/env python3
"""
FinOps Lite — first real API call: month-to-date AWS cost (Unblended).
"""
from datetime import date, datetime
import boto3
from botocore.exceptions import BotoCoreError, ClientError

def first_day_of_month(d: date) -> date:
    return d.replace(day=1)

def get_month_to_date_cost():
    # Uses your default AWS profile (or whatever AWS_PROFILE is set to)
    ce = boto3.client("ce")  # Cost Explorer
    start = first_day_of_month(date.today()).strftime("%Y-%m-%d")
    end = date.today().strftime("%Y-%m-%d")
    try:
        resp = ce.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
        )
        results = resp["ResultsByTime"]
        amount = results[0]["Total"]["UnblendedCost"]["Amount"] if results else "0"
        currency = results[0]["Total"]["UnblendedCost"].get("Unit", "USD") if results else "USD"
        return float(amount), currency, start, end
    except (BotoCoreError, ClientError) as e:
        raise SystemExit(f"Cost Explorer error: {e}")

def main():
    amt, unit, start, end = get_month_to_date_cost()
    print("finops lite")
    print(f"range: {start} → {end}")
    print(f"month-to-date cost: {amt:.2f} {unit}")

if __name__ == "__main__":
    main()
