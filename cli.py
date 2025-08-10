#!/usr/bin/env python3
from datetime import date, timedelta
import boto3

def first_of_month(d: date) -> date:
    return d.replace(day=1)

def last_month_range(today: date):
    start_this = first_of_month(today)     # e.g., 2025-08-01
    last_day_prev = start_this - timedelta(days=1)
    start_prev = first_of_month(last_day_prev)  # e.g., 2025-07-01
    # Cost Explorer expects [Start, End) (end is exclusive)
    return start_prev, start_this

def main():
    print("finops lite")
    today = date.today()
    start_prev, end_prev = last_month_range(today)
    ce = boto3.client("ce")
    # Last full month only, to avoid CE warm-up issues
    resp = ce.get_cost_and_usage(
        TimePeriod={"Start": start_prev.strftime("%Y-%m-%d"), "End": end_prev.strftime("%Y-%m-%d")},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
    )
    r = resp.get("ResultsByTime", [])
    if not r:
        print(f"no data returned for {start_prev} → {end_prev}")
        return
    total = r[0]["Total"]["UnblendedCost"]
    amount = float(total["Amount"])
    unit = total.get("Unit", "USD")
    print(f"last full month: {start_prev} → {end_prev}")
    print(f"total cost: {amount:.2f} {unit}")

if __name__ == "__main__":
    main()
