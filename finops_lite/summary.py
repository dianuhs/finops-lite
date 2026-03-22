"""
Helpers for building compact dashboard summaries.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, List, Optional


def _to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _round_money(amount: Decimal) -> float:
    return float(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _round_pct(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def _extract_currency(cost_data: Dict[str, Any]) -> str:
    for time_period in cost_data.get("ResultsByTime", []) or []:
        total = time_period.get("Total", {})
        blended = total.get("BlendedCost") if total else None
        if blended and blended.get("Unit"):
            return blended["Unit"]

        for group in time_period.get("Groups", []) or []:
            metrics = group.get("Metrics") or {}
            blended = metrics.get("BlendedCost") or {}
            if blended.get("Unit"):
                return blended["Unit"]

    return "USD"


def _period_total(time_period: Dict[str, Any]) -> Decimal:
    total = time_period.get("Total") or {}
    blended = total.get("BlendedCost") or {}
    if blended.get("Amount") is not None:
        return _to_decimal(blended.get("Amount", "0"))

    # Fall back to summing group costs.
    total_amount = Decimal("0")
    for group in time_period.get("Groups", []) or []:
        metrics = group.get("Metrics") or {}
        blended = metrics.get("BlendedCost") or {}
        total_amount += _to_decimal(blended.get("Amount", "0"))

    return total_amount


def _daily_totals(cost_data: Dict[str, Any]) -> Dict[str, Decimal]:
    totals: Dict[str, Decimal] = {}
    for time_period in cost_data.get("ResultsByTime", []) or []:
        time_info = time_period.get("TimePeriod", {}) or {}
        date_str = time_info.get("Start")
        if not date_str:
            continue
        totals[date_str] = _period_total(time_period)
    return totals


def _group_totals(cost_data: Dict[str, Any]) -> Dict[str, Decimal]:
    totals: Dict[str, Decimal] = {}
    for time_period in cost_data.get("ResultsByTime", []) or []:
        for group in time_period.get("Groups", []) or []:
            keys = group.get("Keys") or ["Unknown"]
            group_key = keys[0] if keys else "Unknown"
            metrics = group.get("Metrics") or {}
            blended = metrics.get("BlendedCost") or {}
            amount = _to_decimal(blended.get("Amount", "0"))
            totals[group_key] = totals.get(group_key, Decimal("0")) + amount
    return totals


def build_cost_summary(
    current_data: Dict[str, Any],
    previous_data: Dict[str, Any],
    *,
    group_by: str,
    window_start: date,
    window_end: date,
    schema_version: str = "1.0",
    top_n: int = 10,
) -> Dict[str, Any]:
    """
    Build a compact dashboard summary from Cost Explorer responses.

    If previous_total_cost is zero, change_pct is returned as None.
    """
    currency = _extract_currency(current_data)

    current_totals = _daily_totals(current_data)
    previous_totals = _daily_totals(previous_data)

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

    group_totals = _group_totals(current_data)
    total_cost_value = _round_money(total_cost_decimal)
    previous_total_value = _round_money(previous_total_decimal)

    top_groups: List[Dict[str, Any]] = []
    for group, cost in sorted(
        group_totals.items(), key=lambda item: item[1], reverse=True
    )[:top_n]:
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
    cursor = window_start
    while cursor <= window_end:
        date_str = cursor.isoformat()
        daily_cost = _round_money(current_totals.get(date_str, Decimal("0")))
        daily_trend.append({"date": date_str, "cost": daily_cost})
        cursor += timedelta(days=1)

    return {
        "schema_version": schema_version,
        "currency": currency,
        "group_by": group_by,
        "window": {"start": window_start.isoformat(), "end": window_end.isoformat()},
        "total_cost": total_cost_value,
        "previous_total_cost": previous_total_value,
        "change_pct": change_pct,
        "top_groups": top_groups,
        "daily_trend": daily_trend,
    }
