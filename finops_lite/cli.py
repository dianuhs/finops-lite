#!/usr/bin/env python3
from datetime import date, timedelta
import boto3
from botocore.exceptions import ClientError

# Import our new display functions
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Install 'rich' for better output: pip3 install rich")

def setup_display():
    if RICH_AVAILABLE:
        return Console()
    return None

def show_cost_summary(console, amount, unit, label, date_range):
    """Show cost with nice formatting"""
    if console:
        # Rich formatting
        summary = f"💰 {label}: [bold green]${amount:,.2f} {unit}[/bold green]\n📅 Period: {date_range}"
        panel = Panel(summary, title="🏦 AWS Cost Summary", border_style="blue")
        console.print(panel)
    else:
        # Fallback to plain text
        print(f"\n💰 {label}")
        print(f"Total cost: ${amount:.2f} {unit}")
        print(f"Period: {date_range}\n")

def show_error(console, message):
    """Show error message"""
    if console:
        panel = Panel(f"❌ {message}", title="Error", border_style="red")
        console.print(panel)
    else:
        print(f"❌ Error: {message}")

def show_info(console, message):
    """Show info message"""
    if console:
        panel = Panel(f"ℹ️ {message}", title="Info", border_style="yellow")
        console.print(panel)
    else:
        print(f"ℹ️ {message}")

def show_loading(console, message="Loading..."):
    """Show loading spinner or simple text"""
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

def fetch_cost(start: date, end: date):
    ce = boto3.client("ce")
    return ce.get_cost_and_usage(
        TimePeriod={"Start": start.strftime("%Y-%m-%d"), "End": end.strftime("%Y-%m-%d")},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
    )

def process_result(resp, console, label, date_range):
    """Process and display the cost result"""
    r = resp.get("ResultsByTime", [])
    total = r[0]["Total"]["UnblendedCost"] if r else {"Amount": "0", "Unit": "USD"}
    amount = float(total["Amount"])
    unit = total.get("Unit", "USD")
    
    show_cost_summary(console, amount, unit, label, date_range)

def main():
    console = setup_display()
    
    if console:
        console.print("\n[bold cyan]🚀 FinOps Lite - AWS Cost Explorer[/bold cyan]\n")
    else:
        print("\n🚀 FinOps Lite - AWS Cost Explorer\n")
    
    today = date.today()
    
    # Show loading
    progress = show_loading(console, "Fetching AWS cost data...")
    if progress:
        with progress:
            task = progress.add_task("Loading...", total=None)
            
            # Try month-to-date first
            start_mtd = first_of_month(today)
            try:
                resp = fetch_cost(start_mtd, today)
                progress.update(task, completed=100)
                
                date_range = f"{start_mtd} → {today}"
                process_result(resp, console, "Month-to-Date", date_range)
                return
                
            except ClientError as e:
                progress.update(task, completed=100)
                handle_error(e, console, today)
    else:
        # No rich progress, just fetch
        start_mtd = first_of_month(today)
        try:
            resp = fetch_cost(start_mtd, today)
            date_range = f"{start_mtd} → {today}"
            process_result(resp, console, "Month-to-Date", date_range)
            return
        except ClientError as e:
            handle_error(e, console, today)

def handle_error(e, console, today):
    """Handle AWS Cost Explorer errors"""
    code = e.response.get("Error", {}).get("Code", "")
    msg = e.response.get("Error", {}).get("Message", "")
    
    if code in ("DataUnavailableException", "AccessDeniedException"):
        show_info(console, "Cost Explorer is still ingesting current-month data.\nTrying last full month instead...")
        
        # Fall back to last full month
        start_prev, end_prev = last_month_range(today)
        try:
            resp = fetch_cost(start_prev, end_prev)
            date_range = f"{start_prev} → {end_prev}"
            process_result(resp, console, "Last Full Month", date_range)
            return
        except ClientError as e2:
            code2 = e2.response.get("Error", {}).get("Code", "")
            if code2 in ("DataUnavailableException", "AccessDeniedException"):
                show_error(console, 
                    "Cost Explorer isn't ready yet on this account.\n"
                    "This is normal right after you enable it.\n"
                    "Try again in a few hours (AWS says up to ~24h on first enable)."
                )
                return
            else:
                show_error(console, f"Unexpected error: {code2} - {e2}")
                return
    else:
        show_error(console, f"Unexpected error: {code} - {msg}")
        return

if __name__ == "__main__":
    main()
