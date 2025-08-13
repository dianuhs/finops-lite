"""
Tests for FinOps Lite CLI functionality.
Updated to match enhanced error handling and new features.
"""

import pytest
from click.testing import CliRunner
from finops_lite.cli import cli
from finops_lite.utils.errors import validate_days, validate_threshold, ValidationError


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_version_command(self):
        """Test version command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert "FinOps Lite" in result.output

    def test_help_command(self):
        """Test help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "FinOps Lite" in result.output
        assert "cost" in result.output

    def test_cost_help(self):
        """Test cost subcommand help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["cost", "--help"])
        assert result.exit_code == 0
        assert "overview" in result.output


class TestCostOverview:
    """Test cost overview functionality."""

    def test_dry_run_cost_overview_table(self):
        """Test dry-run cost overview with table format."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--dry-run", "cost", "overview"])
        assert result.exit_code == 0
        assert "DEMO DATA" in result.output
        assert "Amazon EC2" in result.output

    def test_dry_run_cost_overview_json(self):
        """Test dry-run cost overview with JSON format."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--dry-run", "--output-format", "json", "cost", "overview"]
        )
        assert result.exit_code == 0
        assert "Generating JSON format" in result.output

    def test_dry_run_cost_overview_csv(self):
        """Test dry-run cost overview with CSV format."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--dry-run", "--output-format", "csv", "cost", "overview"]
        )
        assert result.exit_code == 0
        assert "Generating CSV format" in result.output

    def test_dry_run_cost_overview_yaml(self):
        """Test dry-run cost overview with YAML format."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--dry-run", "--output-format", "yaml", "cost", "overview"]
        )
        assert result.exit_code == 0
        assert "Generating YAML format" in result.output

    def test_dry_run_cost_overview_executive(self):
        """Test dry-run cost overview with executive format."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--dry-run", "--output-format", "executive", "cost", "overview"]
        )
        assert result.exit_code == 0
        assert "Generating EXECUTIVE format" in result.output


class TestCacheCommands:
    """Test cache management functionality."""

    def test_cache_stats(self):
        """Test cache stats command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["cache", "stats"])
        assert result.exit_code == 0
        assert "Cache Statistics" in result.output
        assert "Cache Entries" in result.output

    def test_cache_clear_with_confirm(self):
        """Test cache clear command with confirmation."""
        runner = CliRunner()
        result = runner.invoke(cli, ["cache", "clear", "--confirm"])
        assert result.exit_code == 0
        assert "Cache cleared successfully" in result.output

    def test_cache_help(self):
        """Test cache command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["cache", "--help"])
        assert result.exit_code == 0
        assert "Cache management commands" in result.output


class TestValidation:
    """Test validation functions."""

    def test_validate_days_valid(self):
        """Test valid days parameter."""
        assert validate_days(30) == 30
        assert validate_days(1) == 1
        assert validate_days(365) == 365

    def test_validate_days_invalid(self):
        """Test invalid days parameter."""
        with pytest.raises(ValidationError, match="Days must be at least 1"):
            validate_days(0)

        with pytest.raises(ValidationError, match="Days cannot exceed 365"):
            validate_days(400)

    def test_validate_threshold_valid(self):
        """Test valid threshold parameter."""
        assert validate_threshold(10.0) == 10.0
        assert validate_threshold(0) == 0.0
        assert validate_threshold(100) == 100.0

    def test_validate_threshold_invalid(self):
        """Test invalid threshold parameter."""
        with pytest.raises(ValidationError, match="Threshold must be positive"):
            validate_threshold(-1)


class TestOtherCommands:
    """Test other CLI commands."""

    def test_tags_compliance(self):
        """Test tags compliance command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tags", "compliance"])
        assert result.exit_code == 0
        assert "Tag Compliance Report" in result.output

    def test_optimize_rightsizing(self):
        """Test optimize rightsizing command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["optimize", "rightsizing"])
        assert result.exit_code == 0
        assert "Rightsizing Analysis" in result.output

    def test_setup_command(self):
        """Test setup command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["setup"])
        assert result.exit_code == 0
        assert "Configuration template" in result.output


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_days_parameter(self):
        """Test error handling for invalid days."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--dry-run", "cost", "overview", "--days", "500"])
        assert result.exit_code == 1
        assert "Days cannot exceed 365" in str(result.exception)

    def test_invalid_savings_threshold(self):
        """Test error handling for invalid savings threshold."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["optimize", "rightsizing", "--savings-threshold", "-10"]
        )
        assert result.exit_code == 1
        assert "Threshold must be positive" in str(result.exception)


class TestConfiguration:
    """Test configuration and options."""

    def test_global_output_format(self):
        """Test global output format option."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--dry-run", "--output-format", "json", "cost", "overview"]
        )
        assert result.exit_code == 0
        assert "JSON format" in result.output

    def test_different_days_parameter(self):
        """Test different days parameter values."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--dry-run", "cost", "overview", "--days", "7"])
        assert result.exit_code == 0
        assert "Last 7 days" in result.output

    def test_different_group_by(self):
        """Test different group-by options."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--dry-run", "cost", "overview", "--group-by", "ACCOUNT"]
        )
        assert result.exit_code == 0
        assert "DEMO DATA" in result.output

    def test_no_cache_option(self):
        """Test no-cache option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--no-cache", "cache", "stats"])
        assert result.exit_code == 0
        assert "Cache is disabled" in result.output

    def test_performance_option(self):
        """Test performance tracking option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--performance", "--dry-run", "cost", "overview"])
        assert result.exit_code == 0
        assert "DEMO DATA" in result.output


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_complete_cost_analysis_workflow(self):
        """Test complete cost analysis workflow."""
        runner = CliRunner()

        # Test cache stats (empty initially)
        result = runner.invoke(cli, ["cache", "stats"])
        assert result.exit_code == 0
        assert "Cache Statistics" in result.output

        # Test cost overview
        result = runner.invoke(cli, ["--dry-run", "cost", "overview"])
        assert result.exit_code == 0
        assert "DEMO DATA" in result.output

        # Test cache clear
        result = runner.invoke(cli, ["cache", "clear", "--confirm"])
        assert result.exit_code == 0

    def test_help_system_comprehensive(self):
        """Test comprehensive help system."""
        runner = CliRunner()

        # Main help
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "FinOps Lite" in result.output

        # Cost help
        result = runner.invoke(cli, ["cost", "--help"])
        assert result.exit_code == 0
        assert "overview" in result.output

        # Cache help
        result = runner.invoke(cli, ["cache", "--help"])
        assert result.exit_code == 0
        assert "Cache management" in result.output

        # Tags help
        result = runner.invoke(cli, ["tags", "--help"])
        assert result.exit_code == 0
        assert "compliance" in result.output

        # Optimize help
        result = runner.invoke(cli, ["optimize", "--help"])
        assert result.exit_code == 0
        assert "rightsizing" in result.output


class TestNewFeatures:
    """Test new caching and performance features."""

    def test_force_refresh_option(self):
        """Test force refresh option."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--dry-run", "cost", "overview", "--force-refresh"]
        )
        assert result.exit_code == 0
        assert "DEMO DATA" in result.output

    def test_export_functionality(self):
        """Test export functionality."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--dry-run", "cost", "overview", "--export", "test_report.json"]
        )
        assert result.exit_code == 0
        assert "exported" in result.output or "DEMO DATA" in result.output

    def test_verbose_mode_with_performance(self):
        """Test verbose mode with performance tracking."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--verbose", "--performance", "--dry-run", "cost", "overview"]
        )
        assert result.exit_code == 0
        assert "DEMO DATA" in result.output
