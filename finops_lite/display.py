from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def show_cost_summary(current_cost, last_month_cost, period="Month-to-Date"):
    """Show cost summary with nice formatting"""
    
    # Calculate if costs went up or down
    if last_month_cost > 0:
        change = ((current_cost - last_month_cost) / last_month_cost) * 100
        if change > 0:
            trend = f"📈 +{change:.1f}% vs last month"
            trend_color = "red"
        else:
            trend = f"📉 {change:.1f}% vs last month" 
            trend_color = "green"
    else:
        trend = "📊 No comparison data"
        trend_color = "yellow"

    # Create a nice box with the info
    summary = f"""
💰 {period}: [bold green]${current_cost:,.2f}[/bold green]
📊 Last Month: ${last_month_cost:,.2f}
[{trend_color}]{trend}[/{trend_color}]
"""
    
    panel = Panel(
        summary,
        title="🏦 AWS Cost Summary", 
        border_style="blue"
    )
    console.print(panel)

def show_services_table(services_data, days=30):
    """Show services in a nice table"""
    
    table = Table(
        title=f"💸 Top Services - Last {days} Days",
        show_header=True,
        header_style="bold magenta"
    )
    
    table.add_column("Service", style="cyan")
    table.add_column("Cost", justify="right", style="green")
    table.add_column("% of Total", justify="right", style="yellow")
    
    # Calculate total cost
    total = sum(float(service.get('cost', 0)) for service in services_data)
    
    # Add each service row
    for service in services_data[:10]:  # Show top 10
        cost = float(service.get('cost', 0))
        percentage = (cost / total * 100) if total > 0 else 0
        
        table.add_row(
            service.get('service', 'Unknown'),
            f"${cost:,.2f}",
            f"{percentage:.1f}%"
        )
    
    console.print(table)
    
    # Show total
    total_panel = Panel(
        f"[bold green]Total: ${total:,.2f}[/bold green]",
        border_style="green"
    )
    console.print(total_panel)

def show_loading(message="Loading..."):
    """Show a loading spinner"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    )

def show_error(message):
    """Show error message in red box"""
    panel = Panel(
        f"❌ {message}",
        title="Error",
        border_style="red"
    )
    console.print(panel)

def show_success(message):
    """Show success message in green box"""
    panel = Panel(
        f"✅ {message}",
        title="Success", 
        border_style="green"
    )
    console.print(panel)
