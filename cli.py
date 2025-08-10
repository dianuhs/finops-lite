#!/usr/bin/env python3
from datetime import date, timedelta
import boto3
from botocore.exceptions import BotoCoreError, ClientError

def first_day(d: date) -> date: return d.replace(day=1)

def get_cost(start: date, end: date):
    ce = boto3.client("ce")
    resp = ce.get_cost_and_usage(
        TimePeriod={"Start": start.strftime("%Y-%m-%d"), "End": end.strftime("%Y-%m-%d")},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
    )
    r = resp.get("ResultsByTime", [])
    amt = float(r[0]["Total"]["UnblendedCost"]["Amount"]) if r else 0.0
    unit = r[0]["Total"]["UnblendedCost"].get("Unit", "USD") if r else "USD"
    return amt, unit

def main():
    today = date.today()
    start_mtd = first_day(today)
    try:
        amt, unit = get_cost(start_mtd, today)
        print("finops lite")
        print(f"range: {start_mtd} → {today}")
        print(f"month-to-date cost: {amt:.2f} {unit}")
    except ClientError as e:
        msg = (e.response.get("Error", {}) or {}).get("Message","").lower()
        if "data is not available" in msg or "not enabled for cost explorer" in msg:
            # fall back to last full month
            start_last = first_day(today.replace(day=1) - timedelta(days=1)).replace(day=1)
            end_last = first_day(today)
            try:
                amt, unit = get_cost(start_last, end_last)
                print("finops lite")
                print("cost explorer is still ingesting current-month data.")
                print(f"showing last full month instead: {start_last} → {end_last}")
                print(f"total cost: {amt:.2f} {unit}")
            except Exception as e2:
                print("finops lite")
                print("error while fetching last month:", e2)
        else:
            print("finops lite")
            print("error:", e)
    except (BotoCoreError, Exception) as e:
        print("finops lite")
        print("error:", e)

if __name__ == "__main__":
    main()
