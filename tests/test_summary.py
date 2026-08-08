"""
Unit tests for summary payload construction.
"""

from datetime import date

import pytest

from finops_lite.summary import build_cost_summary


def _make_day(start_date, total_amount, groups, metric_name="BlendedCost"):
    return {
        "TimePeriod": {
            "Start": start_date,
            "End": "unused",
        },
        "Total": {
            metric_name: {
                "Amount": str(total_amount),
                "Unit": "USD",
            }
        },
        "Groups": [
            {
                "Keys": [group_name],
                "Metrics": {
                    metric_name: {
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


def test_build_cost_summary_uses_only_selected_net_unblended_metric():
    current = {
        "ResultsByTime": [
            _make_day("2026-01-01", 95, [("AmazonEC2", 95)], "NetUnblendedCost")
        ]
    }
    summary = build_cost_summary(
        current,
        {
            "ResultsByTime": [
                _make_day("2025-12-31", 90, [("AmazonEC2", 90)], "NetUnblendedCost")
            ]
        },
        group_by="SERVICE",
        window_start=date(2026, 1, 1),
        window_end=date(2026, 1, 1),
        metric_name="NetUnblendedCost",
    )
    assert summary["total_cost"] == 95.0
    assert summary["aws_cost_metric"] == "NetUnblendedCost"
    assert summary["comparison_window"] == {
        "start": "2025-12-31",
        "end": "2025-12-31",
    }


def test_build_cost_summary_never_falls_back_to_blended_cost():
    current = {"ResultsByTime": [_make_day("2026-01-01", 100, [("AmazonEC2", 100)])]}
    with pytest.raises(ValueError, match="Missing currency"):
        build_cost_summary(
            current,
            {"ResultsByTime": []},
            group_by="SERVICE",
            window_start=date(2026, 1, 1),
            window_end=date(2026, 1, 1),
            metric_name="NetUnblendedCost",
        )


def test_net_unblended_summary_rejects_mixed_currency():
    first = _make_day("2026-01-01", 50, [("AmazonEC2", 50)], "NetUnblendedCost")
    second = _make_day("2026-01-02", 50, [("AmazonEC2", 50)], "NetUnblendedCost")
    second["Total"]["NetUnblendedCost"]["Unit"] = "EUR"
    second["Groups"][0]["Metrics"]["NetUnblendedCost"]["Unit"] = "EUR"
    with pytest.raises(ValueError, match="Mixed currency"):
        build_cost_summary(
            {"ResultsByTime": [first, second]},
            {
                "ResultsByTime": [
                    _make_day(
                        "2025-12-30", 40, [("AmazonEC2", 40)], "NetUnblendedCost"
                    ),
                    _make_day(
                        "2025-12-31", 40, [("AmazonEC2", 40)], "NetUnblendedCost"
                    ),
                ]
            },
            group_by="SERVICE",
            window_start=date(2026, 1, 1),
            window_end=date(2026, 1, 2),
            metric_name="NetUnblendedCost",
        )


def _net_summary(current, previous, start=date(2026, 1, 1), end=date(2026, 1, 1)):
    return build_cost_summary(
        {"ResultsByTime": current},
        {"ResultsByTime": previous},
        group_by="SERVICE",
        window_start=start,
        window_end=end,
        metric_name="NetUnblendedCost",
    )


def test_net_unblended_rejects_missing_previous_date():
    current = [_make_day("2026-01-01", 50, [("EC2", 50)], "NetUnblendedCost")]
    with pytest.raises(ValueError, match="Incomplete previous-period"):
        _net_summary(current, [])


def test_net_unblended_rejects_duplicate_previous_date():
    current = [_make_day("2026-01-01", 50, [("EC2", 50)], "NetUnblendedCost")]
    previous = [
        _make_day("2025-12-31", 40, [("EC2", 40)], "NetUnblendedCost"),
        _make_day("2025-12-31", 40, [("EC2", 40)], "NetUnblendedCost"),
    ]
    with pytest.raises(ValueError, match="Duplicate date"):
        _net_summary(current, previous)


def test_net_unblended_rejects_unexpected_previous_date():
    current = [_make_day("2026-01-01", 50, [("EC2", 50)], "NetUnblendedCost")]
    previous = [_make_day("2025-12-30", 40, [("EC2", 40)], "NetUnblendedCost")]
    with pytest.raises(ValueError, match="unexpected"):
        _net_summary(current, previous)


def test_net_unblended_rejects_missing_previous_currency():
    current = [_make_day("2026-01-01", 50, [("EC2", 50)], "NetUnblendedCost")]
    previous = [_make_day("2025-12-31", 40, [("EC2", 40)], "NetUnblendedCost")]
    previous[0]["Total"]["NetUnblendedCost"].pop("Unit")
    previous[0]["Groups"][0]["Metrics"]["NetUnblendedCost"].pop("Unit")
    with pytest.raises(ValueError, match="Missing currency"):
        _net_summary(current, previous)


def test_net_unblended_rejects_mixed_previous_currency():
    current = [_make_day("2026-01-01", 50, [("EC2", 50)], "NetUnblendedCost")]
    previous = [_make_day("2025-12-31", 40, [("EC2", 40)], "NetUnblendedCost")]
    previous[0]["Groups"][0]["Metrics"]["NetUnblendedCost"]["Unit"] = "EUR"
    with pytest.raises(ValueError, match="Mixed currency"):
        _net_summary(current, previous)


def test_net_unblended_rejects_current_previous_currency_mismatch():
    current = [_make_day("2026-01-01", 50, [("EC2", 50)], "NetUnblendedCost")]
    previous = [_make_day("2025-12-31", 40, [("EC2", 40)], "NetUnblendedCost")]
    previous[0]["Total"]["NetUnblendedCost"]["Unit"] = "EUR"
    previous[0]["Groups"][0]["Metrics"]["NetUnblendedCost"]["Unit"] = "EUR"
    with pytest.raises(ValueError, match="currency mismatch"):
        _net_summary(current, previous)
