"""
Unit tests for summary payload construction.
"""

from datetime import date

import pytest

from finops_lite.summary import build_cost_summary


def _make_day(start_date, total_amount, groups):
    return {
        "TimePeriod": {
            "Start": start_date,
            "End": "unused",
        },
        "Total": {
            "BlendedCost": {
                "Amount": str(total_amount),
                "Unit": "USD",
            }
        },
        "Groups": [
            {
                "Keys": [group_name],
                "Metrics": {
                    "BlendedCost": {
                        "Amount": str(amount),
                        "Unit": "USD",
                    }
                },
            }
            for group_name, amount in groups
        ],
    }


def test_build_cost_summary_structure_and_math():
    current = {
        "ResultsByTime": [
            _make_day("2026-01-01", 150, [("AmazonEC2", 100), ("AmazonS3", 50)]),
            _make_day("2026-01-02", 100, [("AmazonEC2", 60), ("AmazonS3", 40)]),
            _make_day("2026-01-03", 50, [("AmazonEC2", 50), ("AmazonS3", 0)]),
        ]
    }
    previous = {
        "ResultsByTime": [
            _make_day("2025-12-29", 100, [("AmazonEC2", 70), ("AmazonS3", 30)]),
            _make_day("2025-12-30", 50, [("AmazonEC2", 30), ("AmazonS3", 20)]),
            _make_day("2025-12-31", 50, [("AmazonEC2", 20), ("AmazonS3", 30)]),
        ]
    }

    summary = build_cost_summary(
        current,
        previous,
        group_by="SERVICE",
        window_start=date(2026, 1, 1),
        window_end=date(2026, 1, 3),
    )

    expected_keys = {
        "schema_version",
        "currency",
        "group_by",
        "window",
        "total_cost",
        "previous_total_cost",
        "change_pct",
        "top_groups",
        "daily_trend",
        "daily_groups",
    }
    assert expected_keys.issubset(summary.keys())
    assert summary["schema_version"] == "1.0"
    assert summary["currency"] == "USD"
    assert summary["group_by"] == "SERVICE"
    assert summary["window"]["start"] == "2026-01-01"
    assert summary["window"]["end"] == "2026-01-03"

    assert summary["total_cost"] == 300.0
    assert summary["previous_total_cost"] == 200.0
    assert summary["change_pct"] == 50.0

    assert summary["top_groups"][0]["group"] == "AmazonEC2"
    pct_sum = sum(group["pct_of_total"] for group in summary["top_groups"])
    assert abs(pct_sum - 100.0) <= 0.2

    assert [item["date"] for item in summary["daily_trend"]] == [
        "2026-01-01",
        "2026-01-02",
        "2026-01-03",
    ]
    assert (
        sum(
            row["cost"]
            for row in summary["daily_groups"]
            if row["date"] == "2026-01-01"
        )
        == 150.0
    )


def test_build_cost_summary_rejects_missing_day_instead_of_emitting_zero():
    current = {"ResultsByTime": [_make_day("2026-01-01", 10, [("AmazonEC2", 10)])]}
    with pytest.raises(ValueError, match="not observed zero"):
        build_cost_summary(
            current,
            {"ResultsByTime": []},
            group_by="SERVICE",
            window_start=date(2026, 1, 1),
            window_end=date(2026, 1, 2),
        )


def test_build_cost_summary_rejects_non_reconciling_daily_groups():
    current = {"ResultsByTime": [_make_day("2026-01-01", 10, [("AmazonEC2", 9)])]}
    with pytest.raises(ValueError, match="Daily service breakdown does not reconcile"):
        build_cost_summary(
            current,
            {"ResultsByTime": []},
            group_by="SERVICE",
            window_start=date(2026, 1, 1),
            window_end=date(2026, 1, 1),
        )


def test_build_cost_summary_change_pct_null_when_previous_zero():
    current = {
        "ResultsByTime": [
            _make_day("2026-01-01", 10, [("AmazonEC2", 10)]),
        ]
    }
    previous = {
        "ResultsByTime": [
            _make_day("2025-12-31", 0, [("AmazonEC2", 0)]),
        ]
    }

    summary = build_cost_summary(
        current,
        previous,
        group_by="SERVICE",
        window_start=date(2026, 1, 1),
        window_end=date(2026, 1, 1),
    )

    assert summary["previous_total_cost"] == 0.0
    assert summary["change_pct"] is None


def test_build_cost_summary_rejects_malformed_money_instead_of_zero():
    current = {
        "ResultsByTime": [
            _make_day("2026-01-01", "not-a-number", [("AmazonEC2", 10)]),
        ]
    }
    with pytest.raises(ValueError, match="Invalid numeric value"):
        build_cost_summary(
            current,
            {"ResultsByTime": []},
            group_by="SERVICE",
            window_start=date(2026, 1, 1),
            window_end=date(2026, 1, 1),
        )


def test_build_cost_summary_can_include_all_groups_for_reconciliation():
    groups = [(f"Service{i}", i + 1) for i in range(12)]
    total = sum(amount for _, amount in groups)
    summary = build_cost_summary(
        {"ResultsByTime": [_make_day("2026-01-01", total, groups)]},
        {"ResultsByTime": []},
        group_by="SERVICE",
        window_start=date(2026, 1, 1),
        window_end=date(2026, 1, 1),
        top_n=None,
    )
    assert len(summary["top_groups"]) == 12
    assert sum(item["cost"] for item in summary["top_groups"]) == summary["total_cost"]
