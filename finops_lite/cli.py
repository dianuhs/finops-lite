#!/usr/bin/env python3
from __future__ import annotations
from datetime import date, timedelta, datetime
import os
import argparse
import boto3
from botocore.exceptions import ClientError
from collections import defaultdict

# Optional pretty output with Rich (falls back to plain text if not installed)
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    RICH = True
    console = Console()
except Exception:
    RICH = False
    console = None

# ---------- dates ----------
def first_of_month(d: date) -> date:
    return d.replace(day=1)

def last_month_range(today: date):
    start_this = first_of_month(today)
    last_day_prev = start_this - timedelta(days=1)
    start_prev = first_of_month(last_day_prev)
    return start_prev, start_this  # [start, end)

# ---------- sessions / clients ----------
def make_session(profile: str | None, region: str | None):
    return boto3.Session(profile_name=profile, region_name=region)

# ---------- CE helpers ----------
def fetch_total_cost(ce, start: date, end: date):
    """Monthly granularity; return (amount, unit)."""
    resp = ce.get_cost_and_usage(
        TimePeriod={"Start": start.strftime("%Y-%m-%d"), "End": end.strftime("%Y-%m-%d")},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
    )
    r = resp.get("ResultsByTime", [])
    total = r[0]["Total"]["UnblendedCost"] if r else {"Amount": "0", "Unit": "USD"}
    return float(total.get("Amount", "0")), total.get("Unit", "USD")

def fetch_services_cost(ce, start: date, end: date):
    """Daily granularity grouped by SERVICE; return (dict service->amount, unit)."""
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
    import csv, pathlib
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)

# ---------- rendering ----------
def render_total(label: str, amount: float, unit: str, csv_path: str | None = None):
    if csv_path:
        write_csv(csv_path, ["Label", "Estimated Total", "Unit"], [[label, f"{amount:.2f}", unit]])
    if RICH:
        console.print(Panel.fit(f"[bold]{label}[/bold]\n\n[bold green]${amount:,.2f}[/bold green] {unit}",
                                title="AWS Total"))
    else:
        print(label)
        print(f"total cost: {amount:.2f} {unit}")

def render_services(services: dict[str, float], unit: str, top: int, csv_path: str | None = None):
    total = sum(services.values())
    top_items = sorted(services.items(), key=lambda kv: kv[1], reverse=True)[:top]
    headers = ["Service", "Est. Cost", "% of Total"]
    rows = []
    for svc, amt in top_items:
        pct = 0 if total == 0 else (amt / total * 100)
        rows.append([svc, f"${amt:,.2f}", f"{pct:.1f}%"])
    if csv_path:
        write_csv(csv_path, headers, rows)

    if RICH:
        table = Table(title="Top services", show_header=True, header_style="bold")
        for h in headers:
            table.add_column(h)
        for svc, fmt_amt, pct in rows:
            table.add_row(svc, fmt_amt, pct)
        console.print(table)
    else:
        print("Service                   Est. Cost      % of Total")
        for svc, fmt_amt, pct in rows:
            print(f"{svc:25} {fmt_amt:>12} {pct:>10}")

# ---------- argparse ----------
def add_common_flags(p: argparse.ArgumentParser):
    p.add_argument("--profile", default=os.getenv("AWS_PROFILE"),
                   help="AWS config profile (default: env AWS_PROFILE)")
    p.add_argument("--region", default=os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION"),
                   help="AWS region (default: env AWS_REGION/AWS_DEFAULT_REGION)")
    p.add_argument("--csv", metavar="PATH", help="Write the displayed table to CSV at PATH")

def parse_args():
    parser = argparse.ArgumentParser(prog="finops-lite", description="AWS FinOps Lite")
    add_common_flags(parser)
    parser.add_argument("--last-month", action="store_true", help="Force last full month summary")
    sub = parser.add_subparsers(dest="cmd")

    p_total = sub.add_parser("total", help="Show estimated total for a period")
    add_common_flags(p_total)
    p_total.add_argument("--days", type=int, help="Look back N days (e.g., 30)")
    p_total.add_argument("--from", dest="from_date", help="Start date YYYY-MM-DD")
    p_total.add_argument("--to", dest="to_date", help="End date YYYY-MM-DD (exclusive)")

    p_services = sub.add_parser("services", help="Top services for a period")
    add_common_flags(p_services)
    p_services.add_argument("--days", type=int, default=30)
    p_services.add_argument("--from", dest="from_date", help="Start date YYYY-MM-DD")
    p_services.add_argument("--to", dest="to_date", help="End date YYYY-MM-DD (exclusive)")
    p_services.add_argument("--top", type=int, default=10)

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
    ce = sess.client("ce")

    try:
        # subcommand: services
        if args.cmd == "services":
            start, end = compute_range(args, default_days=30)
            svc_map, unit = fetch_services_cost(ce, start, end)
            render_services(svc_map, unit, args.top, csv_path=args.csv)
            return

        # subcommand: total
        if args.cmd == "total":
            start, end = compute_range(args)
            amount, unit = fetch_total_cost(ce, start, end)
            label = f"Period: {start} → {end}"
            render_total(label, amount, unit, csv_path=args.csv)
            return

        # default summary: MTD with fallback to last full month
        today = date.today()
        start_mtd = first_of_month(today)
        try:
            amt, unit = fetch_total_cost(ce, start_mtd, today)
            render_total(f"Month-to-date ({start_mtd} → {today})", amt, unit, csv_path=args.csv)
            return
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("DataUnavailableException", "AccessDeniedException") or args.last_month:
                start_prev, end_prev = last_month_range(today)
                try:
                    amt, unit = fetch_total_cost(ce, start_prev, end_prev)
                    render_total(f"Last full month ({start_prev} → {end_prev})", amt, unit, csv_path=args.csv)
                    return
                except ClientError as e2:
                    code2 = e2.response.get("Error", {}).get("Code", "")
                    if code2 in ("DataUnavailableException", "AccessDeniedException"):
                        msg = "Cost Explorer isn’t ready yet. Try again in a few hours (up to ~24h after first enable)."
                        if RICH:
                            console.print(f"[bold red]{msg}[/bold red]")
                        else:
                            print(msg)
                        return
                    raise
            raise
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        msg = e.response.get("Error", {}).get("Message", "")
        if RICH:
            console.print(f"[bold red]AWS error {code}: {msg}[/bold red]")
        else:
            print("unexpected error:", code, msg)

if __name__ == "__main__":
    main()
