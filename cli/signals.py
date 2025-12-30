import json
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from finops_lite.signals.from_services import (
    read_services_report_csv,
    generate_signals_from_services,
)

console = Console()


@click.group(help="Decision signals that turn cost data into recommended actions.")
def signals():
    pass


@signals.command("from-services")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True), help="Path to services rollup CSV")
@click.option("--period", default="Last 30 days", help="Label used in outputs")
@click.option("--format", "output_format", default="table", help="table | json | executive")
@click.option("--export", type=click.Path(), default=None, help="Write output to a file")
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
    services = read_services_report_csv(file_path)
    signals_list = generate_signals_from_services(
        services,
        period_label=period,
        concentration_pct=concentration_pct,
        spike_amount_usd=spike_amount,
        spike_pct=spike_pct,
    )

    output_format = output_format.lower().strip()

    if output_format == "table":
        console.print(Panel.fit(f"Source: {file_path}\nPeriod: {period}", title="Signals"))
        table = Table(title="Decision Signals", show_lines=True)
        table.add_column("Severity", style="bold")
        table.add_column("Title", overflow="fold")
        table.add_column("Owner")
        table.add_column("Confidence")

        for s in signals_list:
            table.add_row(s.severity.upper(), s.title, s.owner, s.confidence.upper())

        console.print(table)
        return

    if output_format == "json":
        payload = {
            "period": period,
            "source": file_path,
            "signals": [s.to_dict() for s in signals_list],
        }
        output = json.dumps(payload, indent=2)
        if export:
            Path(export).write_text(output, encoding="utf-8")
            console.print(f"[green]Exported JSON to[/green] {export}")
        else:
            console.print(output)
        return

    if output_format == "executive":
        lines = []
        lines.append("# FinOps Lite — Executive Decision Summary")
        lines.append("")
        lines.append(f"Period: **{period}**")
        lines.append("")
        for s in signals_list:
            lines.append(f"## {s.title}")
            lines.append(f"- Severity: **{s.severity.upper()}**")
            lines.append(f"- Confidence: **{s.confidence.upper()}**")
            lines.append(f"- Owner: **{s.owner}**")
            lines.append(f"- Why it matters: {s.why_it_matters}")
            lines.append(f"- Recommended action: {s.recommended_action}")
            lines.append("")

        output = "\n".join(lines)
        if export:
            Path(export).write_text(output, encoding="utf-8")
            console.print(f"[green]Exported executive summary to[/green] {export}")
        else:
            console.print(output)
        return

    raise click.BadParameter("format must be one of: table | json | executive")
