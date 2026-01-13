"""
Professional report formatters for FinOps Lite.
Handles multiple output formats: table, json, csv, yaml, executive summary.

Important:
- This file outputs REAL values from `cost_data` (no demo placeholders).
- It normalizes dataclasses/Decimals/datetimes into JSON/YAML/CSV friendly structures.
"""

import csv
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from decimal import Decimal
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from rich.console import Console


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal objects and dataclasses."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if is_dataclass(obj):
            return asdict(obj)
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
            Formatted string for file formats, None for console output (table)
        """
        output_format = (format_type or self.config.output.format or "table").lower()

        if output_format == "json":
            return self._format_json_output(cost_data)
        if output_format == "csv":
            return self._format_csv_output(cost_data)
        if output_format == "yaml":
            return self._format_yaml_output(cost_data)
        if output_format == "executive":
            return self._format_executive_summary(cost_data)

        # Default to table (handled by CLI)
        return None

    # ----------------------------
    # Normalization helpers
    # ----------------------------
    def _to_float(self, value: Any) -> float:
        if value is None:
            return 0.0
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(value)
        except Exception:
            return 0.0

    def _to_str_dt(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def _normalize_trend(self, trend_obj: Any) -> Dict[str, Any]:
        if trend_obj is None:
            return {
                "direction": "unknown",
                "change_percentage": 0.0,
                "change_amount": 0.0,
                "current_period_cost": 0.0,
                "previous_period_cost": 0.0,
            }

        if is_dataclass(trend_obj):
            d = asdict(trend_obj)
        elif isinstance(trend_obj, dict):
            d = trend_obj
        else:
            # Fallback: best effort attributes
            d = {
                "trend_direction": getattr(trend_obj, "trend_direction", "unknown"),
                "change_percentage": getattr(trend_obj, "change_percentage", 0.0),
                "change_amount": getattr(trend_obj, "change_amount", 0),
                "current_period_cost": getattr(trend_obj, "current_period_cost", 0),
                "previous_period_cost": getattr(trend_obj, "previous_period_cost", 0),
            }

        direction = d.get("trend_direction") or d.get("direction") or "unknown"
        return {
            "direction": direction,
            "change_percentage": float(d.get("change_percentage", 0.0) or 0.0),
            "change_amount": self._to_float(d.get("change_amount", 0)),
            "current_period_cost": self._to_float(d.get("current_period_cost", 0)),
            "previous_period_cost": self._to_float(d.get("previous_period_cost", 0)),
        }

    def _normalize_services(self, services: Any) -> List[Dict[str, Any]]:
        if not services:
            return []

        normalized: List[Dict[str, Any]] = []
        for s in services:
            if is_dataclass(s):
                sd = asdict(s)
            elif isinstance(s, dict):
                sd = s
            else:
                sd = {
                    "service_name": getattr(s, "service_name", "Unknown"),
                    "total_cost": getattr(s, "total_cost", 0),
                    "percentage_of_total": getattr(s, "percentage_of_total", 0.0),
                    "daily_average": getattr(s, "daily_average", 0),
                    "trend": getattr(s, "trend", None),
                    "top_usage_types": getattr(s, "top_usage_types", []),
                }

            normalized.append(
                {
                    "service_name": sd.get("service_name", "Unknown"),
                    "total_cost": self._to_float(sd.get("total_cost", 0)),
                    "percentage_of_total": float(sd.get("percentage_of_total", 0.0) or 0.0),
                    "daily_average": self._to_float(sd.get("daily_average", 0)),
                    "trend": self._normalize_trend(sd.get("trend")),
                    "top_usage_types": sd.get("top_usage_types") or [],
                }
            )

        # Keep a stable ordering (highest cost first)
        normalized.sort(key=lambda x: x.get("total_cost", 0.0), reverse=True)
        return normalized

    def _normalize_cost_overview(self, cost_data: Dict[str, Any]) -> Dict[str, Any]:
        period_days = int(cost_data.get("period_days") or cost_data.get("days") or 30)

        total_cost = self._to_float(cost_data.get("total_cost", 0))
        daily_average = self._to_float(cost_data.get("daily_average", 0))
        currency = cost_data.get("currency") or getattr(self.config.output, "currency", "USD")
        generated_at = cost_data.get("generated_at") or datetime.now()

        # Optional window fields (for monthly/compare features)
        window = cost_data.get("window") or {}
        window_start = cost_data.get("window_start")
        window_end = cost_data.get("window_end")

        trend = self._normalize_trend(cost_data.get("trend"))
        services = self._normalize_services(cost_data.get("service_breakdown"))

        return {
            "version": "1.0",
            "generated_at": self._to_str_dt(generated_at) or datetime.now().isoformat(),
            "report_type": cost_data.get("report_type", "cost_overview"),
            "period_days": period_days,
            "currency": currency,
            "window": window,
            "window_start": self._to_str_dt(window_start),
            "window_end": self._to_str_dt(window_end),
            "summary": {
                "total_cost": total_cost,
                "daily_average": daily_average,
                "trend": trend,
            },
            "services": services,
        }

    # ----------------------------
    # Output formatters
    # ----------------------------
    def _format_json_output(self, cost_data: Dict[str, Any]) -> str:
        payload = {"finops_lite_report": self._normalize_cost_overview(cost_data)}
        return json.dumps(payload, indent=2, cls=DecimalEncoder)

    def _format_yaml_output(self, cost_data: Dict[str, Any]) -> str:
        payload = {"finops_lite_report": self._normalize_cost_overview(cost_data)}
        return yaml.dump(payload, default_flow_style=False, sort_keys=False)

    def _format_csv_output(self, cost_data: Dict[str, Any]) -> str:
        report = self._normalize_cost_overview(cost_data)
        output = StringIO()
        writer = csv.writer(output)

        summary = report["summary"]
        trend = summary["trend"]

        writer.writerow(["FinOps Lite Cost Overview Report"])
        writer.writerow(["Generated", report["generated_at"]])
        writer.writerow(["Period Days", report["period_days"]])
        writer.writerow(["Currency", report["currency"]])

        # Optional time window
        if report.get("window_start") or report.get("window_end"):
            writer.writerow(["Window Start", report.get("window_start") or ""])
            writer.writerow(["Window End", report.get("window_end") or ""])

        writer.writerow(["Total Cost", summary["total_cost"]])
        writer.writerow(["Daily Average", summary["daily_average"]])
        writer.writerow(["Trend Direction", trend.get("direction", "unknown")])
        writer.writerow(["Trend Change %", trend.get("change_percentage", 0.0)])
        writer.writerow(["Trend Change Amount", trend.get("change_amount", 0.0)])
        writer.writerow([])

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

        for s in report["services"]:
            st = s["trend"]
            writer.writerow(
                [
                    s["service_name"],
                    s["total_cost"],
                    s["percentage_of_total"],
                    s["daily_average"],
                    st.get("direction", "unknown"),
                    st.get("change_percentage", 0.0),
                    st.get("change_amount", 0.0),
                ]
            )

        return output.getvalue()

    def _format_executive_summary(self, cost_data: Dict[str, Any]) -> str:
        report = self._normalize_cost_overview(cost_data)

        period_days = report["period_days"]
        currency = report["currency"]
        total_cost = report["summary"]["total_cost"]
        daily_avg = report["summary"]["daily_average"]
        trend = report["summary"]["trend"]

        # Monthly run rate estimate (based on 30-day month)
        monthly_run_rate = daily_avg * 30.0

        services = report["services"]
        top3 = services[:3]
        top3_share = sum([s.get("percentage_of_total", 0.0) for s in top3]) if top3 else 0.0

        def money(x: float) -> str:
            if currency.upper() == "USD":
                return f"${x:,.2f}"
            return f"{x:,.2f} {currency}"

        trend_dir = (trend.get("direction") or "unknown").upper()
        trend_pct = trend.get("change_percentage", 0.0)
        trend_amt = trend.get("change_amount", 0.0)

        window_line = ""
        if report.get("window_start") and report.get("window_end"):
            window_line = f"WINDOW: {report['window_start']} → {report['window_end']}\n"

        lines = []
        lines.append("FINOPS LITE - EXECUTIVE COST SUMMARY")
        lines.append("=" * 50)
        lines.append(f"REPORTING PERIOD: {period_days} Days")
        lines.append(f"GENERATED: {report['generated_at']}")
        if window_line:
            lines.append(window_line.rstrip())

        lines.append("")
        lines.append("KEY FINANCIAL METRICS")
        lines.append("-" * 25)
        lines.append(f"Total Cloud Spend: {money(total_cost)}")
        lines.append(f"Daily Average: {money(daily_avg)}")
        lines.append(f"Monthly Run Rate (est.): {money(monthly_run_rate)}")

        lines.append("")
        lines.append("COST TREND ANALYSIS")
        lines.append("-" * 25)
        lines.append(f"Trend Direction: {trend_dir}")
        lines.append(f"Period-over-Period Change: {trend_pct:+.1f}%")
        lines.append(f"Absolute Change: {money(trend_amt)}")

        lines.append("")
        lines.append("TOP SERVICE CONCENTRATION")
        lines.append("-" * 25)
        lines.append(f"Top 3 Services: {top3_share:.1f}% of total spend")

        lines.append("")
        lines.append("TOP SERVICES BY COST")
        lines.append("-" * 25)
        if not top3:
            lines.append("No service data returned for this period.")
        else:
            for i, s in enumerate(top3, start=1):
                lines.append(
                    f"{i}. {s['service_name']}: {money(s['total_cost'])} ({s['percentage_of_total']:.1f}%)"
                )

        # Recommendations (simple, based on the actual top services)
        lines.append("")
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 25)
        recs = []

        # High service concentration
        if top3_share >= 70:
            recs.append("• Spend is concentrated in a few services. Validate allocation + ownership for the top drivers.")

        # If EC2 present near top
        if any("EC2" in (s["service_name"] or "").upper() for s in services[:5]):
            recs.append("• EC2 is a top driver. Run rightsizing + RI/SP fit checks for steady workloads.")

        # If data transfer / CloudWatch / NAT might show up
        if any("CLOUDWATCH" in (s["service_name"] or "").upper() for s in services[:10]):
            recs.append("• CloudWatch is material. Check log retention, metrics cardinality, and high-volume ingestion.")
        if any("DATA TRANSFER" in (s["service_name"] or "").upper() for s in services[:10]):
            recs.append("• Data Transfer is material. Review cross-AZ / cross-region flows and egress patterns.")

        # Trend is up
        if (trend.get("direction") or "") == "up" and abs(trend_pct) >= 10:
            recs.append("• Spend is up meaningfully. Confirm if this was planned growth or leakage (orphans, scale drift).")

        if not recs:
            recs.append("• Review top services and validate whether increases are expected. If not, start with utilization + retention.")

        lines.extend(recs)

        lines.append("")
        lines.append("Generated by FinOps Lite")
        lines.append("For detail, run: finops cost overview --format json")

        return "\n".join(lines) + "\n"

    def save_report(
        self, content: str, filename: Optional[str] = None, format_type: str = "json"
    ) -> Path:
        """Save report to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"finops_report_{timestamp}.{format_type}"

        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        file_path = reports_dir / filename

        with open(file_path, "w") as f:
            f.write(content)

        self.console.print(f"[green]Report saved to: {file_path}[/green]")
        return file_path
