"""Performance utilities for SquatchCut operations."""

import time
from typing import Any, Callable, Optional, TypeVar
from functools import wraps

from SquatchCut.core import logger

T = TypeVar("T")


def performance_monitor(operation_name: str, threshold_seconds: float = 1.0):
    """Decorator to monitor performance of operations and log slow ones."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                if elapsed > threshold_seconds:
                    logger.warning(
                        f"Slow operation detected: {operation_name} took {elapsed:.2f}s "
                        f"(threshold: {threshold_seconds}s)"
                    )
                else:
                    logger.debug(f"{operation_name} completed in {elapsed:.3f}s")

        return wrapper

    return decorator


def batch_process(
    items: list,
    batch_size: int = 100,
    progress_callback: Optional[Callable[[int, int], None]] = None,
):
    """Process items in batches to avoid memory issues with large datasets."""
    total = len(items)
    for i in range(0, total, batch_size):
        batch = items[i : i + batch_size]
        if progress_callback:
            progress_callback(i + len(batch), total)
        yield batch


def validate_large_dataset_limits(num_parts: int, max_parts: int = 10000) -> None:
    """Validate that dataset size is within reasonable limits."""
    if num_parts > max_parts:
        raise ValueError(
            f"Dataset too large: {num_parts} parts exceeds maximum of {max_parts}. "
            f"Consider splitting your data into smaller files."
        )

    if num_parts > max_parts // 2:
        logger.warning(
            f"Large dataset detected: {num_parts} parts. "
            f"Processing may take longer than usual."
        )


def estimate_memory_usage(num_parts: int, avg_part_size_bytes: int = 1024) -> int:
    """Estimate memory usage for a given number of parts."""
    # Rough estimate: each part object + geometry + metadata
    base_overhead = num_parts * avg_part_size_bytes
    # Additional overhead for nesting algorithm data structures
    nesting_overhead = num_parts * 512  # Rough estimate
    return base_overhead + nesting_overhead


def check_system_resources(num_parts: int) -> None:
    """Check if system has sufficient resources for processing."""
    estimated_memory = estimate_memory_usage(num_parts)

    # Log resource requirements for large datasets
    if num_parts > 1000:
        logger.info(
            f"Processing {num_parts} parts. "
            f"Estimated memory usage: {estimated_memory / 1024 / 1024:.1f} MB"
        )

    # Warn about very large datasets
    if num_parts > 5000:
        logger.warning(
            f"Very large dataset: {num_parts} parts. "
            f"Consider processing in smaller batches if performance issues occur."
        )


class ProgressTracker:
    """Track progress of long-running operations."""

    def __init__(self, total_items: int, operation_name: str = "Processing"):
        self.total_items = total_items
        self.operation_name = operation_name
        self.processed_items = 0
        self.start_time = time.time()
        self.last_report_time = self.start_time
        self.report_interval = 5.0  # Report every 5 seconds

    def update(self, items_processed: int = 1) -> None:
        """Update progress and optionally report status."""
        self.processed_items += items_processed
        current_time = time.time()

        # Report progress periodically
        if current_time - self.last_report_time >= self.report_interval:
            self._report_progress()
            self.last_report_time = current_time

    def _report_progress(self) -> None:
        """Report current progress."""
        if self.total_items > 0:
            percent = (self.processed_items / self.total_items) * 100
            elapsed = time.time() - self.start_time

            if self.processed_items > 0:
                estimated_total = elapsed * (self.total_items / self.processed_items)
                remaining = estimated_total - elapsed
                logger.info(
                    f"{self.operation_name}: {self.processed_items}/{self.total_items} "
                    f"({percent:.1f}%) - ETA: {remaining:.1f}s"
                )

    def finish(self) -> None:
        """Report completion."""
        elapsed = time.time() - self.start_time
        logger.info(
            f"{self.operation_name} completed: {self.processed_items} items in {elapsed:.2f}s"
        )


def optimize_for_large_datasets(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to optimize functions for large datasets."""

    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        # Check if we're dealing with a large dataset
        parts_arg = None
        for arg in args:
            if hasattr(arg, "__len__") and len(arg) > 100:
                parts_arg = arg
                break

        if parts_arg is not None:
            num_parts = len(parts_arg)
            check_system_resources(num_parts)
            validate_large_dataset_limits(num_parts)

        return func(*args, **kwargs)

    return wrapper
