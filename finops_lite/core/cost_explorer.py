"""
AWS Cost Explorer service integration.
Handles all cost data retrieval and analysis.
"""

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..utils.config import FinOpsConfig

logger = logging.getLogger(__name__)


@dataclass
class CostData:
    """Cost data structure."""

    service: str
    cost: Decimal
    currency: str
    period_start: datetime
    period_end: datetime
    usage_quantity: Optional[Decimal] = None
    unit: Optional[str] = None


@dataclass
class CostTrend:
    """Cost trend analysis."""

    current_period_cost: Decimal
    previous_period_cost: Decimal
    change_amount: Decimal
    change_percentage: float
    trend_direction: str  # 'up', 'down', 'stable'


@dataclass
class ServiceCostBreakdown:
    """Service-level cost breakdown."""

    service_name: str
    total_cost: Decimal
    percentage_of_total: float
    daily_average: Decimal
    trend: CostTrend
    top_usage_types: List[Dict[str, Any]]


class CostExplorerService:
    """Service for interacting with AWS Cost Explorer API."""

    def __init__(self, config: FinOpsConfig):
        self.config = config
        self.session = config.get_boto3_session()
        self.ce_client = self.session.client("ce")

    def _load_fixture(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Load Cost Explorer fixture data and filter by requested time window
        to emulate real AWS CE behavior.
        """
        from pathlib import Path
        import json

        fixture_path = Path(__file__).parent.parent / "fixtures" / filename
        if not fixture_path.exists():
            return None

        with open(fixture_path) as f:
            data = json.load(f)

        return data

        logger.info(f"Using Cost Explorer fixture from {fixture_path}")
        with fixture_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    # ----------------------------
    # Window helpers
    # ----------------------------
    def _month_window(self, year: int, month: int) -> Tuple[datetime, datetime, int]:
        """
        Return (start_datetime, end_datetime, days) where end is exclusive for CE.

        CE expects:
          Start: inclusive
          End: exclusive
        """
        if month < 1 or month > 12:
            raise ValueError("month must be 1..12")

        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, month + 1, 1)

        days = (end - start).days
        return (
            datetime.combine(start, datetime.min.time()),
            datetime.combine(end, datetime.min.time()),
            days,
        )

    def _previous_month(self, year: int, month: int) -> Tuple[int, int]:
        if month == 1:
            return year - 1, 12
        return year, month - 1

    # ----------------------------
    # Core CE calls
    # ----------------------------
    def get_cost_and_usage(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "DAILY",
        group_by: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get cost and usage data from AWS Cost Explorer.

        In fixture mode, we load a local JSON file and slice ResultsByTime
        to match the requested [start_date, end_date) window. This keeps
        the analysis path identical to real AWS responses while giving us
        deterministic demo data.
        """
        if not metrics:
            metrics = ["BlendedCost", "UnblendedCost", "UsageQuantity"]

        if not group_by:
            group_by = ["SERVICE"]

        # CE dates are YYYY-MM-DD strings; use date portion
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        logger.info(
            f"Fetching cost data from {start_str} to {end_str} (granularity={granularity})"
        )

        # ----------------------------
        # Fixture mode for local/demo
        # ----------------------------
        fixture = self._load_fixture("ce_cost_and_usage.json")
        if fixture:
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            filtered = [
                r for r in fixture.get("ResultsByTime", [])
                if r["TimePeriod"]["Start"] >= start_str
                and r["TimePeriod"]["End"] <= end_str
            ]

            return {
                "ResultsByTime": filtered
            }
 


        # ----------------------------
        # Real AWS Cost Explorer call
        # ----------------------------
        group_by_params = [{"Type": "DIMENSION", "Key": dim} for dim in group_by]

        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={"Start": start_str, "End": end_str},
                Granularity=granularity,
                Metrics=metrics,
                GroupBy=group_by_params,
            )
            logger.debug(
                f"Retrieved {len(response.get('ResultsByTime', []))} time periods"
            )
            return response
        except Exception as e:
            logger.error(f"Error fetching cost data: {e}")
            raise

    # ----------------------------
    # Overviews
    # ----------------------------
    def get_monthly_cost_overview(self, days: int = 30) -> Dict[str, Any]:
        """
        Get a comprehensive cost overview for the last N days,
        compared to the previous N-day period.

        If a local fixture file exists, we use that for both current and
        previous data to enable deterministic testing on zero-spend accounts.
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.min.time())

        # Try fixture first (dev/test), fall back to real AWS Cost Explorer
        fixture = self._load_fixture("ce_cost_and_usage.json")

        if fixture:
            current_data = fixture
            previous_data = fixture
        else:
            current_data = self.get_cost_and_usage(
                start_dt,
                end_dt,
                granularity="DAILY",
                group_by=["SERVICE"],
                metrics=["BlendedCost", "UnblendedCost", "UsageQuantity"],
            )

            prev_end = start_date
            prev_start = prev_end - timedelta(days=days)
            prev_start_dt = datetime.combine(prev_start, datetime.min.time())
            prev_end_dt = datetime.combine(prev_end, datetime.min.time())

            previous_data = self.get_cost_and_usage(
                prev_start_dt,
                prev_end_dt,
                granularity="DAILY",
                group_by=["SERVICE"],
                metrics=["BlendedCost"],
            )

        analysis = self._analyze_cost_data(
            current_data=current_data,
            previous_data=previous_data,
            days=days,
            window_start=start_dt,
            window_end=end_dt,
            window={"type": "rolling_days", "days": days},
        )
        return analysis

    def get_month_cost_overview(self, year: int, month: int) -> Dict[str, Any]:
        """
        Get a month-window cost overview (YYYY-MM),
        compared to the previous month.
        """
        start_dt, end_dt, days = self._month_window(year, month)
        prev_y, prev_m = self._previous_month(year, month)
        prev_start_dt, prev_end_dt, _prev_days = self._month_window(prev_y, prev_m)

        current_data = self.get_cost_and_usage(
            start_dt,
            end_dt,
            granularity="DAILY",
            group_by=["SERVICE"],
            metrics=["BlendedCost", "UnblendedCost", "UsageQuantity"],
        )

        previous_data = self.get_cost_and_usage(
            prev_start_dt,
            prev_end_dt,
            granularity="DAILY",
            group_by=["SERVICE"],
            metrics=["BlendedCost"],
        )

        analysis = self._analyze_cost_data(
            current_data=current_data,
            previous_data=previous_data,
            days=days,
            window_start=start_dt,
            window_end=end_dt,
            window={
                "type": "calendar_month",
                "year": year,
                "month": month,
                "label": f"{year:04d}-{month:02d}",
            },
            report_type="cost_overview_month",
        )
        return analysis

    def compare_months(
        self, year_a: int, month_a: int, year_b: int, month_b: int
    ) -> Dict[str, Any]:
        """
        Compare month A vs month B (A = current, B = baseline).
        Returns an overview-shaped dict plus a 'comparison' section.
        """
        a = self.get_month_cost_overview(year_a, month_a)
        b = self.get_month_cost_overview(year_b, month_b)

        # Build service maps
        a_services = {s.service_name: s for s in a.get("service_breakdown", [])}
        b_services = {s.service_name: s for s in b.get("service_breakdown", [])}

        all_names = set(a_services.keys()) | set(b_services.keys())

        rows = []
        for name in all_names:
            a_cost = (
                a_services.get(name).total_cost if name in a_services else Decimal("0")
            )
            b_cost = (
                b_services.get(name).total_cost if name in b_services else Decimal("0")
            )
            delta = a_cost - b_cost
            pct = (
                float((delta / b_cost) * 100)
                if b_cost > 0
                else (100.0 if a_cost > 0 else 0.0)
            )

            rows.append(
                {
                    "service_name": name,
                    "current_cost": a_cost,
                    "baseline_cost": b_cost,
                    "delta": delta,
                    "delta_percentage": pct,
                }
            )

        rows.sort(key=lambda r: abs(r["delta"]), reverse=True)

        result = {
            **a,
            "report_type": "cost_compare_months",
            "comparison": {
                "current": {
                    "year": year_a,
                    "month": month_a,
                    "label": f"{year_a:04d}-{month_a:02d}",
                },
                "baseline": {
                    "year": year_b,
                    "month": month_b,
                    "label": f"{year_b:04d}-{month_b:02d}",
                },
                "service_deltas": rows[:50],  # keep it bounded
                "total_delta": a["total_cost"] - b["total_cost"],
                "total_delta_percentage": (
                    float(((a["total_cost"] - b["total_cost"]) / b["total_cost"]) * 100)
                    if b["total_cost"] > 0
                    else (100.0 if a["total_cost"] > 0 else 0.0)
                ),
            },
        }
        return result

    # ----------------------------
    # Analysis
    # ----------------------------
    def _analyze_cost_data(
        self,
        current_data: Dict[str, Any],
        previous_data: Dict[str, Any],
        days: int,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
        window: Optional[Dict[str, Any]] = None,
        report_type: str = "cost_overview",
    ) -> Dict[str, Any]:
        current_total = self._calculate_total_cost(current_data)
        previous_total = self._calculate_total_cost(previous_data)

        trend = self._calculate_trend(current_total, previous_total)
        service_breakdown = self._get_service_breakdown(
            current_data, previous_data, days=days
        )

        daily_average = (current_total / days) if days > 0 else Decimal("0")

        top_services = sorted(
            service_breakdown, key=lambda x: x.total_cost, reverse=True
        )[:10]

        return {
            "report_type": report_type,
            "period_days": days,
            "total_cost": current_total,
            "daily_average": daily_average,
            "trend": trend,
            "service_breakdown": top_services,
            "currency": "USD",
            "generated_at": datetime.now(),
            "window": window or {},
            "window_start": window_start,
            "window_end": window_end,
        }

    def _calculate_total_cost(self, cost_data: Dict[str, Any]) -> Decimal:
        """
        Sum total cost from a Cost Explorer response.

        Prefer UnblendedCost if present, else BlendedCost, else first metric.
        This makes the analyzer more robust to metric changes and also works
        with test fixtures that only include UnblendedCost.
        """
        total = Decimal("0")
        for time_period in cost_data.get("ResultsByTime", []):
            total_block = time_period.get("Total") or {}
            if not total_block:
                continue

            metric_obj = (
                total_block.get("UnblendedCost")
                or total_block.get("BlendedCost")
                or next(iter(total_block.values()), {"Amount": "0"})
            )

            amount = metric_obj.get("Amount", "0")
            total += Decimal(amount)
        return total

    def _calculate_trend(self, current: Decimal, previous: Decimal) -> CostTrend:
        """
        Calculate trend between current and previous periods.

        Handles the common FinOps case where the baseline (previous)
        period has zero spend:
          - If previous == 0 and current > 0 → treat as +100% and "up"
          - If both are zero → 0% and "stable"
        """
        change_amount = current - previous

        if previous > 0:
            change_percentage = float((change_amount / previous) * 100)
        elif current > 0:
            # New spend vs a zero baseline
            change_percentage = 100.0
        else:
            # Both zero
            change_percentage = 0.0

        # Direction logic
        if current == 0 and previous == 0:
            trend_direction = "stable"
        elif current > previous:
            trend_direction = "up"
        elif current < previous:
            trend_direction = "down"
        else:
            trend_direction = "stable"

        return CostTrend(
            current_period_cost=current,
            previous_period_cost=previous,
            change_amount=change_amount,
            change_percentage=change_percentage,
            trend_direction=trend_direction,
        )

    def _get_service_breakdown(
        self,
        current_data: Dict[str, Any],
        previous_data: Dict[str, Any],
        days: int,
    ) -> List[ServiceCostBreakdown]:
        # Aggregate costs by service for current period
        current_services: Dict[str, Decimal] = {}
        for time_period in current_data.get("ResultsByTime", []):
            for group in time_period.get("Groups", []):
                service_name = group["Keys"][0] if group.get("Keys") else "Unknown"
                metrics = group.get("Metrics", {}) or {}
                metric_obj = (
                    metrics.get("UnblendedCost")
                    or metrics.get("BlendedCost")
                    or {}
                )
                amount = Decimal(metric_obj.get("Amount", "0"))
                current_services[service_name] = (
                    current_services.get(service_name, Decimal("0")) + amount
                )

        # Aggregate costs by service for previous period
        previous_services: Dict[str, Decimal] = {}
        for time_period in previous_data.get("ResultsByTime", []):
            for group in time_period.get("Groups", []):
                service_name = group["Keys"][0] if group.get("Keys") else "Unknown"
                metrics = group.get("Metrics", {}) or {}
                metric_obj = (
                    metrics.get("UnblendedCost")
                    or metrics.get("BlendedCost")
                    or {}
                )
                amount = Decimal(metric_obj.get("Amount", "0"))
                previous_services[service_name] = (
                    previous_services.get(service_name, Decimal("0")) + amount
                )

        total_current = (
            sum(current_services.values()) if current_services else Decimal("0")
        )

        breakdown: List[ServiceCostBreakdown] = []
        for service_name, current_cost in current_services.items():
            previous_cost = previous_services.get(service_name, Decimal("0"))

            percentage = (
                float((current_cost / total_current) * 100)
                if total_current > 0
                else 0.0
            )
            daily_average = (current_cost / days) if days > 0 else Decimal("0")

            service_trend = self._calculate_trend(current_cost, previous_cost)

            breakdown.append(
                ServiceCostBreakdown(
                    service_name=service_name,
                    total_cost=current_cost,
                    percentage_of_total=percentage,
                    daily_average=daily_average,
                    trend=service_trend,
                    top_usage_types=[],
                )
            )

        breakdown.sort(key=lambda x: x.total_cost, reverse=True)
        return breakdown

