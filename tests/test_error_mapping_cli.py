"""
CLI error mapping tests for predictable, script-friendly failures.

These tests stub AWS/runtime failures and assert:
- clear user-facing error messaging
- non-zero exit codes
"""

import os

from botocore.exceptions import ClientError, NoCredentialsError
from click.testing import CliRunner

from finops_lite.cli import cli


def _run_overview_cli(args, env=None):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["--no-cache", "cost", "overview", "--days", "7", *args],
            env=env or {"HOME": os.getcwd()},
        )
    return result


def _patch_connectivity_ok(monkeypatch):
    import finops_lite.cli as cli_module

    monkeypatch.setattr(
        cli_module,
        "_test_aws_connectivity",
        lambda *args, **kwargs: {
            "account_id": "123456789012",
            "user_arn": "arn:aws:iam::123456789012:user/test",
            "region": "us-east-1",
            "cost_explorer_status": "available",
        },
    )


def _patch_cost_service_exception(monkeypatch, exc):
    import finops_lite.core.cost_explorer as cost_explorer_module

    class FakeCostExplorerService:
        def __init__(self, config):
            self.config = config

        def get_monthly_cost_overview(self, days):
            raise exc

    monkeypatch.setattr(
        cost_explorer_module, "CostExplorerService", FakeCostExplorerService
    )


def test_missing_aws_credentials_exits_nonzero_with_clear_message(monkeypatch):
    import finops_lite.utils.config as config_module

    def _raise_no_credentials(self):
        raise NoCredentialsError()

    monkeypatch.setattr(
        config_module.FinOpsConfig, "get_boto3_session", _raise_no_credentials
    )

    result = _run_overview_cli([])

    assert result.exit_code == 1
    assert "AWS authentication failed" in result.output
    assert "aws configure" in result.output


def test_invalid_aws_credentials_exits_nonzero_with_clear_message(monkeypatch):
    _patch_connectivity_ok(monkeypatch)
    _patch_cost_service_exception(
        monkeypatch,
        ClientError(
            {
                "Error": {
                    "Code": "InvalidClientTokenId",
                    "Message": "The security token included in the request is invalid",
                }
            },
            "GetCostAndUsage",
        ),
    )

    result = _run_overview_cli([])

    assert result.exit_code == 1
    assert "AWS authentication failed" in result.output
    assert "InvalidClientTokenId" in result.output


def test_access_denied_exits_nonzero_with_clear_message(monkeypatch):
    _patch_connectivity_ok(monkeypatch)
    _patch_cost_service_exception(
        monkeypatch,
        ClientError(
            {
                "Error": {
                    "Code": "AccessDeniedException",
                    "Message": "User is not authorized to perform ce:GetCostAndUsage",
                }
            },
            "GetCostAndUsage",
        ),
    )

    result = _run_overview_cli([])

    assert result.exit_code == 1
    assert "Access denied calling AWS APIs" in result.output
    assert "AccessDeniedException" in result.output
    assert "ce:GetCostAndUsage" in result.output


def test_throttling_exits_nonzero_with_clear_message(monkeypatch):
    import finops_lite.utils.errors as errors_module

    _patch_connectivity_ok(monkeypatch)
    _patch_cost_service_exception(
        monkeypatch,
        ClientError(
            {
                "Error": {
                    "Code": "ThrottlingException",
                    "Message": "Rate exceeded",
                }
            },
            "GetCostAndUsage",
        ),
    )

    # Avoid retry backoff delays in tests.
    monkeypatch.setattr(errors_module.time, "sleep", lambda _seconds: None)

    result = _run_overview_cli([])

    assert result.exit_code == 1
    assert "AWS API rate limit reached" in result.output
    assert "ThrottlingException" in result.output


def test_generic_aws_service_error_exits_nonzero_with_clear_message(monkeypatch):
    _patch_connectivity_ok(monkeypatch)
    _patch_cost_service_exception(
        monkeypatch,
        ClientError(
            {
                "Error": {
                    "Code": "InternalError",
                    "Message": "Internal service failure",
                }
            },
            "GetCostAndUsage",
        ),
    )

    result = _run_overview_cli([])

    assert result.exit_code == 1
    assert "AWS service error" in result.output
    assert "InternalError" in result.output
