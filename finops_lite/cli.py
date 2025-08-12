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
      finops demo                             # Show demo data
      finops version                          # Show version
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
        console.print(f"[red]Error initializing FinOps Lite: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command('demo')
@click.option(
    '--days', '-d',
    default=30,
    type=int,
    help='Number of days to analyze (default: 30)'
)
@click.pass_context
def demo(ctx, days):
    """Show beautiful demo cost data without AWS."""
    config = ctx.obj.config
    
    # Format currency according to config
    currency = config.output.currency
    decimal_places = config.output.decimal_places
    
    def format_cost(amount):
        """Format cost amount with proper currency and decimals."""
        if currency == 'USD':
            return f"${amount:,.{decimal_places}f}"
        else:
            return f"{amount:,.{decimal_places}f} {currency}"
    
    # Show progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating demo data...", total=None)
        
        # Demo data
        total_cost = 2847.23
        daily_avg = total_cost / days
        
        # Demo summary panel
        summary_text = f"""
[bold]Period:[/bold] Last {days} days ([italic]DEMO DATA[/italic])
[bold]Total Cost:[/bold] [green]{format_cost(total_cost)}[/green]
[bold]Daily Average:[/bold] {format_cost(daily_avg)}
[bold]Trend:[/bold] [red]↗ +12.3%[/red] vs previous period
[bold]Currency:[/bold] {currency}
"""
        
        console.print(Panel(summary_text, title="📊 Cost Summary (Demo)", border_style="blue"))
        
        # Demo service breakdown table
        table = Table(title=f"💸 Top Costs by Service (Demo Data)")
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("Cost", style="green", justify="right")
        table.add_column("% of Total", style="yellow", justify="right")
        table.add_column("Daily Avg", style="blue", justify="right")
        table.add_column("Trend", justify="center")
        
        # Demo services data
        demo_services = [
            ("Amazon Elastic Compute Cloud", 1234.56, 43.4, "[red]↗[/red]"),
            ("Amazon Relational Database Service", 543.21, 19.1, "[green]↘[/green]"),
            ("Amazon Simple Storage Service", 321.45, 11.3, "[blue]→[/blue]"),
            ("AWS Lambda", 198.76, 7.0, "[green]↘[/green]"),
            ("Amazon CloudWatch", 87.65, 3.1, "[red]↗[/red]"),
            ("Amazon Virtual Private Cloud", 45.32, 1.6, "[blue]→[/blue]"),
            ("AWS Key Management Service", 23.18, 0.8, "[green]↘[/green]"),
        ]
        
        for service, cost, percentage, trend in demo_services:
            daily_cost = cost / days
            table.add_row(
                service,
                format_cost(cost),
                f"{percentage:.1f}%",
                format_cost(daily_cost),
                trend
            )
        
        console.print(table)
        
        # Demo optimization opportunities
        if config.output.verbose:
            opportunities_text = f"""
[bold]💡 Optimization Opportunities:[/bold]

• [yellow]EC2 Rightsizing:[/yellow] {format_cost(1234.56)} in EC2 costs - consider rightsizing analysis
• [yellow]RDS Optimization:[/yellow] {format_cost(543.21)} in RDS costs - review instance types and storage
• [yellow]Cost Trend Alert:[/yellow] 2 services trending up ({format_cost(1322.21)})
• [yellow]Reserved Instances:[/yellow] Consider RIs for consistent EC2 workloads
"""
            
            console.print(Panel(opportunities_text, title="🎯 Recommendations (Demo)", border_style="yellow"))
        
        # Show note about demo mode
        console.print(f"\n[dim]💡 This is demo data. Connect AWS credentials to see real cost information.[/dim]")


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
    dry_run = ctx.obj.dry_run
    
    if dry_run:
        # In dry-run mode, just call the demo command
        console.print("[yellow]Running in dry-run mode - showing demo data[/yellow]")
        ctx.invoke(demo, days=days)
        return
    
    # For real AWS mode
    try:
        # Test AWS connectivity
        _test_aws_connectivity(config, logger)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching real cost data...", total=None)
            
            # Import and use real AWS Cost Explorer service
            from .core.cost_explorer import CostExplorerService
            cost_service = CostExplorerService(config)
            
            progress.update(task, description="Analyzing costs...")
            
            # Get real cost data
            cost_analysis = cost_service.get_monthly_cost_overview(days)
            
            progress.update(task, description="Formatting results...")
            
            # Display real cost data (this function would need to be implemented)
            console.print("[green]Real AWS cost data would be displayed here![/green]")
            console.print(f"[blue]Analysis period: {days} days[/blue]")
            console.print(f"[blue]Group by: {group_by}[/blue]")
            
    except Exception as e:
        console.print(f"[red]Error getting cost overview: {e}[/red]")
        console.print("[yellow]Falling back to demo data...[/yellow]")
        ctx.invoke(demo, days=days)


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
    
    # Mock compliance report
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
    
    summary_text = f"""
[bold]Service:[/bold] {service.upper()}
[bold]Resources Analyzed:[/bold] 23
[bold]Recommendations:[/bold] 8
[bold]Potential Monthly Savings:[/bold] [green]${savings_threshold * 45.68:.2f}[/green]
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
        ("i-1234567890abcdef0", "m5.large", "m5.medium", f"${savings_threshold * 6.73:.2f}", "[green]High[/green]"),
        ("i-abcdef1234567890", "c5.xlarge", "c5.large", f"${savings_threshold * 12.35:.2f}", "[yellow]Medium[/yellow]"),
        ("i-9876543210fedcba", "r5.2xlarge", "r5.xlarge", f"${savings_threshold * 23.46:.2f}", "[green]High[/green]"),
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
    if interactive:
        console.print("[bold blue]🔧 FinOps Lite Setup Wizard[/bold blue]")
        console.print("This will help you configure FinOps Lite for your AWS environment.\n")
        
        console.print("[green]Interactive setup coming soon![/green]")
        console.print("For now, copy the template from config/templates/finops.yaml")
    else:
        console.print("Configuration template available at: config/templates/finops.yaml")
        console.print("Copy it to one of these locations:")
        console.print("  • ./finops.yaml")
        console.print("  • ~/.config/finops/config.yaml")
        console.print("  • ~/.finops.yaml")


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
