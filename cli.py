#!/usr/bin/env python3
"""
FinOps Lite — month-to-date AWS cost (Unblended) with friendly errors.
"""
from datetime import date
import boto3
from botocore.exceptions import BotoCoreError, ClientError

def first_day_of_month(d: date) -> date:
    return d.replace(day=1)

def get_month_to_date_cost():
    ce = boto3.client("ce")
    start = first_day_of_month(date.today()).strftime("%Y-%m-%d")
    end = date.today().strftime("%Y-%m-%d")
    try:
        resp = ce.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
        )
        results = resp.get("ResultsByTime", [])
        amount = results[0]["Total"]["UnblendedCost"]["Amount"] if results else "0"
        currency = results[0]["Total"]["UnblendedCost"].get("Unit", "USD") if results else "USD"
        return float(amount), currency, start, end
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        msg = e.response.get("Error", {}).get("Message", "")
        # Common first-run message when Cost Explorer was just enabled
        if code == "AccessDeniedException" and "not enabled for cost explorer" in msg.lower():
            return None, None, start, end  # signal "warming up"
        raise
    except BotoCoreError:
        raise

def main():
    try:
        amt, unit, start, end = get_month_to_date_cost()
        print("finops lite")
        print(f"range: {start} → {end}")
        if amt is None:
            print("cost explorer is warming up. try again in a few hours.")
        else:
            print(f"month-to-date cost: {amt:.2f} {unit}")
    except Exception as e:
        print("finops lite")
        print("error:", e)

if __name__ == "__main__":
    main()
