"""
Unit tests for summary payload construction.
"""

from datetime import date

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
