"""
Custom exceptions and error handling for FinOps Lite.
"""

import click
from rich.console import Console

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

class ConfigurationError(FinOpsError):
    """Configuration file or settings error."""
    pass

class ValidationError(FinOpsError):
    """Input validation error."""
    pass

def handle_error(error: Exception, verbose: bool = False):
    """Handle errors with user-friendly messages."""
    
    if isinstance(error, AWSCredentialsError):
        console.print("[red]❌ AWS Credentials Error[/red]")
        console.print("Your AWS credentials are not configured properly.")
        console.print("\n[yellow]💡 Quick fixes:[/yellow]")
        console.print("  • Run: aws configure")
        console.print("  • Set AWS_PROFILE environment variable")
        console.print("  • Use --profile option")
        
    elif isinstance(error, ValidationError):
        console.print(f"[red]❌ Validation Error:[/red] {error}")
        console.print("[yellow]💡 Check your input parameters and try again[/yellow]")
        
    else:
        console.print(f"[red]❌ Error:[/red] {error}")
        if verbose:
            console.print_exception()

def validate_days(days: int) -> int:
    """Validate days parameter."""
    if days < 1 or days > 365:
        raise ValidationError("Days must be between 1 and 365")
    return days

def validate_threshold(threshold: float) -> float:
    """Validate threshold parameter."""
    if threshold < 0:
        raise ValidationError("Threshold must be positive")
    return threshold