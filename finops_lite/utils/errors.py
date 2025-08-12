"""
Custom exceptions and error handling for FinOps Lite.
Enhanced with AWS-specific errors and retry logic.
"""

import time
import click
from typing import Optional, Callable, Any
from functools import wraps
from rich.console import Console
from rich.panel import Panel

console = Console()

class FinOpsError(Exception):
    """Base exception for FinOps Lite."""
    pass

class AWSCredentialsError(FinOpsError):
    """AWS credentials not configured."""
    pass

class AWSPermissionError(FinOpsError):
    """Insufficient AWS permissions."""
    pass

class CostExplorerError(FinOpsError):
    """Cost Explorer specific errors."""
    pass

class CostExplorerNotEnabledError(CostExplorerError):
    """Cost Explorer not enabled in account."""
    pass

class CostExplorerWarmingUpError(CostExplorerError):
    """Cost Explorer still warming up (first 24-48 hours)."""
    pass

class APIRateLimitError(FinOpsError):
    """AWS API rate limit exceeded."""
    pass

class NetworkTimeoutError(FinOpsError):
    """Network timeout or connectivity issue."""
    pass

class ConfigurationError(FinOpsError):
    """Configuration file or settings error."""
    pass

class ValidationError(FinOpsError):
    """Input validation error."""
    pass

def handle_error(error: Exception, verbose: bool = False):
    """Handle errors with user-friendly messages and actionable suggestions."""
    
    if isinstance(error, AWSCredentialsError):
        _handle_credentials_error(error)
        
    elif isinstance(error, CostExplorerNotEnabledError):
        _handle_cost_explorer_not_enabled(error)
        
    elif isinstance(error, CostExplorerWarmingUpError):
        _handle_cost_explorer_warming_up(error)
        
    elif isinstance(error, APIRateLimitError):
        _handle_rate_limit_error(error)
        
    elif isinstance(error, NetworkTimeoutError):
        _handle_network_timeout(error)
        
    elif isinstance(error, AWSPermissionError):
        _handle_permission_error(error)
        
    elif isinstance(error, ValidationError):
        _handle_validation_error(error)
        
    elif isinstance(error, ConfigurationError):
        _handle_configuration_error(error)
        
    else:
        _handle_generic_error(error, verbose)

def _handle_credentials_error(error: AWSCredentialsError):
    """Handle AWS credentials errors with detailed guidance."""
    error_panel = """[red]❌ AWS Credentials Not Found[/red]

[yellow]💡 Quick Fixes:[/yellow]
  [bold]1. Configure AWS CLI:[/bold]
     aws configure
     
  [bold]2. Use named profile:[/bold]
     export AWS_PROFILE=your-profile-name
     # or use: finops --profile your-profile-name
     
  [bold]3. Use environment variables:[/bold]
     export AWS_ACCESS_KEY_ID=your-key
     export AWS_SECRET_ACCESS_KEY=your-secret
     
  [bold]4. For FinOps, create a read-only IAM user:[/bold]
     • Attach policy: ReadOnlyAccess
     • For Cost Explorer: ce:GetCostAndUsage, ce:GetRightsizingRecommendation
     
[dim]💰 Cost Note: Cost Explorer API calls cost ~$0.01 each[/dim]"""
    
    console.print(Panel(error_panel, title="🔑 AWS Credentials", border_style="red"))

def _handle_cost_explorer_not_enabled(error: CostExplorerNotEnabledError):
    """Handle Cost Explorer not enabled error."""
    error_panel = """[red]❌ AWS Cost Explorer Not Enabled[/red]

[yellow]💡 Enable Cost Explorer:[/yellow]
  [bold]1. Log into AWS Console[/bold]
  [bold]2. Go to AWS Cost Management → Cost Explorer[/bold]
  [bold]3. Click "Enable Cost Explorer"[/bold]
  [bold]4. Wait 24-48 hours for data to populate[/bold]
  
[yellow]📊 What you get:[/yellow]
  • Historical cost data
  • Service-level cost breakdowns
  • Rightsizing recommendations
  
[dim]💰 Cost: ~$0.01 per API call, Free tier available[/dim]"""
    
    console.print(Panel(error_panel, title="📊 Cost Explorer Setup", border_style="red"))

def _handle_cost_explorer_warming_up(error: CostExplorerWarmingUpError):
    """Handle Cost Explorer warming up error."""
    error_panel = """[yellow]⏳ Cost Explorer Still Warming Up[/yellow]

[green]✅ Good news: Cost Explorer is enabled![/green]

[yellow]⏰ Please wait:[/yellow]
  • [bold]First-time setup:[/bold] Up to 24-48 hours
  • [bold]New account:[/bold] Data appears gradually
  • [bold]Current status:[/bold] Still processing historical data
  
[yellow]💡 What to do:[/yellow]
  [bold]1. Try again in a few hours[/bold]
  [bold]2. Use --last-month flag for older data[/bold]
  [bold]3. Check AWS Console → Cost Explorer[/bold]
  
[dim]This is normal for new accounts or recently enabled Cost Explorer[/dim]"""
    
    console.print(Panel(error_panel, title="⏳ Cost Explorer Warming Up", border_style="yellow"))

def _handle_rate_limit_error(error: APIRateLimitError):
    """Handle AWS API rate limit errors."""
    error_panel = """[red]❌ AWS API Rate Limit Exceeded[/red]

[yellow]⏱️  Too many requests in short time[/yellow]

[yellow]💡 Solutions:[/yellow]
  [bold]1. Wait and retry:[/bold] AWS limits reset quickly
  [bold]2. Use --days with smaller values[/bold]
  [bold]3. Space out your requests[/bold]
  
[yellow]🚦 Rate Limits:[/yellow]
  • Cost Explorer: ~10 requests/second
  • Other AWS APIs: Varies by service
  
[dim]💰 Remember: Each Cost Explorer call costs ~$0.01[/dim]"""
    
    console.print(Panel(error_panel, title="🚦 Rate Limit", border_style="red"))

def _handle_network_timeout(error: NetworkTimeoutError):
    """Handle network timeout errors."""
    error_panel = """[red]❌ Network Timeout[/red]

[yellow]🌐 Connection to AWS timed out[/yellow]

[yellow]💡 Try these:[/yellow]
  [bold]1. Check internet connection[/bold]
  [bold]2. Verify AWS region is accessible[/bold]
  [bold]3. Try different AWS region with --region[/bold]
  [bold]4. Check if VPN/proxy is interfering[/bold]
  
[yellow]🔍 Debug steps:[/yellow]
  [bold]1. Test basic connectivity:[/bold]
     aws sts get-caller-identity
  [bold]2. Try different region:[/bold]
     finops --region us-east-1 cost overview"""
    
    console.print(Panel(error_panel, title="🌐 Network Issue", border_style="red"))

def _handle_permission_error(error: AWSPermissionError):
    """Handle AWS permission errors."""
    error_panel = """[red]❌ Insufficient AWS Permissions[/red]

[yellow]🔐 Your AWS user lacks required permissions[/yellow]

[yellow]💡 Required permissions for FinOps:[/yellow]
  [bold]Cost Explorer:[/bold]
  • ce:GetCostAndUsage
  • ce:GetRightsizingRecommendation
  • ce:GetReservationCoverage
  
  [bold]Resource Analysis:[/bold]
  • ec2:DescribeInstances
  • rds:DescribeDBInstances
  • s3:ListBucket (for bucket analysis)
  
[yellow]🛠️  Quick fix:[/yellow]
  [bold]Attach AWS managed policy:[/bold] ReadOnlyAccess + CostExplorerAccess"""
    
    console.print(Panel(error_panel, title="🔐 Permissions", border_style="red"))

def _handle_validation_error(error: ValidationError):
    """Handle validation errors."""
    console.print(f"[red]❌ Invalid Input:[/red] {error}")
    console.print("[yellow]💡 Check your parameters and try again[/yellow]")

def _handle_configuration_error(error: ConfigurationError):
    """Handle configuration errors."""
    console.print(f"[red]❌ Configuration Error:[/red] {error}")
    console.print("[yellow]💡 Check your config file or run: finops setup[/yellow]")

def _handle_generic_error(error: Exception, verbose: bool):
    """Handle unexpected errors."""
    console.print(f"[red]❌ Unexpected Error:[/red] {error}")
    if verbose:
        console.print_exception()
    else:
        console.print("[dim]Use --verbose for detailed error information[/dim]")

def validate_days(days: int) -> int:
    """Validate days parameter with enhanced error message."""
    if not isinstance(days, int):
        raise ValidationError("Days must be an integer")
    
    if days < 1:
        raise ValidationError("Days must be at least 1")
    
    if days > 365:
        raise ValidationError("Days cannot exceed 365 (use multiple queries for longer periods)")
    
    # Warn about Cost Explorer API costs for large ranges
    if days > 90:
        console.print(f"[yellow]⚠️  Analyzing {days} days will make multiple API calls (~$0.01 each)[/yellow]")
    
    return days

def validate_threshold(threshold: float) -> float:
    """Validate threshold parameter with enhanced error message."""
    if not isinstance(threshold, (int, float)):
        raise ValidationError("Threshold must be a number")
    
    if threshold < 0:
        raise ValidationError("Threshold must be positive")
    
    if threshold > 10000:
        raise ValidationError("Threshold seems unusually high (>$10,000), please verify")
    
    return float(threshold)
