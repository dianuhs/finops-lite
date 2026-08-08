"""
Helpers for building compact dashboard summaries.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Dict, List, Optional


def _to_decimal(value: Any, *, field: str = "amount") -> Decimal:
    """Parse a finite decimal without silently coercing invalid billing data to zero."""
    if value is None or value == "":
        raise ValueError(f"Missing numeric value for {field}")
    if isinstance(value, Decimal):
        result = value
    else:
        try:
            result = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid numeric value for {field}: {value!r}") from exc
    if not result.is_finite():
        raise ValueError(f"Non-finite numeric value for {field}: {value!r}")
    return result


def _round_money(amount: Decimal) -> float:
    return float(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _round_pct(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def _extract_currency(cost_data: Dict[str, Any], metric_name: str) -> str:
    observed: set[str] = set()
    for time_period in cost_data.get("ResultsByTime", []) or []:
        total = time_period.get("Total", {})
        metric = total.get(metric_name) if total else None
        if metric and metric.get("Unit"):
            observed.add(str(metric["Unit"]))

        for group in time_period.get("Groups", []) or []:
            metrics = group.get("Metrics") or {}
            metric = metrics.get(metric_name) or {}
            if metric.get("Unit"):
                observed.add(str(metric["Unit"]))

    if metric_name == "NetUnblendedCost":
        if not observed:
            raise ValueError("Missing currency for AWS Cost Explorer NetUnblendedCost")
        if len(observed) != 1:
            raise ValueError(
                f"Mixed currency for AWS Cost Explorer NetUnblendedCost: {sorted(observed)}"
            )
        return next(iter(observed))
    if observed:
        return next(iter(observed))
    return "USD"


def _period_total(time_period: Dict[str, Any], metric_name: str) -> Decimal:
    total = time_period.get("Total") or {}
    metric = total.get(metric_name) or {}
    if metric.get("Amount") is not None:
        return _to_decimal(metric.get("Amount"), field=f"Total.{metric_name}.Amount")

    # Fall back to summing group costs.
    total_amount = Decimal("0")
    for group in time_period.get("Groups", []) or []:
        metrics = group.get("Metrics") or {}
        metric = metrics.get(metric_name) or {}
        total_amount += _to_decimal(
            metric.get("Amount"), field=f"Groups[].Metrics.{metric_name}.Amount"
        )

    return total_amount


def _daily_totals(cost_data: Dict[str, Any], metric_name: str) -> Dict[str, Decimal]:
    totals: Dict[str, Decimal] = {}
    for time_period in cost_data.get("ResultsByTime", []) or []:
        time_info = time_period.get("TimePeriod", {}) or {}
        date_str = time_info.get("Start")
        if not date_str:
            continue
        totals[date_str] = _period_total(time_period, metric_name)
    return totals


def _validate_complete_dates(
    cost_data: Dict[str, Any], *, start: date, end: date, label: str
) -> None:
    observed: list[date] = []
    for index, time_period in enumerate(cost_data.get("ResultsByTime", []) or []):
        raw_date = (time_period.get("TimePeriod") or {}).get("Start")
        if not raw_date:
            raise ValueError(f"Missing {label} ResultsByTime[{index}].TimePeriod.Start")
        try:
            observed.append(date.fromisoformat(str(raw_date)))
        except ValueError as exc:
            raise ValueError(
                f"Invalid {label} Cost Explorer date: {raw_date!r}"
            ) from exc
    if len(observed) != len(set(observed)):
        raise ValueError(f"Duplicate date in {label} Cost Explorer response")
    expected = {
        start + timedelta(days=offset) for offset in range((end - start).days + 1)
    }
    missing = sorted(expected - set(observed))
    unexpected = sorted(set(observed) - expected)
    if missing or unexpected:
        raise ValueError(
            f"Incomplete {label} Cost Explorer dates: missing={missing}, unexpected={unexpected}"
        )


def _group_totals(cost_data: Dict[str, Any], metric_name: str) -> Dict[str, Decimal]:
    totals: Dict[str, Decimal] = {}
    for time_period in cost_data.get("ResultsByTime", []) or []:
        for group in time_period.get("Groups", []) or []:
            keys = group.get("Keys") or ["Unknown"]
            group_key = keys[0] if keys else "Unknown"
            metrics = group.get("Metrics") or {}
            metric = metrics.get(metric_name) or {}
            amount = _to_decimal(
                metric.get("Amount"), field=f"Groups[].Metrics.{metric_name}.Amount"
            )
            totals[group_key] = totals.get(group_key, Decimal("0")) + amount
    return totals


def _daily_group_totals(
    cost_data: Dict[str, Any], metric_name: str
) -> Dict[str, Dict[str, Decimal]]:
    daily: Dict[str, Dict[str, Decimal]] = {}
    for time_period in cost_data.get("ResultsByTime", []) or []:
        date_str = (time_period.get("TimePeriod") or {}).get("Start")
        if not date_str:
            raise ValueError("Missing ResultsByTime[].TimePeriod.Start")
        groups: Dict[str, Decimal] = {}
        for group in time_period.get("Groups", []) or []:
            keys = group.get("Keys") or []
            if not keys or not str(keys[0]).strip():
                raise ValueError("Missing ResultsByTime[].Groups[].Keys[0]")
            name = str(keys[0])
            amount = _to_decimal(
                ((group.get("Metrics") or {}).get(metric_name) or {}).get("Amount"),
                field=f"Groups[].Metrics.{metric_name}.Amount",
            )
            groups[name] = groups.get(name, Decimal("0")) + amount
        daily[date_str] = groups
    return daily


def build_cost_summary(
    current_data: Dict[str, Any],
    previous_data: Dict[str, Any],
    *,
    group_by: str,
    window_start: date,
    window_end: date,
    schema_version: str = "1.0",
    top_n: Optional[int] = 10,
    metric_name: str = "BlendedCost",
) -> Dict[str, Any]:
    """
    Build a compact dashboard summary from Cost Explorer responses.

    If previous_total_cost is zero, change_pct is returned as None.
    """
    if metric_name not in {"BlendedCost", "NetUnblendedCost"}:
        raise ValueError(f"Unsupported AWS Cost Explorer metric: {metric_name}")
    currency = _extract_currency(current_data, metric_name)
    comparison_window: Dict[str, str] | None = None
    if metric_name == "NetUnblendedCost":
        duration = (window_end - window_start).days + 1
        previous_end = window_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=duration - 1)
        _validate_complete_dates(
            current_data, start=window_start, end=window_end, label="current-period"
        )
        _validate_complete_dates(
            previous_data,
            start=previous_start,
            end=previous_end,
            label="previous-period",
        )
        previous_currency = _extract_currency(previous_data, metric_name)
        if previous_currency != currency:
            raise ValueError(
                f"Current/previous currency mismatch: {currency} != {previous_currency}"
            )
        comparison_window = {
            "start": previous_start.isoformat(),
            "end": previous_end.isoformat(),
        }

    current_totals = _daily_totals(current_data, metric_name)
    daily_group_totals = _daily_group_totals(current_data, metric_name)
    previous_totals = _daily_totals(previous_data, metric_name)

    total_cost_decimal = sum(current_totals.values(), Decimal("0"))
    previous_total_decimal = sum(previous_totals.values(), Decimal("0"))

    if previous_total_decimal > 0:
        change_pct = _round_pct(
            (total_cost_decimal - previous_total_decimal)
            / previous_total_decimal
            * Decimal("100")
        )
    else:
        change_pct = None

    group_totals = _group_totals(current_data, metric_name)
    total_cost_value = _round_money(total_cost_decimal)
    previous_total_value = _round_money(previous_total_decimal)

    top_groups: List[Dict[str, Any]] = []
    sorted_groups = sorted(group_totals.items(), key=lambda item: item[1], reverse=True)
    selected_groups = sorted_groups if top_n is None else sorted_groups[:top_n]
    for group, cost in selected_groups:
        pct_of_total = (
            _round_pct((cost / total_cost_decimal) * Decimal("100"))
            if total_cost_decimal > 0
            else 0.0
        )
        top_groups.append(
            {
                "group": group,
                "cost": _round_money(cost),
                "pct_of_total": pct_of_total,
            }
        )

    daily_trend: List[Dict[str, Any]] = []
    daily_groups: List[Dict[str, Any]] = []
    cursor = window_start
    while cursor <= window_end:
        date_str = cursor.isoformat()
        if date_str not in current_totals:
            raise ValueError(
                f"Missing Cost Explorer result for {date_str}; missing billing data is not observed zero"
            )
        daily_cost_decimal = current_totals[date_str]
        group_sum = sum(daily_group_totals.get(date_str, {}).values(), Decimal("0"))
        if abs(group_sum - daily_cost_decimal) > Decimal("0.01"):
            raise ValueError(
                f"Daily service breakdown does not reconcile for {date_str}: groups={group_sum} total={daily_cost_decimal}"
            )
        daily_cost = _round_money(daily_cost_decimal)
        daily_trend.append({"date": date_str, "cost": daily_cost})
        for group, cost in sorted(daily_group_totals.get(date_str, {}).items()):
            daily_groups.append(
                {"date": date_str, "group": group, "cost": _round_money(cost)}
            )
        cursor += timedelta(days=1)

    result = {
        "schema_version": schema_version,
        "currency": currency,
        "group_by": group_by,
        "window": {"start": window_start.isoformat(), "end": window_end.isoformat()},
        "total_cost": total_cost_value,
        "previous_total_cost": previous_total_value,
        "change_pct": change_pct,
        "top_groups": top_groups,
        "daily_trend": daily_trend,
        "daily_groups": daily_groups,
    }
    if metric_name != "BlendedCost":
        result["aws_cost_metric"] = metric_name
        result["comparison_window"] = comparison_window
    return result
