"""
Custom exceptions and error handling for FinOps Lite.
Enhanced with AWS-specific errors and retry logic.
"""

import time
from functools import wraps
from typing import Any, Callable, Optional

import click
from rich.console import Console
from rich.panel import Panel

try:
    from botocore.exceptions import (
        BotoCoreError,
        ClientError,
        ConnectTimeoutError,
        EndpointConnectionError,
        NoCredentialsError,
        PartialCredentialsError,
        ReadTimeoutError,
    )
except Exception:  # pragma: no cover - botocore should be present in runtime deps

    class BotoCoreError(Exception):
        pass

    class ClientError(Exception):
        pass

    class ConnectTimeoutError(Exception):
        pass

    class EndpointConnectionError(Exception):
        pass

    class NoCredentialsError(Exception):
        pass

    class PartialCredentialsError(Exception):
        pass

    class ReadTimeoutError(Exception):
        pass


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


class AWSServiceError(FinOpsError):
    """Generic AWS service/runtime error."""

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

    elif isinstance(error, AWSServiceError):
        _handle_aws_service_error(error)

    elif isinstance(error, ValidationError):
        _handle_validation_error(error)

    elif isinstance(error, ConfigurationError):
        _handle_configuration_error(error)

    else:
        _handle_generic_error(error, verbose)


def _handle_credentials_error(error: AWSCredentialsError):
    """Handle AWS credentials errors with concise, actionable guidance."""
    details = str(error).strip()
    error_panel = f"""[red]❌ AWS authentication failed[/red]

[yellow]What failed:[/yellow] FinOps Lite could not authenticate with AWS.
[yellow]Details:[/yellow] {details}

[yellow]Next:[/yellow]
  [bold]1.[/bold] Run [bold]aws configure[/bold] (or set AWS_PROFILE)
  [bold]2.[/bold] Verify the profile/region passed to FinOps Lite
  [bold]3.[/bold] Retry the command"""

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

    console.print(
        Panel(error_panel, title="📊 Cost Explorer Setup", border_style="red")
    )


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

    console.print(
        Panel(error_panel, title="⏳ Cost Explorer Warming Up", border_style="yellow")
    )


def _handle_rate_limit_error(error: APIRateLimitError):
    """Handle AWS API rate limit errors."""
    details = str(error).strip()
    error_panel = f"""[red]❌ AWS API rate limit reached[/red]

[yellow]What failed:[/yellow] AWS throttled one or more API calls.
[yellow]Details:[/yellow] {details}

[yellow]Next:[/yellow]
  [bold]1.[/bold] Wait briefly and retry
  [bold]2.[/bold] Reduce request frequency or use smaller windows
  [bold]3.[/bold] Use cache-enabled runs where possible"""

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
    details = str(error).strip()
    error_panel = f"""[red]❌ Access denied calling AWS APIs[/red]

[yellow]What failed:[/yellow] The current identity does not have required permissions.
[yellow]Details:[/yellow] {details}

[yellow]Next:[/yellow]
  [bold]1.[/bold] Ensure access to [bold]ce:GetCostAndUsage[/bold] and [bold]sts:GetCallerIdentity[/bold]
  [bold]2.[/bold] Use the correct IAM role/profile
  [bold]3.[/bold] Retry the command"""

    console.print(Panel(error_panel, title="🔐 Permissions", border_style="red"))


def _handle_aws_service_error(error: AWSServiceError):
    """Handle generic AWS service/runtime errors."""
    details = str(error).strip()
    error_panel = f"""[red]❌ AWS service error[/red]

[yellow]What failed:[/yellow] AWS returned an unexpected service/runtime error.
[yellow]Details:[/yellow] {details}

[yellow]Next:[/yellow]
  [bold]1.[/bold] Retry shortly (some errors are transient)
  [bold]2.[/bold] If persistent, verify region/service health and permissions
  [bold]3.[/bold] Re-run with [bold]--verbose[/bold] for extra context"""

    console.print(Panel(error_panel, title="☁️ AWS Service Error", border_style="red"))


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


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple = (Exception,),
):
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exceptions: Tuple of exceptions to catch and retry
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    # Don't retry on the last attempt
                    if attempt == max_retries:
                        break

                    # Don't retry on certain errors
                    if isinstance(
                        e,
                        (
                            AWSCredentialsError,
                            CostExplorerNotEnabledError,
                            AWSPermissionError,
                            ValidationError,
                            ConfigurationError,
                        ),
                    ):
                        break

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2**attempt), max_delay)

                    if isinstance(e, APIRateLimitError):
                        console.print(
                            f"[yellow]Rate limited, retrying in {delay:.1f}s... (attempt {attempt + 1}/{max_retries})[/yellow]"
                        )
                    elif isinstance(e, NetworkTimeoutError):
                        console.print(
                            f"[yellow]Network timeout, retrying in {delay:.1f}s... (attempt {attempt + 1}/{max_retries})[/yellow]"
                        )
                    else:
                        console.print(
                            f"[yellow]Temporary error, retrying in {delay:.1f}s... (attempt {attempt + 1}/{max_retries})[/yellow]"
                        )

                    time.sleep(delay)

            # All retries exhausted, raise the last exception
            raise last_exception

        return wrapper

    return decorator


def aws_error_mapper(func: Callable) -> Callable:
    """
    Decorator to map AWS-specific exceptions to our custom exceptions.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Already mapped
            if isinstance(e, FinOpsError):
                raise

            # Credentials
            if isinstance(e, (NoCredentialsError, PartialCredentialsError)):
                raise AWSCredentialsError(
                    "AWS credentials are missing or incomplete. "
                    "Configure credentials with aws configure or use AWS_PROFILE."
                )

            # Network/runtime connectivity
            if isinstance(
                e,
                (
                    ConnectTimeoutError,
                    EndpointConnectionError,
                    ReadTimeoutError,
                ),
            ):
                raise NetworkTimeoutError(f"AWS network error: {e}")

            # Structured AWS API errors
            if isinstance(e, ClientError):
                error = e.response.get("Error", {})
                code = error.get("Code", "Unknown")
                message = error.get("Message", str(e))
                detail = f"{code}: {message}"
                code_l = code.lower()
                msg_l = message.lower()

                credential_codes = {
                    "unrecognizedclientexception",
                    "invalidclienttokenid",
                    "signaturedoesnotmatch",
                    "authfailure",
                    "expiredtoken",
                    "expiredtokenexception",
                }
                permission_codes = {
                    "accessdenied",
                    "accessdeniedexception",
                    "unauthorizedoperation",
                    "notauthorizedexception",
                    "operationnotpermittedexception",
                }
                throttling_codes = {
                    "throttling",
                    "throttlingexception",
                    "requestlimitexceeded",
                    "toomanyrequestsexception",
                    "limitexceededexception",
                    "priorrequestnotcomplete",
                }

                if code_l in credential_codes or "security token" in msg_l:
                    raise AWSCredentialsError(
                        f"AWS credentials are missing or invalid ({detail})"
                    )

                if (
                    code_l in permission_codes
                    or "not authorized" in msg_l
                    or "access denied" in msg_l
                ):
                    raise AWSPermissionError(f"AWS access denied ({detail})")

                if code_l in throttling_codes or "rate exceeded" in msg_l:
                    raise APIRateLimitError(f"AWS throttling/rate limit ({detail})")

                if "cost explorer" in msg_l:
                    if "data is not available" in msg_l or "warming up" in msg_l:
                        raise CostExplorerWarmingUpError(
                            f"Cost Explorer data is still warming up ({detail})"
                        )
                    if "not enabled" in msg_l:
                        raise CostExplorerNotEnabledError(
                            f"Cost Explorer not enabled in this account ({detail})"
                        )
                    raise CostExplorerError(f"Cost Explorer error ({detail})")

                raise AWSServiceError(f"AWS service error ({detail})")

            # Generic botocore runtime errors
            if isinstance(e, BotoCoreError):
                err_l = str(e).lower()
                if "timeout" in err_l or "connection" in err_l:
                    raise NetworkTimeoutError(f"AWS network error: {e}")
                raise AWSServiceError(f"AWS SDK runtime error: {e}")

            # Fallback string-based mapping
            error_message = str(e).lower()
            if "credentials" in error_message:
                raise AWSCredentialsError(f"AWS credentials error: {e}")
            if "throttling" in error_message or "rate limit" in error_message:
                raise APIRateLimitError(f"AWS throttling/rate limit: {e}")
            if "permission" in error_message or "forbidden" in error_message:
                raise AWSPermissionError(f"AWS permission error: {e}")
            if "timeout" in error_message or "connection" in error_message:
                raise NetworkTimeoutError(f"AWS network error: {e}")

            # Re-raise as-is if we can't map it
            raise

    return wrapper


def validate_days(days: int) -> int:
    """Validate days parameter with enhanced error message."""
    if not isinstance(days, int):
        raise ValidationError("Days must be an integer")

    if days < 1:
        raise ValidationError("Days must be at least 1")

    if days > 365:
        raise ValidationError(
            "Days cannot exceed 365 (use multiple queries for longer periods)"
        )

    # Warn about Cost Explorer API costs for large ranges
    if days > 90:
        console.print(
            f"[yellow]⚠️  Analyzing {days} days will make multiple API calls (~$0.01 each)[/yellow]"
        )

    return days


def validate_threshold(threshold: float) -> float:
    """Validate threshold parameter with enhanced error message."""
    if not isinstance(threshold, (int, float)):
        raise ValidationError("Threshold must be a number")

    if threshold < 0:
        raise ValidationError("Threshold must be positive")

    if threshold > 10000:
        raise ValidationError(
            "Threshold seems unusually high (>$10,000), please verify"
        )

    return float(threshold)


def validate_aws_profile(profile: Optional[str]) -> Optional[str]:
    """Validate AWS profile exists."""
    if not profile:
        return None

    try:
        import boto3

        session = boto3.Session(profile_name=profile)
        # Test if profile works
        session.get_credentials()
        return profile
    except Exception as e:
        raise ValidationError(f"AWS profile '{profile}' not found or invalid: {e}")


def validate_aws_region(region: Optional[str]) -> Optional[str]:
    """Validate AWS region is valid."""
    if not region:
        return None

    # Common AWS regions (not exhaustive, but covers most cases)
    valid_regions = {
        "us-east-1",
        "us-east-2",
        "us-west-1",
        "us-west-2",
        "eu-west-1",
        "eu-west-2",
        "eu-west-3",
        "eu-central-1",
        "ap-southeast-1",
        "ap-southeast-2",
        "ap-northeast-1",
        "ap-northeast-2",
        "ap-south-1",
        "ca-central-1",
        "sa-east-1",
        "af-south-1",
        "me-south-1",
    }

    if region not in valid_regions:
        console.print(
            f"[yellow]⚠️  Region '{region}' not in common regions list[/yellow]"
        )
        console.print("[dim]This might be valid but uncommon. Proceeding...[/dim]")

    return region
