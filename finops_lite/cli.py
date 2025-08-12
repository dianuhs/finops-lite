"""
Enhanced CLI interface for FinOps Lite.
Professional-grade AWS cost management in your terminal.
"""

import click
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .utils.config import load_config, FinOpsConfig
from .utils.logger import setup_logger

# Global console for rich output
console = Console()

class FinOpsContext:
    def __init__(self):
        self.config: Optional[FinOpsConfig] = None
        self.logger = None
        self.verbose: bool = False
        self.dry_run: bool = False


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--dry-run', is_flag=True, help='Show demo data without AWS')
@click.pass_context
def cli(ctx, verbose, dry_run):
    """
    🔥 FinOps Lite - AWS Cost Management CLI
    
    Professional AWS cost visibility, optimization, and governance tools.
    """
    ctx.ensure_object(FinOpsContext)
    
    try:
        app_config = load_config()
        logger = setup_logger(verbose=verbose, quiet=False)
        
        ctx.obj.config = app_config
        ctx.obj.logger = logger
        ctx.obj.verbose = verbose
        ctx.obj.dry_run = dry_run
        
    except Exception as e:
        console.print(f"[red]Error initializing FinOps Lite: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--days', '-d', default=30, type=int, help='Number of days to analyze')
@click.pass_context
def demo(ctx, days):
    """Show beautiful demo cost data without AWS."""
    config = ctx.obj.config
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating demo data...", total=None)
        
        # Demo summary
        summary_text = f"""
[bold]Period:[/bold] Last {days} days ([italic]DEMO DATA[/italic])
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
        
        if ctx.obj.verbose:
            console.print(Panel(
                "💡 [bold]Optimization Opportunities:[/bold]\n\n• EC2 Rightsizing: $234/month potential savings\n• Reserved Instances: Consider RIs for consistent workloads", 
                title="🎯 Recommendations", 
                border_style="yellow"
            ))
        
        console.print("\n[dim]💡 This is demo data. Configure AWS credentials to see real costs.[/dim]")


@cli.command()
def version():
    """Show version information."""
    from . import __version__
    
    version_text = f"""
[bold]FinOps Lite[/bold] v{__version__}
[dim]Professional AWS cost management CLI[/dim]

Built with ❤️ for cloud cost optimization
"""
    
    console.print(Panel(version_text, title="📦 Version Info", border_style="blue"))


@cli.group()
def cost():
    """💰 Cost analysis and reporting commands."""
    pass


@cost.command()
@click.option('--days', '-d', default=30, type=int, help='Number of days')
@click.pass_context  
def overview(ctx, days):
    """Get cost overview."""
    if ctx.obj.dry_run:
        console.print("[yellow]Dry-run mode: showing demo data[/yellow]")
        ctx.invoke(demo, days=days)
    else:
        console.print("[red]Real AWS mode not implemented yet. Use 'demo' command.[/red]")


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
