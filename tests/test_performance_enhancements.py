"""Tests for performance enhancement features."""

import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch

from SquatchCut.core.nesting import Part, PlacedPart
from SquatchCut.core.performance_utils import (
    MemoryOptimizer,
    NestingCache,
    ParallelNestingProcessor,
    cached_nesting,
    clear_nesting_cache,
    configure_cache,
    get_cache_stats,
    memory_optimized,
    parallel_nesting,
)


class TestNestingCache:
    """Test nesting cache functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use temporary directory for cache
        self.temp_dir = tempfile.mkdtemp()
        self.cache = NestingCache(cache_dir=self.temp_dir, max_cache_size=5)

        # Test data
        self.parts = [
            Part(id="A", width=100, height=50),
            Part(id="B", width=80, height=60),
        ]
        self.sheet_width = 300
        self.sheet_height = 200
        self.result = [
            PlacedPart(id="A", x=0, y=0, width=100, height=50, sheet_index=0),
            PlacedPart(id="B", x=110, y=0, width=80, height=60, sheet_index=0),
        ]

    def teardown_method(self):
        """Clean up test fixtures."""
        self.cache.clear()

    def test_cache_initialization(self):
        """Test cache initialization."""
        assert self.cache.cache_dir == Path(self.temp_dir)
        assert self.cache.max_cache_size == 5
        assert len(self.cache._memory_cache) == 0

    def test_generate_cache_key(self):
        """Test cache key generation."""
        key1 = self.cache._generate_cache_key(
            self.parts, self.sheet_width, self.sheet_height
        )
        key2 = self.cache._generate_cache_key(
            self.parts, self.sheet_width, self.sheet_height
        )

        # Same inputs should generate same key
        assert key1 == key2
        assert len(key1) == 32  # MD5 hash length

        # Different inputs should generate different keys
        different_parts = [Part(id="C", width=120, height=70)]
        key3 = self.cache._generate_cache_key(
            different_parts, self.sheet_width, self.sheet_height
        )
        assert key1 != key3

    def test_cache_put_and_get_memory(self):
        """Test putting and getting from memory cache."""
        # Put result in cache
        self.cache.put(self.parts, self.sheet_width, self.sheet_height, self.result)

        # Get result from cache
        cached_result = self.cache.get(self.parts, self.sheet_width, self.sheet_height)

        assert cached_result is not None
        assert len(cached_result) == len(self.result)
        assert cached_result[0].id == self.result[0].id

    def test_cache_miss(self):
        """Test cache miss scenario."""
        # Try to get non-existent result
        cached_result = self.cache.get(self.parts, self.sheet_width, self.sheet_height)
        assert cached_result is None

    def test_cache_put_and_get_disk(self):
        """Test putting and getting from disk cache."""
        # Put result in cache
        self.cache.put(self.parts, self.sheet_width, self.sheet_height, self.result)

        # Clear memory cache to force disk read
        self.cache._memory_cache.clear()

        # Get result from cache (should read from disk)
        cached_result = self.cache.get(self.parts, self.sheet_width, self.sheet_height)

        assert cached_result is not None
        assert len(cached_result) == len(self.result)

    def test_cache_size_limit(self):
        """Test cache size limiting."""
        # Fill cache beyond limit
        for i in range(10):
            parts = [Part(id=f"Part_{i}", width=100, height=50)]
            result = [
                PlacedPart(
                    id=f"Part_{i}", x=0, y=0, width=100, height=50, sheet_index=0
                )
            ]
            self.cache.put(parts, 300, 200, result)

        # Memory cache should be limited
        assert len(self.cache._memory_cache) <= self.cache.max_cache_size

    def test_cache_clear(self):
        """Test cache clearing."""
        # Put something in cache
        self.cache.put(self.parts, self.sheet_width, self.sheet_height, self.result)

        # Clear cache
        self.cache.clear()

        # Should be empty
        assert len(self.cache._memory_cache) == 0

        # Should not find cached result
        cached_result = self.cache.get(self.parts, self.sheet_width, self.sheet_height)
        assert cached_result is None

    def test_cache_stats(self):
        """Test cache statistics."""
        # Put some items in cache
        self.cache.put(self.parts, self.sheet_width, self.sheet_height, self.result)

        stats = self.cache.get_cache_stats()

        assert "memory_entries" in stats
        assert "disk_entries" in stats
        assert "total_disk_size_mb" in stats
        assert "cache_directory" in stats

        assert stats["memory_entries"] >= 1
        assert stats["cache_directory"] == str(self.cache.cache_dir)

    def test_cache_thread_safety(self):
        """Test cache thread safety."""
        results = []

        def cache_worker(worker_id):
            parts = [Part(id=f"Worker_{worker_id}", width=100, height=50)]
            result = [
                PlacedPart(
                    id=f"Worker_{worker_id}",
                    x=0,
                    y=0,
                    width=100,
                    height=50,
                    sheet_index=0,
                )
            ]

            # Put and get multiple times
            for i in range(10):
                self.cache.put(parts, 300, 200, result)
                cached = self.cache.get(parts, 300, 200)
                results.append(cached is not None)

        # Run multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All operations should succeed
        assert all(results)


class TestCachedNestingDecorator:
    """Test cached nesting decorator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.call_count = 0

        @cached_nesting
        def mock_nesting_function(parts, sheet_width, sheet_height, config=None):
            self.call_count += 1
            return [
                PlacedPart(id="test", x=0, y=0, width=100, height=50, sheet_index=0)
            ]

        self.mock_function = mock_nesting_function
        self.parts = [Part(id="A", width=100, height=50)]

    def teardown_method(self):
        """Clean up test fixtures."""
        clear_nesting_cache()

    def test_cached_nesting_first_call(self):
        """Test first call to cached function."""
        result = self.mock_function(self.parts, 300, 200)

        assert self.call_count == 1
        assert len(result) == 1
        assert result[0].id == "test"

    def test_cached_nesting_second_call(self):
        """Test second call uses cache."""
        # First call
        result1 = self.mock_function(self.parts, 300, 200)

        # Second call with same parameters
        result2 = self.mock_function(self.parts, 300, 200)

        # Function should only be called once
        assert self.call_count == 1

        # Results should be the same
        assert len(result1) == len(result2)
        assert result1[0].id == result2[0].id

    def test_cached_nesting_different_parameters(self):
        """Test different parameters don't use cache."""
        # First call
        result1 = self.mock_function(self.parts, 300, 200)

        # Second call with different parameters
        result2 = self.mock_function(self.parts, 400, 250)

        # Function should be called twice
        assert self.call_count == 2

    def test_cached_nesting_insufficient_args(self):
        """Test function with insufficient args for caching."""

        @cached_nesting
        def insufficient_args_function(arg1):
            self.call_count += 1
            return "result"

        result = insufficient_args_function("test")

        # Should still work, just without caching
        assert result == "result"
        assert self.call_count == 1


class TestParallelNestingProcessor:
    """Test parallel nesting processor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = ParallelNestingProcessor(max_workers=2, use_processes=False)
        self.call_count = 0

        def mock_nesting_func(**kwargs):
            self.call_count += 1
            time.sleep(0.1)  # Simulate work
            return f"result_{kwargs.get('sheet_id', 'unknown')}"

        self.mock_function = mock_nesting_func

    def test_processor_initialization(self):
        """Test processor initialization."""
        assert self.processor.max_workers == 2
        assert self.processor.use_processes is False

    def test_process_multiple_sheets_single_sheet(self):
        """Test processing single sheet (no parallelization)."""
        configs = [{"sheet_id": 1, "parts": []}]

        results = self.processor.process_multiple_sheets(configs, self.mock_function)

        assert len(results) == 1
        assert results[0] == "result_1"
        assert self.call_count == 1

    def test_process_multiple_sheets_parallel(self):
        """Test processing multiple sheets in parallel."""
        configs = [
            {"sheet_id": 1, "parts": []},
            {"sheet_id": 2, "parts": []},
            {"sheet_id": 3, "parts": []},
        ]

        start_time = time.time()
        results = self.processor.process_multiple_sheets(configs, self.mock_function)
        elapsed = time.time() - start_time

        assert len(results) == 3
        assert "result_1" in results
        assert "result_2" in results
        assert "result_3" in results
        assert self.call_count == 3

        # Should be faster than sequential (3 * 0.1 = 0.3s)
        assert elapsed < 0.25

    def test_process_part_batches_small_dataset(self):
        """Test processing small dataset (no batching)."""
        parts = [Part(id="A", width=100, height=50)]

        def batch_func(part_batch):
            return f"processed_{len(part_batch)}_parts"

        results = self.processor.process_part_batches(
            parts, batch_size=10, processing_func=batch_func
        )

        assert len(results) == 1
        assert results[0] == "processed_1_parts"

    def test_process_part_batches_large_dataset(self):
        """Test processing large dataset with batching."""
        parts = [Part(id=f"Part_{i}", width=100, height=50) for i in range(25)]

        def batch_func(part_batch):
            return f"processed_{len(part_batch)}_parts"

        results = self.processor.process_part_batches(
            parts, batch_size=10, processing_func=batch_func
        )

        # Should have 3 batches: 10, 10, 5
        assert len(results) == 3
        assert "processed_10_parts" in results
        assert "processed_5_parts" in results

    @patch("SquatchCut.core.performance_utils.logger")
    def test_process_with_exception(self, mock_logger):
        """Test handling exceptions in parallel processing."""

        def failing_func(**kwargs):
            if kwargs.get("sheet_id") == 2:
                raise ValueError("Test error")
            return f"result_{kwargs.get('sheet_id')}"

        configs = [
            {"sheet_id": 1, "parts": []},
            {"sheet_id": 2, "parts": []},  # Will fail
            {"sheet_id": 3, "parts": []},
        ]

        results = self.processor.process_multiple_sheets(configs, failing_func)

        assert len(results) == 3
        assert "result_1" in results
        assert None in results  # Failed task
        assert "result_3" in results

        # Should log error
        mock_logger.error.assert_called()


class TestParallelNestingDecorator:
    """Test parallel nesting decorator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.call_count = 0

        @parallel_nesting(max_workers=2)
        def mock_nesting_function(parts, sheet_width, sheet_height):
            self.call_count += 1
            return [
                PlacedPart(
                    id=f"part_{i}", x=i * 10, y=0, width=10, height=10, sheet_index=0
                )
                for i in range(len(parts))
            ]

        self.mock_function = mock_nesting_function

    def test_parallel_nesting_small_dataset(self):
        """Test parallel nesting with small dataset (no parallelization)."""
        parts = [Part(id=f"Part_{i}", width=50, height=50) for i in range(10)]

        result = self.mock_function(parts, 300, 200)

        # Should call function normally
        assert self.call_count == 1
        assert len(result) == 10

    def test_parallel_nesting_large_dataset(self):
        """Test parallel nesting with large dataset."""
        parts = [Part(id=f"Part_{i}", width=50, height=50) for i in range(1500)]

        result = self.mock_function(parts, 600, 400)

        # Should use parallel processing
        assert self.call_count > 1  # Multiple batch calls
        assert len(result) > 0  # Should have results


class TestMemoryOptimizer:
    """Test memory optimizer functionality."""

    def test_optimize_part_data(self):
        """Test part data optimization."""
        # Create parts with extra attributes
        parts = []
        for i in range(3):
            part = Part(id=f"Part_{i}", width=100, height=50)
            part.extra_data = f"extra_{i}"  # Add extra attribute
            part.large_object = list(range(1000))  # Add large object
            parts.append(part)

        optimized_parts = MemoryOptimizer.optimize_part_data(parts)

        assert len(optimized_parts) == 3

        # Should have essential attributes
        for i, opt_part in enumerate(optimized_parts):
            assert hasattr(opt_part, "id")
            assert hasattr(opt_part, "width")
            assert hasattr(opt_part, "height")
            assert opt_part.id == f"Part_{i}"
            assert opt_part.width == 100
            assert opt_part.height == 50

    def test_cleanup_intermediate_data(self):
        """Test cleanup of intermediate data structures."""
        # Create test data structures
        test_list = [1, 2, 3, 4, 5]
        test_dict = {"a": 1, "b": 2, "c": 3}
        test_set = {1, 2, 3}

        data_structures = [test_list, test_dict, test_set]

        MemoryOptimizer.cleanup_intermediate_data(data_structures)

        # Lists, dicts, and sets should be cleared
        assert len(test_list) == 0
        assert len(test_dict) == 0
        # Sets also have clear method, so they should be cleared too
        assert len(test_set) == 0


class TestMemoryOptimizedDecorator:
    """Test memory optimized decorator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.call_count = 0

        @memory_optimized
        def mock_nesting_function(parts, sheet_width, sheet_height):
            self.call_count += 1
            return [
                PlacedPart(
                    id=part.id,
                    x=0,
                    y=0,
                    width=part.width,
                    height=part.height,
                    sheet_index=0,
                )
                for part in parts
            ]

        self.mock_function = mock_nesting_function

    def test_memory_optimized_small_dataset(self):
        """Test memory optimization with small dataset."""
        parts = [Part(id=f"Part_{i}", width=50, height=50) for i in range(100)]

        result = self.mock_function(parts, 300, 200)

        assert self.call_count == 1
        assert len(result) == 100

    @patch("gc.collect")
    def test_memory_optimized_large_dataset(self, mock_gc_collect):
        """Test memory optimization with large dataset."""
        parts = [Part(id=f"Part_{i}", width=50, height=50) for i in range(600)]

        result = self.mock_function(parts, 600, 400)

        assert self.call_count == 1
        assert len(result) == 600

        # Should trigger garbage collection for large datasets
        mock_gc_collect.assert_called()


class TestCacheManagementFunctions:
    """Test cache management convenience functions."""

    def teardown_method(self):
        """Clean up after tests."""
        clear_nesting_cache()

    @patch("SquatchCut.core.performance_utils._global_cache")
    def test_clear_nesting_cache(self, mock_cache):
        """Test clearing global cache."""
        clear_nesting_cache()
        mock_cache.clear.assert_called_once()

    @patch("SquatchCut.core.performance_utils._global_cache")
    def test_get_cache_stats(self, mock_cache):
        """Test getting cache statistics."""
        mock_cache.get_cache_stats.return_value = {"memory_entries": 5}

        stats = get_cache_stats()

        assert stats == {"memory_entries": 5}
        mock_cache.get_cache_stats.assert_called_once()

    @patch("SquatchCut.core.performance_utils.logger")
    def test_configure_cache(self, mock_logger):
        """Test configuring cache."""
        configure_cache(cache_dir="/tmp/test", max_cache_size=50)

        # Should log configuration
        mock_logger.info.assert_called()


class TestPerformanceIntegration:
    """Integration tests for performance features."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parts = [
            Part(id=f"Part_{i}", width=50 + i * 5, height=40 + i * 3) for i in range(20)
        ]

    def teardown_method(self):
        """Clean up after tests."""
        clear_nesting_cache()

    def test_combined_optimizations(self):
        """Test combining multiple performance optimizations."""

        @cached_nesting
        @memory_optimized
        def optimized_nesting_function(parts, sheet_width, sheet_height):
            # Simulate nesting algorithm
            placed_parts = []
            x, y = 0, 0

            for part in parts:
                if x + part.width > sheet_width:
                    x = 0
                    y += 60  # Move to next row

                placed_parts.append(
                    PlacedPart(
                        id=part.id,
                        x=x,
                        y=y,
                        width=part.width,
                        height=part.height,
                        sheet_index=0,
                    )
                )
                x += part.width + 5

            return placed_parts

        # First call
        start_time = time.time()
        result1 = optimized_nesting_function(self.parts, 400, 300)
        first_call_time = time.time() - start_time

        # Second call (should use cache)
        start_time = time.time()
        result2 = optimized_nesting_function(self.parts, 400, 300)
        second_call_time = time.time() - start_time

        # Results should be identical
        assert len(result1) == len(result2)
        assert all(p1.id == p2.id for p1, p2 in zip(result1, result2))

        # Second call should be faster (cached). On CI, timing can be flaky,
        # so we allow a generous 50% threshold.
        assert second_call_time < first_call_time * 0.5

    def test_performance_monitoring_integration(self):
        """Test integration with performance monitoring."""
        from SquatchCut.core.performance_utils import performance_monitor

        @performance_monitor("Test Operation", threshold_seconds=0.01)
        @cached_nesting
        def monitored_function(parts, sheet_width, sheet_height):
            time.sleep(0.02)  # Simulate slow operation
            return []

        with patch("SquatchCut.core.performance_utils.logger") as mock_logger:
            result = monitored_function(self.parts, 400, 300)

        # Should log slow operation warning
        mock_logger.warning.assert_called()

        # Second call should be fast (cached) and not trigger warning
        mock_logger.reset_mock()

        with patch("SquatchCut.core.performance_utils.logger") as mock_logger:
            result2 = monitored_function(self.parts, 400, 300)

        # Should only log debug message for fast operation
        mock_logger.debug.assert_called()
        mock_logger.warning.assert_not_called()

    def test_cache_persistence_across_calls(self):
        """Test that cache persists across multiple function calls."""
        call_count = 0

        @cached_nesting
        def counting_function(parts, sheet_width, sheet_height):
            nonlocal call_count
            call_count += 1
            return [
                PlacedPart(id="test", x=0, y=0, width=100, height=50, sheet_index=0)
            ]

        # Multiple calls with same parameters
        for _ in range(5):
            result = counting_function(self.parts, 400, 300)

        # Function should only be called once
        assert call_count == 1

        # Different parameters should trigger new call
        result = counting_function(self.parts, 500, 350)
        assert call_count == 2
