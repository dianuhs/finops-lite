"""
AWS Cost Explorer service integration.
Handles all cost data retrieval and analysis.
"""

import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from decimal import Decimal
import logging

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

        Args:
            start_date: Start date for cost analysis
            end_date: End date for cost analysis
            granularity: DAILY, MONTHLY, or HOURLY
            group_by: List of dimensions to group by (e.g., ['SERVICE'])
            metrics: List of metrics to retrieve (e.g., ['BlendedCost'])

        Returns:
            Cost and usage data from AWS Cost Explorer
        """
        if not metrics:
            metrics = ["BlendedCost", "UnblendedCost", "UsageQuantity"]

        if not group_by:
            group_by = ["SERVICE"]

        try:
            # Format dates as strings
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            logger.info(f"Fetching cost data from {start_str} to {end_str}")

            # Build GroupBy parameter
            group_by_params = []
            for dimension in group_by:
                group_by_params.append({"Type": "DIMENSION", "Key": dimension})

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

    def get_monthly_cost_overview(self, days: int = 30) -> Dict[str, Any]:
        """
        Get a comprehensive monthly cost overview.

        Args:
            days: Number of days to analyze

        Returns:
            Comprehensive cost overview with trends and breakdowns
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # Convert to datetime objects for API
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.min.time())

        # Get current period data
        current_data = self.get_cost_and_usage(
            start_datetime,
            end_datetime,
            granularity="DAILY",
            group_by=["SERVICE"],
            metrics=["BlendedCost", "UnblendedCost", "UsageQuantity"],
        )

        # Get previous period for trend analysis
        prev_end = start_date
        prev_start = prev_end - timedelta(days=days)
        prev_start_datetime = datetime.combine(prev_start, datetime.min.time())
        prev_end_datetime = datetime.combine(prev_end, datetime.min.time())

        previous_data = self.get_cost_and_usage(
            prev_start_datetime,
            prev_end_datetime,
            granularity="DAILY",
            group_by=["SERVICE"],
            metrics=["BlendedCost"],
        )

        # Process and analyze the data
        analysis = self._analyze_cost_data(current_data, previous_data, days)

        return analysis

    def _analyze_cost_data(
        self, current_data: Dict[str, Any], previous_data: Dict[str, Any], days: int
    ) -> Dict[str, Any]:
        """Analyze cost data and generate insights."""

        # Calculate total costs
        current_total = self._calculate_total_cost(current_data)
        previous_total = self._calculate_total_cost(previous_data)

        # Calculate trend
        trend = self._calculate_trend(current_total, previous_total)

        # Get service breakdown
        service_breakdown = self._get_service_breakdown(current_data, previous_data)

        # Calculate daily average
        daily_average = current_total / days if days > 0 else Decimal("0")

        # Get top services (limit to top 10)
        top_services = sorted(
            service_breakdown, key=lambda x: x.total_cost, reverse=True
        )[:10]

        return {
            "period_days": days,
            "total_cost": current_total,
            "daily_average": daily_average,
            "trend": trend,
            "service_breakdown": top_services,
            "currency": "USD",  # Could be made configurable
            "generated_at": datetime.now(),
        }

    def _calculate_total_cost(self, cost_data: Dict[str, Any]) -> Decimal:
        """Calculate total cost from Cost Explorer response."""
        total = Decimal("0")

        for time_period in cost_data.get("ResultsByTime", []):
            if time_period.get("Total"):
                # Use BlendedCost as the primary metric
                blended_cost = time_period["Total"].get("BlendedCost", {})
                amount = blended_cost.get("Amount", "0")
                total += Decimal(amount)

        return total

    def _calculate_trend(self, current: Decimal, previous: Decimal) -> CostTrend:
        """Calculate cost trend between two periods."""
        change_amount = current - previous

        if previous > 0:
            change_percentage = float((change_amount / previous) * 100)
        else:
            change_percentage = 0.0

        # Determine trend direction
        if abs(change_percentage) < 5:  # Less than 5% change
            trend_direction = "stable"
        elif change_percentage > 0:
            trend_direction = "up"
        else:
            trend_direction = "down"

        return CostTrend(
            current_period_cost=current,
            previous_period_cost=previous,
            change_amount=change_amount,
            change_percentage=change_percentage,
            trend_direction=trend_direction,
        )

    def _get_service_breakdown(
        self, current_data: Dict[str, Any], previous_data: Dict[str, Any]
    ) -> List[ServiceCostBreakdown]:
        """Get detailed service-level cost breakdown."""

        # Aggregate costs by service for current period
        current_services = {}
        for time_period in current_data.get("ResultsByTime", []):
            for group in time_period.get("Groups", []):
                service_name = group["Keys"][0] if group.get("Keys") else "Unknown"
                metrics = group.get("Metrics", {})

                blended_cost = metrics.get("BlendedCost", {})
                amount = Decimal(blended_cost.get("Amount", "0"))

                if service_name not in current_services:
                    current_services[service_name] = Decimal("0")
                current_services[service_name] += amount

        # Aggregate costs by service for previous period
        previous_services = {}
        for time_period in previous_data.get("ResultsByTime", []):
            for group in time_period.get("Groups", []):
                service_name = group["Keys"][0] if group.get("Keys") else "Unknown"
                metrics = group.get("Metrics", {})

                blended_cost = metrics.get("BlendedCost", {})
                amount = Decimal(blended_cost.get("Amount", "0"))

                if service_name not in previous_services:
                    previous_services[service_name] = Decimal("0")
                previous_services[service_name] += amount

        # Calculate total for percentage calculations
        total_current = sum(current_services.values())

        # Build service breakdown
        breakdown = []
        for service_name, current_cost in current_services.items():
            previous_cost = previous_services.get(service_name, Decimal("0"))

            # Calculate percentage of total
            percentage = (
                float((current_cost / total_current) * 100)
                if total_current > 0
                else 0.0
            )

            # Calculate daily average (assuming period length from config)
            daily_average = current_cost / self.config.cost.default_days

            # Calculate trend for this service
            service_trend = self._calculate_trend(current_cost, previous_cost)

            breakdown.append(
                ServiceCostBreakdown(
                    service_name=service_name,
                    total_cost=current_cost,
                    percentage_of_total=percentage,
                    daily_average=daily_average,
                    trend=service_trend,
                    top_usage_types=[],  # Could be expanded to include usage type details
                )
            )

        return breakdown

    def get_cost_by_dimension(
        self, dimension: str, days: int = 30, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get costs grouped by a specific dimension.

        Args:
            dimension: AWS dimension (SERVICE, LINKED_ACCOUNT, REGION, etc.)
            days: Number of days to analyze
            limit: Maximum number of results to return

        Returns:
            List of costs grouped by the specified dimension
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.min.time())

        try:
            response = self.get_cost_and_usage(
                start_datetime,
                end_datetime,
                granularity="DAILY",
                group_by=[dimension],
                metrics=["BlendedCost"],
            )

            # Aggregate costs by dimension value
            dimension_costs = {}
            for time_period in response.get("ResultsByTime", []):
                for group in time_period.get("Groups", []):
                    key = group["Keys"][0] if group.get("Keys") else "Unknown"
                    amount = Decimal(
                        group.get("Metrics", {})
                        .get("BlendedCost", {})
                        .get("Amount", "0")
                    )

                    if key not in dimension_costs:
                        dimension_costs[key] = Decimal("0")
                    dimension_costs[key] += amount

            # Sort by cost and limit results
            sorted_costs = sorted(
                dimension_costs.items(), key=lambda x: x[1], reverse=True
            )[:limit]

            # Format results
            total_cost = sum(dimension_costs.values())
            results = []

            for key, cost in sorted_costs:
                percentage = float((cost / total_cost) * 100) if total_cost > 0 else 0.0

                results.append(
                    {
                        "dimension_value": key,
                        "cost": cost,
                        "percentage": percentage,
                        "daily_average": cost / days,
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Error getting costs by {dimension}: {e}")
            raise

    def get_cost_anomalies(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get cost anomalies from AWS Cost Anomaly Detection.

        Args:
            days: Number of days to look back for anomalies

        Returns:
            List of cost anomalies
        """
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)

            response = self.ce_client.get_anomalies(
                DateInterval={
                    "StartDate": start_date.strftime("%Y-%m-%d"),
                    "EndDate": end_date.strftime("%Y-%m-%d"),
                }
            )

            anomalies = []
            for anomaly in response.get("Anomalies", []):
                anomalies.append(
                    {
                        "anomaly_id": anomaly.get("AnomalyId"),
                        "anomaly_score": anomaly.get("AnomalyScore", {}).get(
                            "CurrentScore", 0
                        ),
                        "impact": anomaly.get("Impact", {}).get("TotalImpact", 0),
                        "service": anomaly.get("DimensionKey", "Unknown"),
                        "start_date": anomaly.get("AnomalyStartDate"),
                        "end_date": anomaly.get("AnomalyEndDate"),
                        "feedback": anomaly.get("Feedback", "NONE"),
                    }
                )

            return anomalies

        except Exception as e:
            # Cost Anomaly Detection might not be available in all regions/accounts
            logger.warning(f"Could not fetch cost anomalies: {e}")
            return []
