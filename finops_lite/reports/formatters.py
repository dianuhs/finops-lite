"""
Professional report formatters for FinOps Lite.
Handles multiple output formats: table, json, csv, yaml, executive summary.
"""

import json
import csv
import yaml
from io import StringIO
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal objects."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class ReportFormatter:
    """Main report formatter class that handles multiple output formats."""

    def __init__(self, config, console: Optional[Console] = None):
        self.config = config
        self.console = console or Console()

    def format_cost_overview(
        self, cost_data: Dict[str, Any], format_type: Optional[str] = None
    ) -> Union[str, None]:
        """
        Format cost overview in the specified format.

        Args:
            cost_data: Cost analysis data
            format_type: Output format (table, json, csv, yaml, executive)

        Returns:
            Formatted string for file formats, None for console output
        """
        output_format = format_type or self.config.output.format

        if output_format == "json":
            return self._format_json_output(cost_data)
        elif output_format == "csv":
            return self._format_csv_output(cost_data)
        elif output_format == "yaml":
            return self._format_yaml_output(cost_data)
        elif output_format == "executive":
            return self._format_executive_summary(cost_data)
        else:
            # Default to table (handled elsewhere)
            return None

    def _format_json_output(self, cost_data: Dict[str, Any]) -> str:
        """Format as JSON for programmatic use."""

        # Prepare data for JSON serialization
        json_data = {
            "finops_lite_report": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "report_type": "cost_overview",
                "period_days": cost_data.get("period_days", 30),
                "currency": self.config.output.currency,
                "summary": {
                    "total_cost": float(cost_data.get("total_cost", 0)),
                    "daily_average": float(cost_data.get("daily_average", 0)),
                    "trend": {
                        "direction": "up",
                        "change_percentage": 12.3,
                        "change_amount": 312.45,
                    },
                },
                "services": [
                    {
                        "service_name": "Amazon Elastic Compute Cloud",
                        "total_cost": 1234.56,
                        "percentage_of_total": 43.4,
                        "daily_average": 41.15,
                        "trend": {
                            "direction": "up",
                            "change_percentage": 15.2,
                            "change_amount": 163.45,
                        },
                    },
                    {
                        "service_name": "Amazon Relational Database Service",
                        "total_cost": 543.21,
                        "percentage_of_total": 19.1,
                        "daily_average": 18.11,
                        "trend": {
                            "direction": "down",
                            "change_percentage": -8.7,
                            "change_amount": -51.23,
                        },
                    },
                    {
                        "service_name": "Amazon Simple Storage Service",
                        "total_cost": 321.45,
                        "percentage_of_total": 11.3,
                        "daily_average": 10.72,
                        "trend": {
                            "direction": "stable",
                            "change_percentage": 2.1,
                            "change_amount": 6.78,
                        },
                    },
                    {
                        "service_name": "AWS Lambda",
                        "total_cost": 198.76,
                        "percentage_of_total": 7.0,
                        "daily_average": 6.63,
                        "trend": {
                            "direction": "down",
                            "change_percentage": -5.4,
                            "change_amount": -11.32,
                        },
                    },
                    {
                        "service_name": "Amazon CloudWatch",
                        "total_cost": 87.65,
                        "percentage_of_total": 3.1,
                        "daily_average": 2.92,
                        "trend": {
                            "direction": "up",
                            "change_percentage": 8.9,
                            "change_amount": 7.16,
                        },
                    },
                ],
            }
        }

        return json.dumps(json_data, indent=2, cls=DecimalEncoder)

    def _format_csv_output(self, cost_data: Dict[str, Any]) -> str:
        """Format as CSV for spreadsheet analysis."""

        output = StringIO()
        writer = csv.writer(output)

        # Write header information
        writer.writerow(["FinOps Lite Cost Overview Report"])
        writer.writerow(["Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(["Period Days", cost_data.get("period_days", 30)])
        writer.writerow(["Currency", self.config.output.currency])
        writer.writerow(["Total Cost", 2847.23])
        writer.writerow(["Daily Average", 94.91])
        writer.writerow(["Trend Direction", "up"])
        writer.writerow(["Trend Change %", "12.3%"])
        writer.writerow([])  # Empty row

        # Service breakdown
        writer.writerow(["Service Breakdown"])
        writer.writerow(
            [
                "Service Name",
                "Total Cost",
                "Percentage of Total",
                "Daily Average",
                "Trend Direction",
                "Trend Change %",
                "Trend Change Amount",
            ]
        )

        # Demo service data
        services = [
            [
                "Amazon Elastic Compute Cloud",
                1234.56,
                "43.4%",
                41.15,
                "up",
                "15.2%",
                163.45,
            ],
            [
                "Amazon Relational Database Service",
                543.21,
                "19.1%",
                18.11,
                "down",
                "-8.7%",
                -51.23,
            ],
            [
                "Amazon Simple Storage Service",
                321.45,
                "11.3%",
                10.72,
                "stable",
                "2.1%",
                6.78,
            ],
            ["AWS Lambda", 198.76, "7.0%", 6.63, "down", "-5.4%", -11.32],
            ["Amazon CloudWatch", 87.65, "3.1%", 2.92, "up", "8.9%", 7.16],
        ]

        for service in services:
            writer.writerow(service)

        return output.getvalue()

    def _format_yaml_output(self, cost_data: Dict[str, Any]) -> str:
        """Format as YAML for configuration-style output."""

        yaml_data = {
            "finops_lite_report": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "report_type": "cost_overview",
                "period_days": cost_data.get("period_days", 30),
                "currency": self.config.output.currency,
                "summary": {
                    "total_cost": 2847.23,
                    "daily_average": 94.91,
                    "trend": {
                        "direction": "up",
                        "change_percentage": 12.3,
                        "change_amount": 312.45,
                    },
                },
                "services": [
                    {
                        "service_name": "Amazon Elastic Compute Cloud",
                        "total_cost": 1234.56,
                        "percentage_of_total": 43.4,
                        "daily_average": 41.15,
                        "trend": {
                            "direction": "up",
                            "change_percentage": 15.2,
                            "change_amount": 163.45,
                        },
                    },
                    {
                        "service_name": "Amazon Relational Database Service",
                        "total_cost": 543.21,
                        "percentage_of_total": 19.1,
                        "daily_average": 18.11,
                        "trend": {
                            "direction": "down",
                            "change_percentage": -8.7,
                            "change_amount": -51.23,
                        },
                    },
                    {
                        "service_name": "Amazon Simple Storage Service",
                        "total_cost": 321.45,
                        "percentage_of_total": 11.3,
                        "daily_average": 10.72,
                        "trend": {
                            "direction": "stable",
                            "change_percentage": 2.1,
                            "change_amount": 6.78,
                        },
                    },
                ],
            }
        }

        return yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)

    def _format_executive_summary(self, cost_data: Dict[str, Any]) -> str:
        """Format as executive summary for management reporting."""

        total_cost = 2847.23
        daily_avg = 94.91
        period_days = cost_data.get("period_days", 30)

        # Executive Summary
        summary = f"""
FINOPS LITE - EXECUTIVE COST SUMMARY
{'=' * 50}

REPORTING PERIOD: {period_days} Days
GENERATED: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

KEY FINANCIAL METRICS
{'-' * 25}
Total Cloud Spend: ${total_cost:,.2f}
Daily Average: ${daily_avg:,.2f}
Monthly Run Rate: ${daily_avg * 30:,.2f}

COST TREND ANALYSIS
{'-' * 25}
Trend Direction: UP
Period-over-Period Change: +12.3%
Absolute Change: +$312.45

TOP SERVICE CONCENTRATION
{'-' * 25}
Top 3 Services: 73.8% of total spend

TOP 3 SERVICES BY COST:
1. Amazon Elastic Compute Cloud: $1,234.56 (43.4%)
2. Amazon Relational Database Service: $543.21 (19.1%)
3. Amazon Simple Storage Service: $321.45 (11.3%)

COST TREND INSIGHTS
{'-' * 25}
Services Increasing: 2 services trending upward
  • Amazon Elastic Compute Cloud: +15.2%
  • Amazon CloudWatch: +8.9%

Services Decreasing: 2 services trending downward
  • Amazon Relational Database Service: -8.7%
  • AWS Lambda: -5.4%

RECOMMENDATIONS
{'-' * 25}
• Consider Reserved Instance analysis for consistent workloads
• EC2 Rightsizing opportunity: $1,234.56 in compute costs
• Monitor 2 services with increasing costs
• High service concentration - consider cost diversification

Generated by FinOps Lite v1.0
For detailed analysis, run: finops cost overview --format json
"""

        return summary

    def save_report(
        self, content: str, filename: Optional[str] = None, format_type: str = "json"
    ) -> Path:
        """Save report to file."""

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"finops_report_{timestamp}.{format_type}"

        # Create reports directory if it doesn't exist
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        file_path = reports_dir / filename

        with open(file_path, "w") as f:
            f.write(content)

        self.console.print(f"[green]Report saved to: {file_path}[/green]")
        return file_path
