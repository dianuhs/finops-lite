#!/usr/bin/env python3
from datetime import date, timedelta
import boto3
from botocore.exceptions import ClientError, BotoCoreError

def first_of_month(d: date) -> date:
    return d.replace(day=1)

def last_month_range(today: date):
    start_this = first_of_month(today)
    last_day_prev = start_this - timedelta(days=1)
    start_prev = first_of_month(last_day_prev)
    return start_prev, start_this  # [start, end)

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
    print("finops lite")
    today = date.today()
    start_mtd = first_of_month(today)

    try:
        amt, unit = get_cost(start_mtd, today)
        print(f"range: {start_mtd} → {today}")
        print(f"month-to-date cost: {amt:.2f} {unit}")
        return
    except ClientError as e:
        err = e.response.get("Error", {})
        code = (err.get("Code") or "").strip()
        msg = (err.get("Message") or "").lower()

        # Handle common first-run CE issues
        if code in ("DataUnavailableException", "AccessDeniedException") or \
           "data is not available" in msg or \
           "not enabled for cost explorer" in msg:
            start_prev, end_prev = last_month_range(today)
            try:
                amt, unit = get_cost(start_prev, end_prev)
                print("cost explorer is still ingesting current-month data.")
                print(f"showing last full month instead: {start_prev} → {end_prev}")
                print(f"total cost: {amt:.2f} {unit}")
                return
            except Exception as e2:
                print("fallback error (last month):", e2)
                return
        # Unknown client error: show it
        print("error:", code or "ClientError", "-", err.get("Message"))
        return
    except (BotoCoreError, Exception) as e:
        print("error:", e)
        return

if __name__ == "__main__":
    main()
