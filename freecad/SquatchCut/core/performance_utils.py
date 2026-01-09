"""Performance utilities for SquatchCut operations."""

import hashlib
import multiprocessing
import pickle
import tempfile
import threading
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar

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
    progress_callback: Callable[[int, int], None] | None = None,
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

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and report completion."""
        self.finish()
        return False

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


class NestingCache:
    """Cache for nesting results to avoid recomputation."""

    def __init__(self, cache_dir: str | None = None, max_cache_size: int = 100):
        self.cache_dir = (
            Path(cache_dir)
            if cache_dir
            else Path(tempfile.gettempdir()) / "squatchcut_cache"
        )
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_cache_size = max_cache_size
        self._memory_cache: dict[str, Any] = {}
        self._cache_lock = threading.Lock()

    def _generate_cache_key(
        self, parts: list, sheet_width: float, sheet_height: float, config: Any = None
    ) -> str:
        """Generate a unique cache key for the nesting parameters."""
        # Create a hashable representation of the input
        parts_data = []
        for part in parts:
            if hasattr(part, "__dict__"):
                parts_data.append(sorted(part.__dict__.items()))
            else:
                parts_data.append(str(part))

        config_data = (
            str(sorted(config.__dict__.items()))
            if config and hasattr(config, "__dict__")
            else str(config)
        )

        cache_input = {
            "parts": parts_data,
            "sheet_width": sheet_width,
            "sheet_height": sheet_height,
            "config": config_data,
        }

        # Generate hash
        cache_str = str(sorted(cache_input.items()))
        return hashlib.md5(cache_str.encode()).hexdigest()

    def get(
        self, parts: list, sheet_width: float, sheet_height: float, config: Any = None
    ) -> Any | None:
        """Get cached nesting result if available."""
        cache_key = self._generate_cache_key(parts, sheet_width, sheet_height, config)

        with self._cache_lock:
            # Check memory cache first
            if cache_key in self._memory_cache:
                logger.debug(f"Cache hit (memory): {cache_key[:8]}")
                return self._memory_cache[cache_key]

            # Check disk cache
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            if cache_file.exists():
                try:
                    with open(cache_file, "rb") as f:
                        result = pickle.load(f)

                    # Add to memory cache
                    self._memory_cache[cache_key] = result
                    logger.debug(f"Cache hit (disk): {cache_key[:8]}")
                    return result
                except Exception as e:
                    logger.warning(f"Failed to load cache file {cache_file}: {e}")
                    cache_file.unlink(missing_ok=True)

        return None

    def put(
        self,
        parts: list,
        sheet_width: float,
        sheet_height: float,
        result: Any,
        config: Any = None,
    ) -> None:
        """Store nesting result in cache."""
        cache_key = self._generate_cache_key(parts, sheet_width, sheet_height, config)

        with self._cache_lock:
            # Store in memory cache
            self._memory_cache[cache_key] = result

            # Limit memory cache size
            if len(self._memory_cache) > self.max_cache_size:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(self._memory_cache))
                del self._memory_cache[oldest_key]

            # Store in disk cache
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            try:
                with open(cache_file, "wb") as f:
                    pickle.dump(result, f)
                logger.debug(f"Cached result: {cache_key[:8]}")
            except Exception as e:
                logger.warning(f"Failed to save cache file {cache_file}: {e}")

    def clear(self) -> None:
        """Clear all cached results."""
        with self._cache_lock:
            self._memory_cache.clear()

            # Clear disk cache
            for cache_file in self.cache_dir.glob("*.pkl"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete cache file {cache_file}: {e}")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        disk_files = list(self.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in disk_files)

        return {
            "memory_entries": len(self._memory_cache),
            "disk_entries": len(disk_files),
            "total_disk_size_mb": total_size / 1024 / 1024,
            "cache_directory": str(self.cache_dir),
        }


# Global cache instance
_global_cache = NestingCache()


def cached_nesting(func: Callable) -> Callable:
    """Decorator to cache nesting results."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract key parameters for caching
        if len(args) >= 3:
            parts, sheet_width, sheet_height = args[0], args[1], args[2]
            config = kwargs.get("config") or (args[3] if len(args) > 3 else None)

            # Check cache
            cached_result = _global_cache.get(parts, sheet_width, sheet_height, config)
            if cached_result is not None:
                return cached_result

            # Compute result
            result = func(*args, **kwargs)

            # Cache result
            _global_cache.put(parts, sheet_width, sheet_height, result, config)

            return result
        else:
            # Not enough args for caching, just call function
            return func(*args, **kwargs)

    return wrapper


class ParallelNestingProcessor:
    """Process nesting operations in parallel for improved performance."""

    def __init__(self, max_workers: int | None = None, use_processes: bool = False):
        self.max_workers = max_workers or min(4, multiprocessing.cpu_count())
        self.use_processes = use_processes

    def process_multiple_sheets(
        self, sheet_configs: list[dict], nesting_func: Callable
    ) -> list[Any]:
        """Process multiple sheet configurations in parallel."""
        if len(sheet_configs) <= 1:
            # No benefit from parallelization
            return [nesting_func(**config) for config in sheet_configs]

        executor_class = (
            ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor
        )

        with executor_class(max_workers=self.max_workers) as executor:
            futures = []
            for config in sheet_configs:
                future = executor.submit(nesting_func, **config)
                futures.append(future)

            results = []
            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=300)  # 5 minute timeout
                    results.append(result)
                except Exception as e:
                    logger.error(f"Parallel nesting failed for sheet {i}: {e}")
                    results.append(None)

            return results

    def process_part_batches(
        self, parts: list, batch_size: int, processing_func: Callable
    ) -> list[Any]:
        """Process parts in parallel batches."""
        if len(parts) <= batch_size:
            return [processing_func(parts)]

        # Split into batches
        batches = []
        for i in range(0, len(parts), batch_size):
            batch = parts[i : i + batch_size]
            batches.append(batch)

        executor_class = (
            ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor
        )

        with executor_class(max_workers=self.max_workers) as executor:
            futures = []
            for batch in batches:
                future = executor.submit(processing_func, batch)
                futures.append(future)

            results = []
            for future in futures:
                try:
                    result = future.result(timeout=180)  # 3 minute timeout per batch
                    results.append(result)
                except Exception as e:
                    logger.error(f"Parallel batch processing failed: {e}")
                    results.append(None)

            return [r for r in results if r is not None]


def parallel_nesting(max_workers: int | None = None, use_processes: bool = False):
    """Decorator to enable parallel processing for nesting operations."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if parallel processing would be beneficial
            parts = args[0] if args else []
            if len(parts) < 50:  # Not worth parallelizing small datasets
                return func(*args, **kwargs)

            processor = ParallelNestingProcessor(max_workers, use_processes)

            # For very large datasets, process in batches
            if len(parts) > 1000:
                batch_size = len(parts) // processor.max_workers

                def batch_func(part_batch):
                    batch_args = (part_batch,) + args[1:]
                    return func(*batch_args, **kwargs)

                batch_results = processor.process_part_batches(
                    parts, batch_size, batch_func
                )

                # Combine results from all batches
                combined_result = []
                for batch_result in batch_results:
                    if isinstance(batch_result, list):
                        combined_result.extend(batch_result)
                    else:
                        combined_result.append(batch_result)

                return combined_result
            else:
                return func(*args, **kwargs)

        return wrapper

    return decorator


class MemoryOptimizer:
    """Optimize memory usage for large nesting operations."""

    @staticmethod
    def optimize_part_data(parts: list) -> list:
        """Optimize part data structures to reduce memory usage."""
        optimized_parts = []

        for part in parts:
            # Create minimal part representation
            if hasattr(part, "__dict__"):
                # Keep only essential attributes
                essential_attrs = [
                    "id",
                    "width",
                    "height",
                    "can_rotate",
                    "x",
                    "y",
                    "rotation_deg",
                    "sheet_index",
                ]
                optimized_part = type("OptimizedPart", (), {})()

                for attr in essential_attrs:
                    if hasattr(part, attr):
                        setattr(optimized_part, attr, getattr(part, attr))

                optimized_parts.append(optimized_part)
            else:
                optimized_parts.append(part)

        return optimized_parts

    @staticmethod
    def cleanup_intermediate_data(data_structures: list) -> None:
        """Clean up intermediate data structures to free memory."""
        for ds in data_structures:
            if hasattr(ds, "clear"):
                ds.clear()
            elif isinstance(ds, list):
                ds.clear()
            elif isinstance(ds, dict):
                ds.clear()


def memory_optimized(func: Callable) -> Callable:
    """Decorator to optimize memory usage during nesting operations."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Optimize input data
        if args and hasattr(args[0], "__len__"):
            parts = args[0]
            if len(parts) > 500:  # Only optimize for larger datasets
                optimized_parts = MemoryOptimizer.optimize_part_data(parts)
                args = (optimized_parts,) + args[1:]

        # Call function
        result = func(*args, **kwargs)

        # Clean up if dealing with large datasets
        if args and hasattr(args[0], "__len__") and len(args[0]) > 500:
            # Force garbage collection for large datasets
            import gc

            gc.collect()

        return result

    return wrapper


# Convenience functions for cache management


def clear_nesting_cache() -> None:
    """Clear the global nesting cache."""
    _global_cache.clear()
    logger.info("Nesting cache cleared")


def get_cache_stats() -> dict[str, Any]:
    """Get statistics about the nesting cache."""
    return _global_cache.get_cache_stats()


def configure_cache(cache_dir: str | None = None, max_cache_size: int = 100) -> None:
    """Configure the global nesting cache."""
    global _global_cache
    _global_cache = NestingCache(cache_dir, max_cache_size)
    logger.info(f"Cache configured: {cache_dir}, max size: {max_cache_size}")


# Performance monitoring for the new features


@performance_monitor("Cache Operation", threshold_seconds=0.1)
def _cache_operation_wrapper(operation: Callable) -> Any:
    """Wrapper for cache operations to monitor performance."""
    return operation()


@performance_monitor("Parallel Processing", threshold_seconds=5.0)
def _parallel_processing_wrapper(operation: Callable) -> Any:
    """Wrapper for parallel processing operations to monitor performance."""
    return operation()
