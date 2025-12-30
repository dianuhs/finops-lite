import csv
from dataclasses import dataclass
from typing import List

from finops_lite.signals.models import Signal


REQUIRED_COLUMNS = {
    "service_name",
    "total_cost",
    "percentage_of_total",
    "daily_average",
    "trend_direction",
    "trend_percentage",
    "trend_amount",
}


@dataclass
class ServiceRow:
    service_name: str
    total_cost: float
    percentage_of_total: float
    daily_average: float
    trend_direction: str
    trend_percentage: float
    trend_amount: float


def _to_float(value: str) -> float:
    """
    Converts values like "$1,234.56" or "1,234.56" or "1234.56" into float.
    """
    if value is None:
        return 0.0
    cleaned = str(value).replace("$", "").replace(",", "").strip()
    return float(cleaned) if cleaned else 0.0


def read_services_report_csv(path: str) -> List[ServiceRow]:
    """
    Reads a services rollup CSV with columns:
    service_name,total_cost,percentage_of_total,daily_average,trend_direction,trend_percentage,trend_amount
    """
    with open(path, "r", newline="", encoding="utf-8") as f:
        # Sniff delimiter (your example looked tab-separated in GitHub paste, but may be CSV in repo)
        sample = f.read(4096)
        f.seek(0)

        dialect = csv.Sniffer().sniff(sample, delimiters=[",", "\t"])
        reader = csv.DictReader(f, dialect=dialect)

        cols = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - cols
        if missing:
            raise ValueError(f"Missing columns: {sorted(missing)}. Found: {sorted(cols)}")

        rows: List[ServiceRow] = []
        for r in reader:
            rows.append(
                ServiceRow(
                    service_name=r["service_name"].strip(),
                    total_cost=_to_float(r["total_cost"]),
                    percentage_of_total=_to_float(r["percentage_of_total"]),
                    daily_average=_to_float(r["daily_average"]),
                    trend_direction=r["trend_direction"].strip().lower(),
                    trend_percentage=_to_float(r["trend_percentage"]),
                    trend_amount=_to_float(r["trend_amount"]),
                )
            )
        return rows


def generate_signals_from_services(
    services: List[ServiceRow],
    period_label: str = "Last 30 days",
    concentration_pct: float = 35.0,
    spike_amount_usd: float = 100.0,
    spike_pct: float = 10.0,
) -> List[Signal]:
    """
    Creates decision signals using service-level spend + trends.
    This is intentionally rule-based (fast, explainable, and practical).
    """
    if not services:
        return [
            Signal(
                id="no_data",
                title="No services data available",
                severity="warn",
                confidence="high",
                owner="FinOps",
                evidence={"period": period_label},
                why_it_matters="Without service-level spend, we can’t identify cost drivers or prioritize optimizations.",
                recommended_action="Regenerate the services report for the target period and re-run signals.",
            )
        ]

    signals: List[Signal] = []

    # Sort by % of total spend
    services_by_pct = sorted(services, key=lambda s: s.percentage_of_total, reverse=True)
    top = services_by_pct[0]

    # 1) Concentration risk
    if top.percentage_of_total >= concentration_pct:
        signals.append(
            Signal(
                id="concentration_risk",
                title=f"Concentration risk: {top.service_name} is {top.percentage_of_total:.1f}% of spend",
                severity="high" if top.percentage_of_total >= concentration_pct + 10 else "warn",
                confidence="high",
                owner="Shared",
                evidence={
                    "period": period_label,
                    "service_name": top.service_name,
                    "percentage_of_total": round(top.percentage_of_total, 2),
                    "total_cost": round(top.total_cost, 2),
                },
                why_it_matters=(
                    "When one service dominates spend, small usage or configuration changes can swing the bill. "
                    "This is also the highest-leverage place to focus optimization work."
                ),
                recommended_action=(
                    "Identify the primary workloads driving this service. Validate whether the trend is usage-driven "
                    "(expected) or config drift (fixable). Then pick one lever: rightsizing, commitments, scheduling, or lifecycle policies."
                ),
            )
        )

    # 2) Spike drivers (top 3 services by positive trend_amount that exceed thresholds)
    spike_drivers = sorted(services, key=lambda s: s.trend_amount, reverse=True)
    spike_drivers = [
        s for s in spike_drivers
        if s.trend_amount >= spike_amount_usd and s.trend_percentage >= spike_pct
    ][:3]

    if spike_drivers:
        signals.append(
            Signal(
                id="spike_drivers",
                title="Spend spike drivers: services increasing the bill",
                severity="warn",
                confidence="high",
                owner="Shared",
                evidence={
                    "period": period_label,
                    "drivers": [
                        {
                            "service_name": s.service_name,
                            "trend_amount": round(s.trend_amount, 2),
                            "trend_percentage": round(s.trend_percentage, 2),
                            "percentage_of_total": round(s.percentage_of_total, 2),
                        }
                        for s in spike_drivers
                    ],
                },
                why_it_matters=(
                    "Trend dollars show where attention will pay off fastest. "
                    "This prevents teams from optimizing low-impact areas while the real drivers keep compounding."
                ),
                recommended_action=(
                    "For each driver: identify the top account/tag/workload behind the increase, then validate whether it’s "
                    "a legitimate usage change or an unplanned change that needs correction."
                ),
            )
        )

    # 3) Simple “rising services” watchlist (less strict thresholds)
    rising = [
        s for s in services
        if s.trend_direction == "up" and s.trend_percentage >= 7.5 and s.trend_amount >= 25.0
    ]
    rising = sorted(rising, key=lambda s: s.trend_amount, reverse=True)[:5]

    if rising:
        signals.append(
            Signal(
                id="rising_watchlist",
                title="Rising services watchlist",
                severity="info" if len(rising) <= 2 else "warn",
                confidence="medium",
                owner="FinOps",
                evidence={
                    "period": period_label,
                    "services": [
                        {
                            "service_name": s.service_name,
                            "trend_amount": round(s.trend_amount, 2),
                            "trend_percentage": round(s.trend_percentage, 2),
                            "percentage_of_total": round(s.percentage_of_total, 2),
                        }
                        for s in rising
                    ],
                },
                why_it_matters="Catching upward trends early reduces decision latency and usually lowers the cost of fixes.",
                recommended_action=(
                    "Verify whether increases map to expected events (launch, traffic, migrations). "
                    "If not, create a small investigation task and assign an engineering owner within 48 hours."
                ),
            )
        )

    # If nothing triggered, return a healthy signal
    if not signals:
        signals.append(
            Signal(
                id="stable_spend",
                title="No major cost signals detected",
                severity="info",
                confidence="high",
                owner="FinOps",
                evidence={"period": period_label},
                why_it_matters="Stable trends mean you can focus on governance, allocation quality, and forecasting.",
                recommended_action="Improve tag coverage, define owners, and add 1–2 unit metrics (cost per environment, cost per workload).",
            )
        )

    return signals
