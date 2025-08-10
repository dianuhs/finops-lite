#!/usr/bin/env python3
from datetime import date, timedelta
import boto3
from botocore.exceptions import BotoCoreError, ClientError

def first_of_month(d: date) -> date:
    return d.replace(day=1)

def get_cost(start: date, end: date):
    ce = boto3.client("ce")
    resp = ce.get_cost_and-usage(
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
    start_mtd = first_of_month(today)
    print("finops lite")
    try:
        amt, unit = get_cost(start_mtd, today)
        print(f"range: {start_mtd} → {today}")
        print(f"month-to-date cost: {amt:.2f} {unit}")
    except ClientError as e:
        msg = (e.response.get("Error", {}) or {}).get("Message", "").lower()
        if "data is not available" in msg or "not enabled for cost explorer" in msg:
            # fall back to last full month
            last_month_end = first_of_month(today)  # first of this month
            last_month_start = first_of_month(last_month_end - timedelta(days=1))
            try:
                amt, unit = get_cost(last_month_start, last_month_end)
                print("cost explorer is still ingesting current-month data.")
                print(f"showing last full month instead: {last_month_start} → {last_month_end}")
                print(f"total cost: {amt:.2f} {unit}")
            except Exception as e2:
                print("error while fetching last month:", e2)
        else:
            print("error:", e)
    except (BotoCoreError, Exception) as e:
        print("error:", e)

if __name__ == "__main__":
    main()
