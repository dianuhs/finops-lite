from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

import finops_lite.cli as cli_module
from finops_lite.ccac import CCACBuildError, build_ccac_result, illustrative_summary
from finops_lite.cli import cli


def test_ccac_demo_is_deterministic_and_reconciled():
    runner = CliRunner()
    first = runner.invoke(cli, ["--no-cache", "ccac", "--demo"])
    second = runner.invoke(cli, ["--no-cache", "ccac", "--demo"])
    assert first.exit_code == 0, first.output
    assert second.exit_code == 0, second.output
    assert first.output == second.output

    payload = json.loads(first.output)
    assert payload["contract"] == "ccac/1.0.0"
    assert payload["document_type"] == "tool_result"
    assert payload["producer"]["name"] == "finops-lite"
    assert payload["mode"] == "illustrative"
    assert payload["period"] == {
        "start": "2026-07-01",
        "end": "2026-07-22",
        "timezone": "UTC",
    }
    daily_metrics = [metric for metric in payload["metrics"] if "date" in metric["dimensions"] and "service" not in metric["dimensions"]]
    assert len(daily_metrics) == 21
    assert next(metric for metric in daily_metrics if metric["dimensions"]["date"] == "2026-07-21")["value"] == 175.0
    daily_service_metrics = [metric for metric in payload["metrics"] if "date" in metric["dimensions"] and "service" in metric["dimensions"]]
    assert len(daily_service_metrics) == 42
    assert payload["inputs"][0]["data_classification"] == "public_illustrative"
    assert payload["extensions"]["finops_lite"]["reconciliation"]["status"] == "passed"
    assert payload["extensions"]["finops_lite"]["reconciliation"]["difference"] == 0.0


def test_ccac_demo_writes_payload_only_to_file(tmp_path):
    target = tmp_path / "result.json"
    result = CliRunner().invoke(cli, ["--no-cache", "ccac", "--demo", "--output", str(target)])
    assert result.exit_code == 0, result.output
    assert result.output == ""
    assert json.loads(target.read_text())["document_type"] == "tool_result"


def test_ccac_real_mode_uses_complete_summary(monkeypatch):
    seen = {}

    def fake_run_summarize(*args, **kwargs):
        seen.update(kwargs)
        return illustrative_summary()

    monkeypatch.setattr(cli_module, "run_summarize", fake_run_summarize)
    result = CliRunner().invoke(
        cli,
        [
            "--no-cache",
            "ccac",
            "--start",
            "2026-07-01",
            "--end",
            "2026-07-03",
            "--run-id",
            "123e4567-e89b-12d3-a456-426614174001",
            "--generated-at",
            "2026-08-04T13:00:00Z",
        ],
    )
    assert result.exit_code == 0, result.output
    assert seen["top_n"] is None
    payload = json.loads(result.output)
    assert payload["mode"] == "real"
    assert payload["inputs"][0]["source_type"] == "aws_cost_explorer_api"
    assert payload["inputs"][0]["access"] == "external_read_only"


def test_ccac_rejects_non_reconciling_service_breakdown():
    summary = illustrative_summary()
    summary["top_groups"][0]["cost"] = 209.0
    with pytest.raises(CCACBuildError, match="Service breakdown does not reconcile"):
        build_ccac_result(
            summary,
            mode="illustrative",
            source_type="fixture",
            source_version="1.0",
        )


def test_ccac_rejects_non_reconciling_daily_trend():
    summary = illustrative_summary()
    summary["daily_trend"][0]["cost"] = 149.0
    with pytest.raises(CCACBuildError, match="Daily trend does not reconcile"):
        build_ccac_result(
            summary,
            mode="illustrative",
            source_type="fixture",
            source_version="1.0",
        )


def test_ccac_rejects_missing_or_duplicate_daily_dates():
    summary = illustrative_summary()
    summary["daily_trend"][2]["date"] = "2026-07-02"
    with pytest.raises(CCACBuildError, match="each source-window date exactly once"):
        build_ccac_result(
            summary,
            mode="illustrative",
            source_type="fixture",
            source_version="1.0",
        )


def test_ccac_demo_has_enough_history_for_default_watchdog_window():
    summary = illustrative_summary()
    assert len(summary["daily_trend"]) >= 15
    assert summary["daily_trend"][-1]["cost"] > max(row["cost"] for row in summary["daily_trend"][:-1])


def test_ccac_accepts_a_reconciled_zero_cost_period():
    summary = illustrative_summary()
    summary["total_cost"] = 0
    summary["previous_total_cost"] = 0
    summary["change_pct"] = None
    summary["top_groups"] = []
    summary["daily_groups"] = []
    for row in summary["daily_trend"]:
        row["cost"] = 0
    result = build_ccac_result(
        summary,
        mode="illustrative",
        source_type="fixture",
        source_version="1.0",
        run_id="123e4567-e89b-12d3-a456-426614174000",
        generated_at="2026-08-04T12:00:00Z",
    )
    total = next(metric for metric in result["metrics"] if metric["id"] == "metric.cloud.total")
    change_pct = next(metric for metric in result["metrics"] if metric["id"] == "metric.cloud.change-percentage")
    assert total["value"] == 0.0
    assert total["basis"] == "observed"
    assert change_pct["value"] is None
    assert change_pct["basis"] == "unknown"


@pytest.mark.parametrize("bad_value", [None, "", "not-a-number", "NaN", "Infinity", True])
def test_ccac_rejects_invalid_total_instead_of_coercing_to_zero(bad_value):
    summary = illustrative_summary()
    summary["total_cost"] = bad_value
    with pytest.raises(CCACBuildError):
        build_ccac_result(
            summary,
            mode="illustrative",
            source_type="fixture",
            source_version="1.0",
        )


def test_help_and_demo_do_not_create_home_cache(monkeypatch, tmp_path):
    unavailable_home = tmp_path / "does-not-exist"
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: unavailable_home))

    help_result = CliRunner().invoke(cli, ["--help"])
    demo_result = CliRunner().invoke(cli, ["ccac", "--demo"])

    assert help_result.exit_code == 0
    assert demo_result.exit_code == 0, demo_result.output
    assert not unavailable_home.exists()
