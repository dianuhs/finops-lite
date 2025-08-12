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
from .utils.errors import handle_error, validate_days, ValidationError, AWSCredentialsError
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
        raise AWSCredentialsError(f"Unable to locate credentials: {e}")


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
                
                # Use real AWS Cost Explorer service
                from .core.cost_explorer import CostExplorerService
                cost_service = CostExplorerService(config)
                
                progress.update(task, description="Analyzing costs...")
                cost_analysis = cost_service.get_monthly_cost_overview(days)
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
                
        except AWSCredentialsError as e:
            handle_error(e, config.output.verbose)
            sys.exit(1)
            
    except ValidationError as e:
        handle_error(e, config.output.verbose)
        sys.exit(1)
    except Exception as e:
        handle_error(e, config.output.verbose)
        sys.exit(1)


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
    
    # Cost summary panel
    total_cost = cost_analysis['total_cost']
    daily_avg = cost_analysis['daily_average']
    trend = cost_analysis['trend']
    
    # Format trend direction
    if trend.trend_direction == 'up':
        trend_icon = "[red]↗[/red]"
        trend_color = "red"
    elif trend.trend_direction == 'down':
        trend_icon = "[green]↘[/green]"
        trend_color = "green"
    else:
        trend_icon = "[blue]→[/blue]"
        trend_color = "blue"
    
    trend_text = f"{trend_icon} {trend.change_percentage:+.1f}%"
    
    summary_text = f"""
[bold]Period:[/bold] Last {cost_analysis['period_days']} days
[bold]Total Cost:[/bold] [green]{format_cost(total_cost)}[/green]
[bold]Daily Average:[/bold] {format_cost(daily_avg)}
[bold]Trend:[/bold] {trend_text} vs previous period
[bold]Currency:[/bold] {currency}
"""
    
    console.print(Panel(summary_text, title="📊 Cost Summary", border_style="blue"))
    
    # Service breakdown table
    service_breakdown = cost_analysis['service_breakdown']
    
    if service_breakdown:
        table = Table(title=f"💸 Top Costs by Service")
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("Cost", style="green", justify="right")
        table.add_column("% of Total", style="yellow", justify="right")
        table.add_column("Daily Avg", style="blue", justify="right")
        table.add_column("Trend", justify="center")
        
        for service in service_breakdown[:10]:  # Show top 10
            # Format service trend
            service_trend = service.trend
            if service_trend.trend_direction == 'up':
                service_trend_icon = "[red]↗[/red]"
            elif service_trend.trend_direction == 'down':
                service_trend_icon = "[green]↘[/green]"
            else:
                service_trend_icon = "[blue]→[/blue]"
            
            table.add_row(
                service.service_name,
                format_cost(service.total_cost),
                f"{service.percentage_of_total:.1f}%",
                format_cost(service.daily_average),
                service_trend_icon
            )
        
        console.print(table)
        
        # Show optimization opportunities if verbose
        if config.output.verbose:
            _show_optimization_opportunities(service_breakdown, format_cost)
    else:
        console.print("[yellow]No cost data available for the specified period[/yellow]")


def _show_optimization_opportunities(service_breakdown: list, format_cost):
    """Show potential cost optimization opportunities."""
    
    # Find services with high costs or upward trends
    high_cost_services = [s for s in service_breakdown if s.total_cost > 100]  # > $100
    trending_up_services = [s for s in service_breakdown if s.trend.trend_direction == 'up']
    
    opportunities = []
    
    # EC2 optimization opportunities
    ec2_services = [s for s in service_breakdown if 'EC2' in s.service_name.upper()]
    if ec2_services:
        total_ec2_cost = sum(s.total_cost for s in ec2_services)
        if total_ec2_cost > 50:  # > $50
            opportunities.append(f"• [yellow]EC2 Rightsizing:[/yellow] {format_cost(total_ec2_cost)} in EC2 costs - consider rightsizing analysis")
    
    # RDS optimization
    rds_services = [s for s in service_breakdown if 'RDS' in s.service_name.upper()]
    if rds_services:
        total_rds_cost = sum(s.total_cost for s in rds_services)
        if total_rds_cost > 30:  # > $30
            opportunities.append(f"• [yellow]RDS Optimization:[/yellow] {format_cost(total_rds_cost)} in RDS costs - review instance types and storage")
    
    # Services with upward trends
    if trending_up_services:
        trending_cost = sum(s.total_cost for s in trending_up_services[:3])
        opportunities.append(f"• [yellow]Cost Trend Alert:[/yellow] {len(trending_up_services)} services trending up ({format_cost(trending_cost)})")
    
    # Reserved Instance opportunities
    if any('EC2' in s.service_name.upper() for s in high_cost_services):
        opportunities.append("• [yellow]Reserved Instances:[/yellow] Consider RIs for consistent EC2 workloads")
    
    if opportunities:
        opportunities_text = "\n".join(opportunities)
        console.print(Panel(
            f"[bold]💡 Optimization Opportunities:[/bold]\n\n{opportunities_text}", 
            title="🎯 Recommendations", 
            border_style="yellow"
        ))


@cli.group()
def tags():
    """🏷️  Tag compliance and governance commands."""
    pass


@tags.command('compliance')
@click.option(
    '--service',
    help='Filter by AWS service (e.g., ec2, rds, s3)'
)
@click.option(
    '--fix',
    is_flag=True,
    help='Interactively fix tag compliance issues'
)
@click.pass_context
def tag_compliance(ctx, service, fix):
    """Check tag compliance across resources."""
    config = ctx.obj.config
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Scanning resources...", total=None)
            
            # Mock compliance report for now
            _display_tag_compliance_mock(config, service, fix)
            
    except Exception as e:
        handle_error(e, config.output.verbose)
        sys.exit(1)


def _display_tag_compliance_mock(config: FinOpsConfig, service_filter: str, fix: bool):
    """Display mock tag compliance report."""
    
    # Compliance summary
    summary_text = f"""
[bold]Resources Scanned:[/bold] 156
[bold]Compliant:[/bold] [green]89 (57%)[/green]
[bold]Non-Compliant:[/bold] [red]67 (43%)[/red]
[bold]Required Tags:[/bold] {', '.join(config.tagging.required_tags)}
"""
    
    console.print(Panel(summary_text, title="🏷️  Tag Compliance Report", border_style="blue"))
    
    # Non-compliant resources table
    table = Table(title="❌ Non-Compliant Resources")
    table.add_column("Resource", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Missing Tags", style="red")
    table.add_column("Cost Impact", style="green", justify="right")
    
    # Mock non-compliant resources
    resources = [
        ("i-1234567890abcdef0", "EC2 Instance", "Environment, Owner", "$123.45"),
        ("vol-abcdef1234567890", "EBS Volume", "Project", "$45.67"),
        ("rds-production-db", "RDS Instance", "CostCenter", "$234.56"),
    ]
    
    for resource, resource_type, missing, cost in resources:
        table.add_row(resource, resource_type, missing, cost)
    
    console.print(table)
    
    if fix:
        console.print("\n[bold yellow]Interactive tag fixing mode:[/yellow]")
        if Confirm.ask("Would you like to fix tag compliance issues?"):
            console.print("[green]Tag fixing functionality coming soon![/green]")


@cli.group()
def optimize():
    """🚀 Cost optimization commands."""
    pass


@optimize.command('rightsizing')
@click.option(
    '--service',
    type=click.Choice(['ec2', 'rds', 'all'], case_sensitive=False),
    default='ec2',
    help='Service to analyze for rightsizing'
)
@click.option(
    '--savings-threshold',
    type=float,
    default=10.0,
    help='Minimum monthly savings threshold (default: $10)'
)
@click.pass_context
def rightsizing_recommendations(ctx, service, savings_threshold):
    """Get rightsizing recommendations for underutilized resources."""
    config = ctx.obj.config
    
    try:
        # Validate savings threshold
        if savings_threshold < 0:
            raise ValidationError("Savings threshold must be positive")
            
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing resource utilization...", total=None)
            
            _display_rightsizing_mock(config, service, savings_threshold)
            
    except ValidationError as e:
        handle_error(e, config.output.verbose)
        sys.exit(1)
    except Exception as e:
        handle_error(e, config.output.verbose)
        sys.exit(1)


def _display_rightsizing_mock(config: FinOpsConfig, service: str, threshold: float):
    """Display mock rightsizing recommendations."""
    
    summary_text = f"""
[bold]Service:[/bold] {service.upper()}
[bold]Resources Analyzed:[/bold] 23
[bold]Recommendations:[/bold] 8
[bold]Potential Monthly Savings:[/bold] [green]${threshold * 45.68:.2f}[/green]
"""
    
    console.print(Panel(summary_text, title="🚀 Rightsizing Analysis", border_style="green"))
    
    # Recommendations table
    table = Table(title="💡 Rightsizing Recommendations")
    table.add_column("Resource", style="cyan")
    table.add_column("Current", style="yellow")
    table.add_column("Recommended", style="green")
    table.add_column("Monthly Savings", style="green", justify="right")
    table.add_column("Confidence", justify="center")
    
    recommendations = [
        ("i-1234567890abcdef0", "m5.large", "m5.medium", f"${threshold * 6.73:.2f}", "[green]High[/green]"),
        ("i-abcdef1234567890", "c5.xlarge", "c5.large", f"${threshold * 12.35:.2f}", "[yellow]Medium[/yellow]"),
        ("i-9876543210fedcba", "r5.2xlarge", "r5.xlarge", f"${threshold * 23.46:.2f}", "[green]High[/green]"),
    ]
    
    for resource, current, recommended, savings, confidence in recommendations:
        table.add_row(resource, current, recommended, savings, confidence)
    
    console.print(table)


@cli.command('setup')
@click.option(
    '--interactive', '-i',
    is_flag=True,
    help='Run interactive setup wizard'
)
def setup_config(interactive):
    """🔧 Set up FinOps Lite configuration."""
    try:
        if interactive:
            console.print("[bold blue]🔧 FinOps Lite Setup Wizard[/bold blue]")
            console.print("This will help you configure FinOps Lite for your AWS environment.\n")
            
            # Interactive setup would go here
            console.print("[green]Interactive setup coming soon![/green]")
            console.print("For now, copy the template from config/templates/finops.yaml")
        else:
            console.print("Configuration template available at: config/templates/finops.yaml")
            console.print("Copy it to one of these locations:")
            console.print("  • ./finops.yaml")
            console.print("  • ~/.config/finops/config.yaml")
            console.print("  • ~/.finops.yaml")
    except Exception as e:
        handle_error(e, verbose=False)


@cli.command('version')
def version():
    """Show version information."""
    try:
        from . import __version__
        
        version_text = f"""
[bold]FinOps Lite[/bold] v{__version__}
[dim]Professional AWS cost management CLI[/dim]

Built with ❤️  for cloud cost optimization
"""
        
        console.print(Panel(version_text, title="📦 Version Info", border_style="blue"))
    except Exception as e:
        handle_error(e, verbose=False)


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        handle_error(e, verbose=False)
        sys.exit(1)


if __name__ == '__main__':
    main()
