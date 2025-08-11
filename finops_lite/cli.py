#!/usr/bin/env python3
from __future__ import annotations

from datetime import date, timedelta, datetime
import os
import argparse
from collections import defaultdict

import boto3
from botocore.exceptions import ClientError

# Audit mode (make sure finops_lite/audit.py exists)
from finops_lite.audit import run_audit, DEFAULT_GB_MONTH, DEFAULT_EIP_HOURLY


# ---------- date helpers ----------
def first_of_month(d: date) -> date:
    return d.replace(day=1)


def last_month_range(today: date):
    start_this = first_of_month(today)
    last_day_prev = start_this - timedelta(days=1)
    start_prev = first_of_month(last_day_prev)
    return start_prev, start_this  # [start, end)


# ---------- boto session ----------
def make_session(profile: str | None, region: str | None):
    return boto3.Session(profile_name=profile, region_name=region)


# ---------- Cost Explorer helpers ----------
def fetch_total_cost(ce, start: date, end: date):
    """
    Monthly granularity; returns (amount, unit).
    """
    resp = ce.get_cost_and_usage(
        TimePeriod={"Start": start.strftime("%Y-%m-%d"), "End": end.strftime("%Y-%m-%d")},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
    )
    r = resp.get("ResultsByTime", [])
    total = r[0]["Total"]["UnblendedCost"] if r else {"Amount": "0", "Unit": "USD"}
    return float(total.get("Amount", "0")), total.get("Unit", "USD")


def fetch_services_cost(ce, start: date, end: date):
    """
    Daily granularity grouped by SERVICE; returns (dict service->amount, unit).
    """
    resp = ce.get_cost_and_usage(
        TimePeriod={"Start": start.strftime("%Y-%m-%d"), "End": end.strftime("%Y-%m-%d")},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    acc = defaultdict(float)
    unit = "USD"
    for bucket in resp.get("ResultsByTime", []):
        for grp in bucket.get("Groups", []):
            svc = grp["Keys"][0]
            amt = float(grp["Metrics"]["UnblendedCost"]["Amount"])
            unit = grp["Metrics"]["UnblendedCost"].get("Unit", unit)
            acc[svc] += amt
    return acc, unit


# ---------- CSV ----------
def write_csv(path, headers, rows):
    import csv
    import pathlib

    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)


# ---------- rendering ----------
def render_total(args, label: str, amount: float, unit: str):
    # CSV export
    if getattr(args, "csv", None):
        write_csv(args.csv, ["Label", "Estimated Total", "Unit"], [[label, f"{amount:.2f}", unit]])

    # Print
    print(label)
    print(f"Estimated total: ${amount:,.2f} {unit}")


def render_services(args, services: dict[str, float], unit: str, top: int):
    total = sum(services.values())
    top_items = sorted(services.items(), key=lambda kv: kv[1], reverse=True)[:top]
    headers = ["Service", "Est. Cost", "% of Total"]
    rows = []
    for svc, amt in top_items:
        pct = 0 if total == 0 else (amt / total * 100)
        rows.append([svc, f"${amt:,.2f}", f"{pct:.1f}%"])

    # CSV export
    if getattr(args, "csv", None):
        write_csv(args.csv, headers, rows)

    # Print
    print("Service                         Est. Cost      % of Total")
    for svc, fmt_amt, pct in rows:
        print(f"{svc:30} {fmt_amt:>12} {pct:>10}")


# ---------- argparse ----------
def add_common_flags(p: argparse.ArgumentParser):
    p.add_argument(
        "--profile",
        default=os.getenv("AWS_PROFILE"),
        help="AWS config profile (default: env AWS_PROFILE)",
    )
    p.add_argument(
        "--region",
        default=os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION"),
        help="AWS region (default: env AWS_REGION/AWS_DEFAULT_REGION)",
    )
    p.add_argument("--csv", metavar="PATH", help="Write the displayed table to CSV at PATH")


def parse_args():
    parser = argparse.ArgumentParser(prog="finops-lite", description="AWS FinOps Lite")
    add_common_flags(parser)
    parser.add_argument(
        "--last-month",
        action="store_true",
        help="Force last full month summary for default run",
    )

    sub = parser.add_subparsers(dest="cmd")

    # total
    p_total = sub.add_parser("total", help="Show estimated total for a period")
    add_common_flags(p_total)
    p_total.add_argument("--days", type=int, help="Look back N days (e.g., 30)")
    p_total.add_argument("--from", dest="from_date", help="Start date YYYY-MM-DD")
    p_total.add_argument("--to", dest="to_date", help="End date YYYY-MM-DD (exclusive)")

    # services
    p_services = sub.add_parser("services", help="Top services for a period")
    add_common_flags(p_services)
    p_services.add_argument("--days", type=int, default=30)
    p_services.add_argument("--from", dest="from_date", help="Start date YYYY-MM-DD")
    p_services.add_argument("--to", dest="to_date", help="End date YYYY-MM-DD (exclusive)")
    p_services.add_argument("--top", type=int, default=10)

    # audit
    p_audit = sub.add_parser(
        "audit",
        help="Detect waste: stopped EC2, unattached EBS, unused EIPs, untagged resources",
    )
    add_common_flags(p_audit)
    p_audit.add_argument(
        "--required-tags",
        default="Owner,CostCenter,Env",
        help="Comma-separated required tags to check (default: Owner,CostCenter,Env)",
    )
    p_audit.add_argument(
        "--assume-gb-month",
        type=float,
        default=DEFAULT_GB_MONTH,
        help=f"Assumed $/GB-month for unattached EBS (default: {DEFAULT_GB_MONTH})",
    )
    p_audit.add_argument(
        "--assume-eip-hour",
        type=float,
        default=DEFAULT_EIP_HOURLY,
        help=f"Assumed $/hour for unused EIPs (default: {DEFAULT_EIP_HOURLY})",
    )

    return parser.parse_args()


def compute_range(args, default_days: int | None = None):
    today = date.today()
    if getattr(args, "from_date", None) and getattr(args, "to_date", None):
        s = datetime.strptime(args.from_date, "%Y-%m-%d").date()
        e = datetime.strptime(args.to_date, "%Y-%m-%d").date()
        return s, e
    if getattr(args, "days", None):
        return today - timedelta(days=args.days), today
    if default_days:
        return today - timedelta(days=default_days), today
    return first_of_month(today), today


# ---------- main ----------
def main():
    args = parse_args()
    sess = make_session(args.profile, args.region)

    # subcommand: audit (doesn't use Cost Explorer; safe even when CE is warming up)
    if args.cmd == "audit":
        run_audit(
            session=sess,
            profile=args.profile,
            region=args.region,
            required_tags_csv=args.required_tags,
            gb_month_rate=args.assume_gb_month,
            eip_hour_rate=args.assume_eip_hour,
        )
        return

    ce = sess.client("ce")

    try:
        # subcommand: services
        if args.cmd == "services":
            start, end = compute_range(args, default_days=30)
            svc_map, unit = fetch_services_cost(ce, start, end)
            render_services(args, svc_map, unit, args.top)
            return

        # subcommand: total
        if args.cmd == "total":
            start, end = compute_range(args)
            amount, unit = fetch_total_cost(ce, start, end)
            label = f"Period: {start} → {end}"
            render_total(args, label, amount, unit)
            return

        # default summary: MTD with fallback to last full month
        today = date.today()
        start_mtd = first_of_month(today)
        try:
            amt, unit = fetch_total_cost(ce, start_mtd, today)
            render_total(args, f"Month-to-date ({start_mtd} → {today})", amt, unit)
            return
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("DataUnavailableException", "AccessDeniedException") or args.last_month:
                start_prev, end_prev = last_month_range(today)
                try:
                    amt, unit = fetch_total_cost(ce, start_prev, end_prev)
                    render_total(args, f"Last full month ({start_prev} → {end_prev})", amt, unit)
                    return
                except ClientError as e2:
                    code2 = e2.response.get("Error", {}).get("Code", "")
                    if code2 in ("DataUnavailableException", "AccessDeniedException"):
                        print(
                            "Cost Explorer isn’t ready yet. Try again in a few hours (up to ~24h after first enable)."
                        )
                        return
                    raise
            raise
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        msg = e.response.get("Error", {}).get("Message", "")
        print("AWS error:", code, msg)


if __name__ == "__main__":
    main()
