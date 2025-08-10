#!/usr/bin/env python3
from __future__ import annotations
from datetime import date, timedelta
import argparse
import boto3
from collections import defaultdict

def first_of_month(d: date) -> date:
    return d.replace(day=1)

def last_month_range(today: date):
    start_this = first_of_month(today)
    last_day_prev = start_this - timedelta(days=1)
    start_prev = first_of_month(last_day_prev)
    return start_prev, start_this  # [start, end)

def ce_client():
    return boto3.client("ce")

def get_total_cost(start: date, end: date):
    """Return (amount, unit). Raises if CE not ready."""
    resp = ce_client().get_cost_and_usage(
        TimePeriod={"Start": start.strftime("%Y-%m-%d"), "End": end.strftime("%Y-%m-%d")},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
    )
    r = resp.get("ResultsByTime", [])
    total = r[0]["Total"]["UnblendedCost"] if r else {"Amount": "0", "Unit": "USD"}
    return float(total["Amount"]), total.get("Unit", "USD")

def get_cost_by_service_last_n_days(days: int = 30):
    """Sum DAILY UnblendedCost grouped by SERVICE over the last N days."""
    today = date.today()
    start = today - timedelta(days=days)
    end = today  # CE end is exclusive; using today is fine
    resp = ce_client().get_cost_and_usage(
        TimePeriod={"Start": start.strftime("%Y-%m-%d"), "End": end.strftime("%Y-%m-%d")},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    totals = defaultdict(float)
    unit = "USD"
    for day in resp.get("ResultsByTime", []):
        for group in day.get("Groups", []):
            svc = group["Keys"][0]
            amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
            unit = group["Metrics"]["UnblendedCost"].get("Unit", unit)
            totals[svc] += amount
    # Return sorted list (desc by amount)
    items = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    return items, unit, start, end

def print_services(items, unit, start, end, top: int | None = 15):
    print(f"services — last { (end - start).days } days: {start} → {end}")
    if not items:
        print("no service data returned.")
        return
    if top:
        items = items[:top]
    width_name = max(len(k) for k, _v in items) if items else 10
    for name, amt in items:
        print(f"{name.ljust(width_name)}  {amt:10.2f} {unit}")
    total = sum(v for _k, v in items)
    print("-" * (width_name + 16))
    print(f"{'subtotal'.ljust(width_name)}  {total:10.2f} {unit}")

def do_totals(args):
    print("finops lite")
    today = date.today()
    if args.last_month:
        start, end = last_month_range(today)
        try:
            amt, unit = get_total_cost(start, end)
            print(f"last full month: {start} → {end}")
            print(f"total cost: {amt:.2f} {unit}")
            return
        except Exception:
            pass  # fall through to friendly message
    else:
        # default: month-to-date with fallback to last month
        start_mtd = first_of_month(today)
        try:
            amt, unit = get_total_cost(start_mtd, today)
            print(f"range: {start_mtd} → {today}")
            print(f"month-to-date cost: {amt:.2f} {unit}")
            return
        except Exception:
            # fallback to last month
            start, end = last_month_range(today)
            try:
                amt, unit = get_total_cost(start, end)
                print("cost explorer is still ingesting current-month data.")
                print(f"showing last full month instead: {start} → {end}")
                print(f"total cost: {amt:.2f} {unit}")
                return
            except Exception:
                pass
    # Friendly final message if CE isn’t ready yet
    print("cost explorer isn’t ready on this account yet. this is normal right after enabling it.")
    print("try again in a few hours (aws can take up to ~24h on first enable).")

def do_services(args):
    print("finops lite")
    try:
        items, unit, start, end = get_cost_by_service_last_n_days(args.days)
        print_services(items, unit, start, end, top=args.top)
    except Exception:
        print("couldn’t fetch service costs yet — cost explorer probably still ingesting.")
        print("try again later; this will work automatically once CE finishes.")

def main():
    parser = argparse.ArgumentParser(prog="finops-lite", description="FinOps Lite — tiny AWS cost helper")
    sub = parser.add_subparsers(dest="command")

    # totals (default)
    parser.add_argument("--last-month", action="store_true", help="show last full month instead of month-to-date")

    # services
    p_svc = sub.add_parser("services", help="show cost by AWS service over the last N days (default 30)")
    p_svc.add_argument("--days", type=int, default=30, help="number of days to include (default 30)")
    p_svc.add_argument("--top", type=int, default=15, help="show top N services (default 15)")

    args = parser.parse_args()

    if args.command == "services":
        do_services(args)
    else:
        do_totals(args)

if __name__ == "__main__":
    main()
