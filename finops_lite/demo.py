from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Demo data
summary_text = """
[bold]Period:[/bold] Last 30 days ([italic]DEMO DATA[/italic])
[bold]Total Cost:[/bold] [green]$2,847.23[/green]
[bold]Daily Average:[/bold] $94.91
[bold]Trend:[/bold] [red]↗ +12.3%[/red] vs previous period
"""

console.print(Panel(summary_text, title="📊 Cost Summary (Demo)", border_style="blue"))

# Demo table
table = Table(title="💸 Top AWS Services (Demo)")
table.add_column("Service", style="cyan", no_wrap=True)
table.add_column("Cost", style="green", justify="right")
table.add_column("% of Total", style="yellow", justify="right")
table.add_column("Trend", justify="center")

demo_services = [
    ("Amazon EC2", "$1,234.56", "43.4%", "[red]↗[/red]"),
    ("Amazon RDS", "$543.21", "19.1%", "[green]↘[/green]"),
    ("Amazon S3", "$321.45", "11.3%", "[blue]→[/blue]"),
    ("AWS Lambda", "$198.76", "7.0%", "[green]↘[/green]"),
    ("CloudWatch", "$87.65", "3.1%", "[red]↗[/red]"),
]

for service, cost, percent, trend in demo_services:
    table.add_row(service, cost, percent, trend)

console.print(table)
console.print("\n[dim]💡 This is demo data showing how beautiful your FinOps CLI looks![/dim]")
