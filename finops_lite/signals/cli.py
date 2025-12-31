"""
CLI for FinOps Lite decision signals.

This command group turns a simple cost rollup into "decision signals" that are easy
to share and act on.
"""

from __future__ import annotations

import json

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .from_services import build_signals_from_services_csv

console = Console()


@click.group()
def signals():
    """📡 Decision signals and lightweight analytics."""
    pass


@signals.command("from-services")
@click.option(
    "--file",
    "file_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to services rollup CSV",
)
@click.option("--period", default="Last 30 days", help="Label used in outputs")
@click.option(
    "--format",
    "output_format",
    default="table",
    help="table | json | executive",
)
@click.option(
    "--export",
    type=click.Path(),
    default=None,
    help="Write output to a file",
)
@click.option("--concentration-pct", default=35.0, type=float)
@click.option("--spike-amount", default=100.0, type=float)
@click.option("--spike-pct", default=10.0, type=float)
def from_services(
    file_path,
    period,
    output_format,
    export,
    concentration_pct,
    spike_amount,
    spike_pct,
):
    """Generate decision signals from a services rollup CSV."""
    signals_list = build_signals_from_services_csv(
        file_path=file_path,
        period_label=period,
        concentration_pct=concentration_pct,
        spike_amount_usd=spike_amount,
        spike_pct=spike_pct,
    )

    output_format = output_format.lower().strip()

    if output_format == "table":
        console.print(
            Panel.fit(
                f"Source: {file_path}\nPeriod: {period}",
                title="Signals",
            )
        )
        table = Table(title="Decision Signals", show_lines=True)
        table.add_column("Severity", style="bold")
        table.add_column("Title", overflow="fold")
        table.add_column("Owner")
        table.add_column("Confidence")
        table.add_column("Evidence", overflow="fold")

        for s in signals_list:
            evidence_str = ", ".join(f"{k}={v}" for k, v in (s.evidence or {}).items())
            table.add_row(s.severity, s.title, s.owner, s.confidence, evidence_str)

        console.print(table)

        if export:
            payload = [s.to_dict() for s in signals_list]
            with open(export, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            console.print(f"[green]Exported to {export}[/green]")
        return

    payload = [s.to_dict() for s in signals_list]

    if output_format == "json":
        text = json.dumps(payload, indent=2)
    elif output_format == "executive":
        lines = [f"Signals ({period})", ""]
        for s in signals_list:
            lines.append(
                f"- [{s.severity.upper()}] {s.title} (Owner: {s.owner}, Confidence: {s.confidence})"
            )
        text = "\n".join(lines)
    else:
        raise click.ClickException("Unsupported format. Use: table | json | executive")

    console.print(text)

    if export:
        with open(export, "w", encoding="utf-8") as f:
            f.write(text)
        console.print(f"[green]Exported to {export}[/green]")
