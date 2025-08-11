#!/usr/bin/env python3
from __future__ import annotations
from datetime import date, timedelta
import argparse
import boto3
from collections import defaultdict

# Import rich for beautiful output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

def show_header():
    """Show app header"""
    if console:
        console.print("\n[bold cyan]🚀 FinOps Lite - AWS Cost Explorer[/bold cyan]\n")
    else:
        print("\n🚀 FinOps Lite - AWS Cost Explorer\n")

def show_cost_summary(amount, unit, label, date_range):
    """Show cost summary with beautiful formatting"""
    if console:
        summary = f"💰 {label}: [bold green]${amount:,.2f} {unit}[/bold green]\n📅 Period: {date_range}"
        panel = Panel(summary, title="🏦 AWS Cost Summary", border_style="blue")
        console.print(panel)
    else:
        print(f"💰 {label}: ${amount:.2f} {unit}")
        print(f"📅 Period: {date_range}")

def show_services_table(items, unit, start, end, top=15):
    """Show services in a beautiful table"""
    if not items:
        show_error("No service data returned")
        return
    
    days = (end - start).days
    
    if console:
        table = Table(
            title=f"💸 Top Services - Last {days} Days ({start} → {end})",
            box=box.ROUNDED,
            header_style="bold magenta"
        )
        
        table.add_column("Service", style="cyan", min_width=20)
        table.add_column("Cost", justify="right", style="green")
        table.add_column("% of Total", justify="right", style="yellow")
        
        # Calculate total for percentages
        total_cost = sum(amt for _, amt in items)
        
        # Show top N services
        display_items = items[:top] if top else items
        
        for name, amt in display_items:
            percentage = (amt / total_cost * 100) if total_cost > 0 else 0
            table.add_row(
                name,
                f"${amt:,.2f}",
                f"{percentage:.1f}%"
            )
        
        console.print(table)
        
        # Show total
        total_panel = Panel(
            f"[bold green]Total Cost: ${total_cost:,.2f} {unit}[/bold green]",
            title="Summary",
            border_style="green"
        )
        console.print(total_panel)
    else:
        # Fallback to your original formatting
        print(f"services — last {days} days: {start} → {end}")
        display_items = items[:top] if top else items
        width_name = max(len(k) for k, _v in display_items) if display_items else 10
        
        for name, amt in display_items:
            print(f"{name.ljust(width_name)}  {amt:10.2f} {unit}")
        
        total = sum(v for _k, v in display_items)
        print("-" * (width_name + 16))
        print(f"{'subtotal'.ljust(width_name)}  {total:10.2f} {unit}")

def show_error(message):
    """Show error message"""
    if console:
        panel = Panel(f"❌ {message}", title="Error", border_style="red")
        console.print(panel)
    else:
        print(f"❌ {message}")

def show_info(message):
    """Show info message"""
    if console:
        panel = Panel(f"ℹ️ {message}", title="Info", border_style="yellow")
        console.print(panel)
    else:
        print(f"ℹ️ {message}")

def show_loading(message="Loading..."):
    """Show loading spinner"""
    if console and RICH_AVAILABLE:
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        )
    else:
        print(f"⏳ {message}")
        return None

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

def do_totals(args):
    show_header()
    today = date.today()
    
    if args.last_month:
        start, end = last_month_range(today)
        progress = show_loading("Fetching last month costs...")
        
        if progress:
            with progress:
                task = progress.add_task("Loading...", total=None)
                try:
                    amt, unit = get_total_cost(start, end)
                    progress.update(task, completed=100)
                    show_cost_summary(amt, unit, "Last Full Month", f"{start} → {end}")
                    return
                except Exception:
                    progress.update(task, completed=100)
        else:
            try:
                amt, unit = get_total_cost(start, end)
                show_cost_summary(amt, unit, "Last Full Month", f"{start} → {end}")
                return
            except Exception:
                pass
    else:
        # default: month-to-date with fallback to last month
        start_mtd = first_of_month(today)
        progress = show_loading("Fetching month-to-date costs...")
        
        if progress:
            with progress:
                task = progress.add_task("Loading...", total=None)
                try:
                    amt, unit = get_total_cost(start_mtd, today)
                    progress.update(task, completed=100)
                    show_cost_summary(amt, unit, "Month-to-Date", f"{start_mtd} → {today}")
                    return
                except Exception:
                    progress.update(task, description="Trying last month as fallback...")
                    # fallback to last month
                    start, end = last_month_range(today)
                    try:
                        amt, unit = get_total_cost(start, end)
                        progress.update(task, completed=100)
                        show_info("Cost Explorer is still ingesting current-month data.\nShowing last full month instead.")
                        show_cost_summary(amt, unit, "Last Full Month", f"{start} → {end}")
                        return
                    except Exception:
                        progress.update(task, completed=100)
        else:
            try:
                amt, unit = get_total_cost(start_mtd, today)
                show_cost_summary(amt, unit, "Month-to-Date", f"{start_mtd} → {today}")
                return
            except Exception:
                # fallback to last month
                start, end = last_month_range(today)
                try:
                    amt, unit = get_total_cost(start, end)
                    show_info("Cost Explorer is still ingesting current-month data.\nShowing last full month instead.")
                    show_cost_summary(amt, unit, "Last Full Month", f"{start} → {end}")
                    return
                except Exception:
                    pass
    
    # Friendly final message if CE isn't ready yet
    show_error(
        "Cost Explorer isn't ready on this account yet.\n"
        "This is normal right after enabling it.\n"
        "Try again in a few hours (AWS can take up to ~24h on first enable)."
    )

def do_services(args):
    show_header()
    progress = show_loading(f"Fetching service costs for last {args.days} days...")
    
    if progress:
        with progress:
            task = progress.add_task("Loading...", total=None)
            try:
                items, unit, start, end = get_cost_by_service_last_n_days(args.days)
                progress.update(task, completed=100)
                show_services_table(items, unit, start, end, top=args.top)
            except Exception:
                progress.update(task, completed=100)
                show_error(
                    "Couldn't fetch service costs yet — Cost Explorer probably still ingesting.\n"
                    "Try again later; this will work automatically once CE finishes."
                )
    else:
        try:
            items, unit, start, end = get_cost_by_service_last_n_days(args.days)
            show_services_table(items, unit, start, end, top=args.top)
        except Exception:
            show_error(
                "Couldn't fetch service costs yet — Cost Explorer probably still ingesting.\n"
                "Try again later; this will work automatically once CE finishes."
            )

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
