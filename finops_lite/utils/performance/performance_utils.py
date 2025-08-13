"""
Performance utilities for FinOps Lite.
Provides timing, progress tracking, and concurrent execution helpers.
"""

import time
import asyncio
import concurrent.futures
from typing import List, Callable, Any, Optional, Dict
from functools import wraps
from contextlib import contextmanager
from dataclasses import dataclass

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    BarColumn,
)
from rich.table import Table
from rich.panel import Panel

console = Console()


@dataclass
class PerformanceMetrics:
    """Track performance metrics for operations."""

    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    api_calls_made: int = 0
    cache_hits: int = 0
    error_count: int = 0

    def finish(self):
        """Mark operation as finished and calculate duration."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time

    def __str__(self) -> str:
        if self.duration:
            return f"{self.operation_name}: {self.duration:.2f}s"
        return f"{self.operation_name}: In progress..."


class PerformanceTracker:
    """Track and report performance metrics across operations."""

    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.current_operation: Optional[PerformanceMetrics] = None

    def start_operation(self, name: str) -> PerformanceMetrics:
        """Start tracking a new operation."""
        metric = PerformanceMetrics(operation_name=name, start_time=time.time())
        self.metrics.append(metric)
        self.current_operation = metric
        return metric

    def finish_current_operation(self):
        """Finish the current operation."""
        if self.current_operation:
            self.current_operation.finish()
            self.current_operation = None

    def record_api_call(self):
        """Record an API call for the current operation."""
        if self.current_operation:
            self.current_operation.api_calls_made += 1

    def record_cache_hit(self):
        """Record a cache hit for the current operation."""
        if self.current_operation:
            self.current_operation.cache_hits += 1

    def record_error(self):
        """Record an error for the current operation."""
        if self.current_operation:
            self.current_operation.error_count += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.metrics:
            return {}

        total_duration = sum(m.duration for m in self.metrics if m.duration)
        total_api_calls = sum(m.api_calls_made for m in self.metrics)
        total_cache_hits = sum(m.cache_hits for m in self.metrics)
        total_errors = sum(m.error_count for m in self.metrics)

        return {
            "total_operations": len(self.metrics),
            "total_duration": round(total_duration, 2),
            "total_api_calls": total_api_calls,
            "total_cache_hits": total_cache_hits,
            "total_errors": total_errors,
            "avg_duration": (
                round(total_duration / len(self.metrics), 2) if self.metrics else 0
            ),
            "cache_efficiency": (
                round(
                    (total_cache_hits / (total_api_calls + total_cache_hits) * 100), 1
                )
                if (total_api_calls + total_cache_hits) > 0
                else 0
            ),
        }

    def show_summary(self, verbose: bool = False):
        """Display performance summary."""
        summary = self.get_summary()

        if not summary:
            return

        if verbose:
            # Detailed performance report
            table = Table(title="🚀 Performance Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Total Operations", str(summary["total_operations"]))
            table.add_row("Total Duration", f"{summary['total_duration']}s")
            table.add_row("Average Duration", f"{summary['avg_duration']}s")
            table.add_row("API Calls Made", str(summary["total_api_calls"]))
            table.add_row("Cache Hits", str(summary["total_cache_hits"]))
            table.add_row("Cache Efficiency", f"{summary['cache_efficiency']}%")
            table.add_row("Errors", str(summary["total_errors"]))

            console.print(table)

            # Individual operation details
            if len(self.metrics) > 1:
                ops_table = Table(title="📊 Operation Details")
                ops_table.add_column("Operation", style="cyan")
                ops_table.add_column("Duration", style="green")
                ops_table.add_column("API Calls", style="yellow")
                ops_table.add_column("Cache Hits", style="blue")

                for metric in self.metrics:
                    if metric.duration:
                        ops_table.add_row(
                            metric.operation_name,
                            f"{metric.duration:.2f}s",
                            str(metric.api_calls_made),
                            str(metric.cache_hits),
                        )

                console.print(ops_table)
        else:
            # Simple summary
            if (
                summary["total_duration"] > 1.0
            ):  # Only show if operation took meaningful time
                efficiency_text = ""
                if summary["cache_efficiency"] > 0:
                    efficiency_text = f" (Cache: {summary['cache_efficiency']}%)"

                console.print(
                    f"[dim]⏱️  Completed in {summary['total_duration']}s{efficiency_text}[/dim]"
                )


def timing_decorator(operation_name: str = None):
    """Decorator to automatically time function execution."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = operation_name or func.__name__
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                if duration > 0.5:  # Only log if operation took meaningful time
                    console.print(f"[dim]⏱️  {name}: {duration:.2f}s[/dim]")

                return result
            except Exception as e:
                duration = time.time() - start_time
                console.print(f"[dim]❌ {name} failed after {duration:.2f}s[/dim]")
                raise

        return wrapper

    return decorator


@contextmanager
def performance_context(
    operation_name: str, tracker: Optional[PerformanceTracker] = None
):
    """Context manager for tracking operation performance."""
    if tracker:
        metric = tracker.start_operation(operation_name)
    else:
        metric = PerformanceMetrics(operation_name, time.time())

    try:
        yield metric
    finally:
        metric.finish()
        if tracker:
            tracker.finish_current_operation()


def create_progress_bar(description: str = "Processing...") -> Progress:
    """Create a standardized progress bar for operations."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    )


def run_concurrent_tasks(
    tasks: List[Callable],
    max_workers: int = 4,
    description: str = "Processing tasks...",
) -> List[Any]:
    """
    Run multiple tasks concurrently with progress tracking.

    Args:
        tasks: List of callable tasks to execute
        max_workers: Maximum number of concurrent workers
        description: Description for progress bar

    Returns:
        List of results from tasks
    """
    if not tasks:
        return []

    if len(tasks) == 1:
        # Single task, no need for concurrency
        return [tasks[0]()]

    results = []

    with create_progress_bar() as progress:
        task_id = progress.add_task(description, total=len(tasks))

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_index = {executor.submit(task): i for i, task in enumerate(tasks)}

            # Collect results as they complete
            completed_results = [None] * len(tasks)

            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    completed_results[index] = future.result()
                except Exception as e:
                    console.print(f"[red]Task {index} failed: {e}[/red]")
                    completed_results[index] = None

                progress.update(task_id, advance=1)

            results = completed_results

    return results


async def run_async_tasks(
    tasks: List[Callable], description: str = "Processing async tasks..."
) -> List[Any]:
    """
    Run multiple async tasks concurrently with progress tracking.

    Args:
        tasks: List of async callable tasks
        description: Description for progress bar

    Returns:
        List of results from tasks
    """
    if not tasks:
        return []

    if len(tasks) == 1:
        return [await tasks[0]()]

    with create_progress_bar() as progress:
        task_id = progress.add_task(description, total=len(tasks))

        async def run_with_progress(task, task_index):
            try:
                result = await task()
                progress.update(task_id, advance=1)
                return result
            except Exception as e:
                console.print(f"[red]Async task {task_index} failed: {e}[/red]")
                progress.update(task_id, advance=1)
                return None

        # Run all tasks concurrently
        results = await asyncio.gather(
            *[run_with_progress(task, i) for i, task in enumerate(tasks)],
            return_exceptions=True,
        )

    return results


class BatchProcessor:
    """Process items in batches with progress tracking."""

    def __init__(self, batch_size: int = 10, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers

    def process(
        self,
        items: List[Any],
        processor: Callable,
        description: str = "Processing items...",
    ) -> List[Any]:
        """
        Process items in batches.

        Args:
            items: List of items to process
            processor: Function to process each item
            description: Description for progress bar

        Returns:
            List of processed results
        """
        if not items:
            return []

        # Create batches
        batches = [
            items[i : i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]

        all_results = []

        with create_progress_bar() as progress:
            task_id = progress.add_task(description, total=len(items))

            for batch in batches:
                # Process batch items concurrently
                batch_tasks = [lambda item=item: processor(item) for item in batch]
                batch_results = run_concurrent_tasks(
                    batch_tasks,
                    max_workers=min(self.max_workers, len(batch)),
                    description=f"Processing batch of {len(batch)} items...",
                )

                all_results.extend(batch_results)
                progress.update(task_id, advance=len(batch))

        return all_results


@contextmanager
def show_spinner(message: str = "Working..."):
    """Simple spinner context manager for quick operations."""
    with console.status(f"[bold blue]{message}"):
        yield
