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
from .utils.errors import (
    handle_error, 
    validate_days, 
    validate_threshold,
    validate_aws_profile,
    validate_aws_region,
    ValidationError, 
    AWSCredentialsError,
    CostExplorerNotEnabledError,
    CostExplorerWarmingUpError,
    APIRateLimitError,
    NetworkTimeoutError,
    AWSPermissionError,
    retry_with_backoff,
    aws_error_mapper
)
from .reports.formatters import ReportFormatter

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
    help='AWS profile to use',
    callback=lambda ctx, param, value: validate_aws_profile(value) if value else None
)
@click.option(
    '--region', '-r',
    help='AWS region to use',
    callback=lambda ctx, param, value: validate_aws_region(value) if value else None
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
    type=click.Choice(['table', 'json', 'csv', 'yaml', 'executive'], case_sensitive=False),
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
      finops cost overview --format json     # JSON output
      finops --output-format csv cost overview # CSV output
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
        
    except Exception as e:
        handle_error(e, verbose)
        sys.exit(1)


@aws_error_mapper
@retry_with_backoff(max_retries=2, base_delay=1.0, exceptions=(NetworkTimeoutError,))
def _test_aws_connectivity(config: FinOpsConfig, logger):
    """Test AWS connectivity and permissions with enhanced error handling."""
    try:
        with console.status("[bold blue]Testing AWS connectivity..."):
            session = config.get_boto3_session()
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
            # Test Cost Explorer specifically
            ce = session.client('ce')
            # Make a minimal Cost Explorer call to test permissions
            try:
                from datetime import datetime, timedelta
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=7)
                
                ce.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_date.strftime('%Y-%m-%d'),
                        'End': end_date.strftime('%Y-%m-%d')
                    },
                    Granularity='MONTHLY',
                    Metrics=['BlendedCost']
                )
                cost_explorer_status = "[green]✅ Available[/green]"
            except Exception as ce_error:
                error_msg = str(ce_error).lower()
                if 'data is not available' in error_msg or 'warming up' in error_msg:
                    cost_explorer_status = "[yellow]⏳ Warming up[/yellow]"
                elif 'not enabled' in error_msg:
                    cost_explorer_status = "[red]❌ Not enabled[/red]"
                else:
                    cost_explorer_status = "[yellow]⚠️  Permission issue[/yellow]"
            
        # Show connection info if verbose
        if config.output.verbose:
            table = Table(title="AWS Connection Info")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Account ID", identity.get('Account', 'Unknown'))
            table.add_row("User/Role", identity.get('Arn', 'Unknown').split('/')[-1])
            table.add_row("Region", config.aws.region or session.region_name or 'Unknown')
            table.add_row("Cost Explorer", cost_explorer_status)
            
            console.print(table)
            
    except Exception as e:
        # The aws_error_mapper decorator will convert this to appropriate custom exceptions
        raise


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
    help='Number of days to analyze (default: 30)',
    callback=lambda ctx, param, value: validate_days(value) if value else 30
)
@click.option(
    '--group-by',
    type=click.Choice(['SERVICE', 'ACCOUNT', 'REGION', 'INSTANCE_TYPE'], case_sensitive=False),
    default='SERVICE',
    help='Group costs by dimension'
)
@click.option(
    '--format', 'output_format',
    type=click.Choice(['table', 'json', 'csv', 'yaml', 'executive'], case_sensitive=False),
    help='Output format (overrides global setting)'
)
@click.option(
    '--export', 'export_file',
    help='Export report to file (e.g., report.json, costs.csv)'
)
@click.pass_context
def cost_overview(ctx, days, group_by, output_format, export_file):
    """Get a comprehensive cost overview with multiple output formats."""
    config = ctx.obj.config
    logger = ctx.obj.logger
    dry_run = ctx.obj.dry_run
    
    try:
        # Override format if specified
        if output_format:
            config.output.format = output_format
        
        if dry_run:
            # Check if non-table format requested
            if config.output.format != 'table':
                formatter = ReportFormatter(config, console)
                demo_data = {
                    'period_days': days, 
                    'total_cost': 2847.23, 
                    'daily_average': 94.91
                }
                console.print(f"[yellow]Generating {config.output.format.upper()} format (demo data)...[/yellow]")
                content = formatter.format_cost_overview(demo_data, config.output.format)
                if content:
                    console.print(content)
                    
                # Handle export
                if export_file:
                    formatter.save_report(content, export_file, config.output.format)
                    console.print(f"[green]Demo report exported to: {export_file}[/green]")
                return
            
            # Existing beautiful table format (unchanged)
            console.print("[yellow]Dry-run mode: showing demo data[/yellow]")
            
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
                console.print("\n[dim]💡 This is demo data. Configure AWS credentials to see real costs.[/dim]")
            return
        
        # Real AWS mode
        try:
            # Test AWS connectivity only when actually needed
            _test_aws_connectivity(config, logger)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Fetching cost data...", total=None)
                
                # Use real AWS Cost Explorer service with retry logic
                from .core.cost_explorer import CostExplorerService
                cost_service = CostExplorerService(config)
                
                progress.update(task, description="Analyzing costs...")
                cost_analysis = _get_cost_data_with_retry(cost_service, days)
                progress.update(task, description="Formatting results...")
                
                # Format and display based on format
                if config.output.format == 'table':
                    # Use existing beautiful table display
                    _display_cost_overview_real(config, cost_analysis, group_by)
                else:
                    # Use new formatter for other formats
                    formatter = ReportFormatter(config, console)
                    content = formatter.format_cost_overview(cost_analysis, config.output.format)
                    if content:
                        console.print(content)
                
                # Handle export for real data
                if export_file:
                    formatter = ReportFormatter(config, console)
                    content = formatter.format_cost_overview(cost_analysis, config.output.format)
                    if content:
                        formatter.save_report(content, export_file, config.output.format)
                        console.print(f"[green]Report exported to: {export_file}[/green]")
                
        except (CostExplorerNotEnabledError, CostExplorerWarmingUpError, 
                AWSCredentialsError, AWSPermissionError, APIRateLimitError, 
                NetworkTimeoutError) as e:
            handle_error(e, config.output.verbose)
            sys.exit(1)
            
    except ValidationError as e:
        handle_error(e, config.output.verbose)
        sys.exit(1)
    except Exception as e:
        handle_error(e, config.output.verbose)
        sys.exit(1)


@aws_error_mapper
@retry_with_backoff(max_retries=3, base_delay=2.0, exceptions=(APIRateLimitError, NetworkTimeoutError))
def _get_cost_data_with_retry(cost_service, days):
    """Get cost data with automatic retry for transient errors."""
    return cost_service.get_monthly_cost_overview(days)


def _display_cost_overview_real(config: FinOpsConfig, cost_analysis: dict, group_by: str):
    """Display real cost overview from AWS Cost Explorer."""
    
    # Format currency according to config
    currency = config.output.currency
    decimal_places = config.output.decimal_places
    
    def format_cost(amount):
        """Format cost amount with proper currency and decimals."""
        if currency == 'USD':
            return f"${amount:,.{decimal_places}f}"
        else:
            return f"{amount:,.{decimal_places}f} {currency}"
