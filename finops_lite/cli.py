"""
Enhanced CLI interface for FinOps Lite.
Professional-grade AWS cost management in your terminal.
"""

import click
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich import print as rich_print
from rich.text import Text

from .utils.config import load_config, FinOpsConfig
from .utils.logger import setup_logger

# Global console for rich output
console = Console()

# Context object to pass data between commands
class FinOpsContext:
    def __init__(self):
        self.config: Optional[FinOpsConfig] = None
        self.logger = None
        self.verbose: bool = False
        self.dry_run: bool = False


@click.group()
@click.option(
    '--config', '-c',
    type=click.Path(exists=True, path_type=Path),
    help='Path to configuration file'
)
@click.option(
    '--profile', '-p',
    help='AWS profile to use'
)
@click.option(
    '--region', '-r',
    help='AWS region to use'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
@click.option(
    '--quiet', '-q',
    is_flag=True,
    help='Suppress all output except errors'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show what would be done without making changes'
)
@click.option(
    '--output-format',
    type=click.Choice(['table', 'json', 'csv', 'yaml'], case_sensitive=False),
    help='Output format'
)
@click.option(
    '--no-color',
    is_flag=True,
    help='Disable colored output'
)
@click.pass_context
def cli(ctx, config, profile, region, verbose, quiet, dry_run, output_format, no_color):
    """
    🔥 FinOps Lite - AWS Cost Management CLI
    
    Professional AWS cost visibility, optimization, and governance tools.
    
    Examples:
      finops cost overview                    # Get cost overview
      finops cost by-service --days 7        # Service costs (7 days)
      finops tags compliance                  # Tag compliance report
      finops optimize rightsizing            # EC2 rightsizing recommendations
    """
    # Create context object
    ctx.ensure_object(FinOpsContext)
    
    try:
        # Load configuration
        app_config = load_config(config)
        
        # Override config with CLI options
        if profile:
            app_config.aws.profile = profile
        if region:
            app_config.aws.region = region
        if output_format:
            app_config.output.format = output_format
        if no_color:
            app_config.output.color = False
        if verbose:
            app_config.output.verbose = True
        if quiet:
            app_config.output.quiet = True
        
        # Setup logger
        logger = setup_logger(
            verbose=app_config.output.verbose,
            quiet=app_config.output.quiet
        )
        
        # Configure rich console
        if not app_config.output.color:
            console._color_system = None
        
        # Store in context
        ctx.obj.config = app_config
        ctx.obj.logger = logger
        ctx.obj.verbose = verbose
        ctx.obj.dry_run = dry_run
        
        # Commands that don't need AWS connectivity
        no_aws_commands = ['setup', 'version']
        
        # Test AWS connectivity only for commands that need it
        if (ctx.invoked_subcommand and 
            ctx.invoked_subcommand not in no_aws_commands and 
            not dry_run):
            _test_aws_connectivity(app_config, logger)
            
    except Exception as e:
        console.print(f"[red]Error initializing FinOps Lite: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


def _test_aws_connectivity(config: FinOpsConfig, logger):
    """Test AWS connectivity and permissions."""
    try:
        with console.status("[bold blue]Testing AWS connectivity..."):
            session = config.get_boto3_session()
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
        # Show connection info if verbose
        if config.output.verbose:
            table = Table(title="AWS Connection Info")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Account ID", identity.get('Account', 'Unknown'))
            table.add_row("User/Role", identity.get('Arn', 'Unknown').split('/')[-1])
            table.add_row("Region", config.aws.region or session.region_name or 'Unknown')
            
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]AWS connectivity test failed: {e}[/red]")
        console.print("[yellow]Tip: Check your AWS credentials and permissions[/yellow]")
        sys.exit(1)


@cli.group()
@click.pass_context
def cost(ctx):
    """💰 Cost analysis and reporting commands."""
    pass


@cost.command('overview')
@click.option(
    '--days', '-d',
    default=30,
    type=int,
    help='Number of days to analyze (default: 30)'
)
@click.option(
    '--group-by',
    type=click.Choice(['SERVICE', 'ACCOUNT', 'REGION', 'INSTANCE_TYPE'], case_sensitive=False),
    default='SERVICE',
    help='Group costs by dimension'
)
@click.pass_context
def cost_overview(ctx, days, group_by):
    """Get a comprehensive cost overview."""
    config = ctx.obj.config
    logger = ctx.obj.logger
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching cost data...", total=None)
            
            progress.update(task, description="Analyzing costs...")
            
            # Mock data for demonstration
            _display_cost_overview_mock(config, days, group_by)
            
    except Exception as e:
        console.print(f"[red]Error getting cost overview: {e}[/red]")
        if config.output.verbose:
            console.print_exception()
        sys.exit(1)


def _display_cost_overview_mock(config: FinOpsConfig, days: int, group_by: str):
    """Display mock cost overview (will be replaced with real data)."""
    
    # Cost summary panel
    summary_text = f"""
[bold]Period:[/bold] Last {days} days
[bold]Total Cost:[/bold] [green]$2,847.23[/green]
[bold]Daily Average:[/bold] $94.91
[bold]Trend:[/bold] [red]↗ +12.3%[/red] vs previous period
"""
    
    console.print(Panel(summary_text, title="📊 Cost Summary", border_style="blue"))
    
    # Top services table
    table = Table(title=f"💸 Top Costs by {group_by}")
    table.add_column("Service", style="cyan", no_wrap=True)
    table.add_column("Cost", style="green", justify="right")
    table.add_column("% of Total", style="yellow", justify="right")
    table.add_column("Trend", justify="center")
    
    # Mock data
    services = [
        ("EC2-Instance", "$1,234.56", "43.4%", "[red]↗[/red]"),
        ("RDS", "$543.21", "19.1%", "[green]↘[/green]"),
        ("S3", "$321.45", "11.3%", "[blue]→[/blue]"),
        ("Lambda", "$198.76", "7.0%", "[green]↘[/green]"),
        ("CloudWatch", "$87.65", "3.1%", "[red]↗[/red]"),
    ]
    
    for service, cost, percent, trend in services:
        table.add_row(service, cost, percent, trend)
    
    console.print(table)


@cli.command('version')
def version():
    """Show version information."""
    from . import __version__
    
    version_text = f"""
[bold]FinOps Lite[/bold] v{__version__}
[dim]Professional AWS cost management CLI[/dim]

Built with ❤️  for cloud cost optimization
"""
    
    console.print(Panel(version_text, title="📦 Version Info", border_style="blue"))


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
EOF