"""
Signals builder: derive decision signals from a service rollup CSV.

Expected columns:
service_name,total_cost,percentage_of_total,daily_average,trend_direction,trend_percentage,trend_amount
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

REQUIRED_COLUMNS: Set[str] = {
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


@dataclass
class Signal:
    id: str
    title: str
    severity: str
    confidence: str
    owner: str
    evidence: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "severity": self.severity,
            "confidence": self.confidence,
            "owner": self.owner,
            "evidence": self.evidence or {},
        }


def _read_services_csv(file_path: str) -> List[ServiceRow]:
    with open(file_path, "r", encoding="utf-8", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        dialect = csv.Sniffer().sniff(sample)
        reader = csv.DictReader(f, dialect=dialect)

        cols = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - cols
        if missing:
            raise ValueError(
                f"Missing columns: {sorted(missing)}. Found: {sorted(cols)}"
            )

        rows: List[ServiceRow] = []
        for r in reader:
            rows.append(
                ServiceRow(
                    service_name=str(r["service_name"]).strip(),
                    total_cost=float(r["total_cost"]),
                    percentage_of_total=float(r["percentage_of_total"]),
                    daily_average=float(r["daily_average"]),
                    trend_direction=str(r["trend_direction"]).strip().lower(),
                    trend_percentage=float(r["trend_percentage"]),
                    trend_amount=float(r["trend_amount"]),
                )
            )
        return rows


def build_signals_from_services_csv(
    file_path: str,
    period_label: str = "Last 30 days",
    concentration_pct: float = 35.0,
    spike_amount_usd: float = 100.0,
    spike_pct: float = 10.0,
) -> List[Signal]:
    services = _read_services_csv(file_path)

    if not services:
        return [
            Signal(
                id="no_data",
                title="No rows found in services CSV",
                severity="info",
                confidence="high",
                owner="Shared",
                evidence={"period": period_label},
            )
        ]

    signals: List[Signal] = []

    services_by_pct = sorted(
        services,
        key=lambda s: s.percentage_of_total,
        reverse=True,
    )
    top = services_by_pct[0]

    if top.percentage_of_total >= concentration_pct:
        signals.append(
            Signal(
                id="concentration_risk",
                title=(
                    f"Concentration risk: {top.service_name} is "
                    f"{top.percentage_of_total:.1f}% of spend"
                ),
                severity=(
                    "high"
                    if top.percentage_of_total >= concentration_pct + 10
                    else "warn"
                ),
                confidence="high",
                owner="Shared",
                evidence={
                    "period": period_label,
                    "service_name": top.service_name,
                    "percentage_of_total": round(top.percentage_of_total, 2),
                    "total_cost": round(top.total_cost, 2),
                },
            )
        )

    spike_drivers = sorted(services, key=lambda s: s.trend_amount, reverse=True)
    spike_drivers = [
        s
        for s in spike_drivers
        if s.trend_amount >= spike_amount_usd and s.trend_percentage >= spike_pct
    ][:3]

    if spike_drivers:
        items = [
            {
                "service_name": s.service_name,
                "trend_amount": round(s.trend_amount, 2),
                "trend_percentage": round(s.trend_percentage, 2),
            }
            for s in spike_drivers
        ]
        signals.append(
            Signal(
                id="spike_drivers",
                title="Spike drivers detected (top movers)",
                severity="warn",
                confidence="medium",
                owner="FinOps",
                evidence={"period": period_label, "drivers": items},
            )
        )

    rising = [
        s
        for s in services
        if s.trend_direction == "up"
        and s.trend_percentage >= 7.5
        and s.trend_amount >= 25.0
    ]
    rising = sorted(rising, key=lambda s: s.trend_amount, reverse=True)[:5]

    if rising:
        items = [
            {
                "service_name": s.service_name,
                "trend_amount": round(s.trend_amount, 2),
                "trend_percentage": round(s.trend_percentage, 2),
            }
            for s in rising
        ]
        signals.append(
            Signal(
                id="rising_watchlist",
                title="Rising services watchlist",
                severity="info",
                confidence="medium",
                owner="FinOps",
                evidence={"period": period_label, "services": items},
            )
        )

    if not signals:
        signals.append(
            Signal(
                id="no_signals",
                title="No notable signals detected from service rollup",
                severity="info",
                confidence="high",
                owner="Shared",
                evidence={"period": period_label},
            )
        )

    return signals
