#!/usr/bin/env python3
from datetime import date, timedelta
import boto3
from botocore.exceptions import ClientError

def first_of_month(d: date) -> date:
    return d.replace(day=1)

def last_month_range(today: date):
    start_this = first_of_month(today)
    last_day_prev = start_this - timedelta(days=1)
    start_prev = first_of_month(last_day_prev)
    return start_prev, start_this  # [start, end)

def fetch_cost(start: date, end: date):
    ce = boto3.client("ce")
    return ce.get_cost_and_usage(
        TimePeriod={"Start": start.strftime("%Y-%m-%d"), "End": end.strftime("%Y-%m-%d")},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
    )

def print_result(resp, label):
    r = resp.get("ResultsByTime", [])
    total = r[0]["Total"]["UnblendedCost"] if r else {"Amount": "0", "Unit": "USD"}
    amount = float(total["Amount"])
    unit = total.get("Unit", "USD")
    print(label)
    print(f"total cost: {amount:.2f} {unit}")

def main():
    print("finops lite")
    today = date.today()

    # Try month-to-date first
    start_mtd = first_of_month(today)
    try:
        resp = fetch_cost(start_mtd, today)
        print(f"range: {start_mtd} → {today}")
        print_result(resp, "month-to-date")
        return
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        msg = e.response.get("Error", {}).get("Message", "")
        if code in ("DataUnavailableException", "AccessDeniedException"):
            # Fall back to last full month, which also may be unavailable on day 1
            start_prev, end_prev = last_month_range(today)
            try:
                resp = fetch_cost(start_prev, end_prev)
                print("cost explorer is still ingesting current-month data.")
                print(f"showing last full month instead: {start_prev} → {end_prev}")
                print_result(resp, "last full month")
                return
            except ClientError as e2:
                code2 = e2.response.get("Error", {}).get("Code", "")
                if code2 in ("DataUnavailableException", "AccessDeniedException"):
                    print("cost explorer isn’t ready yet on this account. this is normal right after you enable it.")
                    print("try again in a few hours (AWS says up to ~24h on first enable).")
                    return
                else:
                    print("unexpected error:", code2, e2)
                    return
        else:
            print("unexpected error:", code, msg)
            return

if __name__ == "__main__":
    main()
