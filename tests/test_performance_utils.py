"""Tests for performance utilities."""

import pytest
import time
from unittest.mock import patch, MagicMock

from SquatchCut.core.performance_utils import (
    performance_monitor,
    batch_process,
    validate_large_dataset_limits,
    estimate_memory_usage,
    check_system_resources,
    ProgressTracker,
    optimize_for_large_datasets,
)


class TestPerformanceMonitor:
    """Test performance monitoring decorator."""

    def test_performance_monitor_fast_operation(self):
        """Test that fast operations don't trigger warnings."""
        with patch("SquatchCut.core.performance_utils.logger") as mock_logger:

            @performance_monitor("test_operation", threshold_seconds=1.0)
            def fast_function():
                return "result"

            result = fast_function()

            assert result == "result"
            mock_logger.warning.assert_not_called()
            mock_logger.debug.assert_called_once()

    def test_performance_monitor_slow_operation(self):
        """Test that slow operations trigger warnings."""
        with patch("SquatchCut.core.performance_utils.logger") as mock_logger:

            @performance_monitor("test_operation", threshold_seconds=0.01)
            def slow_function():
                time.sleep(0.02)
                return "result"

            result = slow_function()

            assert result == "result"
            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "Slow operation detected" in warning_call
            assert "test_operation" in warning_call

    def test_performance_monitor_with_exception(self):
        """Test that performance monitor works even when function raises exception."""
        with patch("SquatchCut.core.performance_utils.logger") as mock_logger:

            @performance_monitor("test_operation", threshold_seconds=0.01)
            def failing_function():
                time.sleep(0.02)
                raise ValueError("Test error")

            with pytest.raises(ValueError, match="Test error"):
                failing_function()

            # Should still log the slow operation
            mock_logger.warning.assert_called_once()


class TestBatchProcessing:
    """Test batch processing utilities."""

    def test_batch_process_small_dataset(self):
        """Test batch processing with small dataset."""
        items = list(range(10))
        batches = list(batch_process(items, batch_size=3))

        assert len(batches) == 4
        assert batches[0] == [0, 1, 2]
        assert batches[1] == [3, 4, 5]
        assert batches[2] == [6, 7, 8]
        assert batches[3] == [9]

    def test_batch_process_with_progress_callback(self):
        """Test batch processing with progress callback."""
        items = list(range(10))
        progress_calls = []

        def progress_callback(current, total):
            progress_calls.append((current, total))

        batches = list(
            batch_process(items, batch_size=3, progress_callback=progress_callback)
        )

        assert len(batches) == 4
        assert len(progress_calls) == 4
        assert progress_calls[0] == (3, 10)
        assert progress_calls[1] == (6, 10)
        assert progress_calls[2] == (9, 10)
        assert progress_calls[3] == (10, 10)

    def test_batch_process_empty_dataset(self):
        """Test batch processing with empty dataset."""
        items = []
        batches = list(batch_process(items, batch_size=5))

        assert len(batches) == 0


class TestDatasetValidation:
    """Test dataset size validation."""

    def test_validate_large_dataset_limits_normal_size(self):
        """Test validation with normal dataset size."""
        # Should not raise exception
        validate_large_dataset_limits(100, max_parts=1000)

    def test_validate_large_dataset_limits_too_large(self):
        """Test validation with oversized dataset."""
        with pytest.raises(ValueError, match="Dataset too large"):
            validate_large_dataset_limits(1500, max_parts=1000)

    def test_validate_large_dataset_limits_warning_threshold(self):
        """Test validation with dataset near warning threshold."""
        with patch("SquatchCut.core.performance_utils.logger") as mock_logger:
            validate_large_dataset_limits(600, max_parts=1000)

            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "Large dataset detected" in warning_call

    def test_estimate_memory_usage(self):
        """Test memory usage estimation."""
        usage = estimate_memory_usage(100)
        assert usage > 0
        assert isinstance(usage, int)

        # Larger datasets should use more memory
        usage_large = estimate_memory_usage(1000)
        assert usage_large > usage

    def test_check_system_resources_small_dataset(self):
        """Test system resource check with small dataset."""
        with patch("SquatchCut.core.performance_utils.logger") as mock_logger:
            check_system_resources(100)

            # Should not log anything for small datasets
            mock_logger.info.assert_not_called()
            mock_logger.warning.assert_not_called()

    def test_check_system_resources_large_dataset(self):
        """Test system resource check with large dataset."""
        with patch("SquatchCut.core.performance_utils.logger") as mock_logger:
            check_system_resources(2000)

            mock_logger.info.assert_called_once()
            info_call = mock_logger.info.call_args[0][0]
            assert "Processing 2000 parts" in info_call

    def test_check_system_resources_very_large_dataset(self):
        """Test system resource check with very large dataset."""
        with patch("SquatchCut.core.performance_utils.logger") as mock_logger:
            check_system_resources(6000)

            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "Very large dataset" in warning_call


class TestProgressTracker:
    """Test progress tracking functionality."""

    def test_progress_tracker_basic_functionality(self):
        """Test basic progress tracking."""
        with patch("SquatchCut.core.performance_utils.logger") as mock_logger:
            tracker = ProgressTracker(100, "Test Operation")

            # Update progress
            tracker.update(10)
            tracker.update(20)

            # Finish
            tracker.finish()

            mock_logger.info.assert_called()
            finish_call = mock_logger.info.call_args[0][0]
            assert "Test Operation completed" in finish_call
            assert "30 items" in finish_call

    def test_progress_tracker_periodic_reporting(self):
        """Test periodic progress reporting."""
        with patch("SquatchCut.core.performance_utils.logger") as mock_logger:
            with patch("time.time") as mock_time:
                # Mock time to trigger periodic reporting
                mock_time.side_effect = [
                    0,
                    0,
                    6,
                    6,
                    12,
                ]  # Start, update, report trigger, update, finish

                tracker = ProgressTracker(100, "Test Operation")
                tracker.report_interval = 5.0  # 5 second intervals

                tracker.update(25)  # Should trigger report
                tracker.update(25)  # Should not trigger report yet

                # Should have logged progress
                assert mock_logger.info.call_count >= 1

    def test_progress_tracker_zero_total(self):
        """Test progress tracker with zero total items."""
        with patch("SquatchCut.core.performance_utils.logger") as mock_logger:
            tracker = ProgressTracker(0, "Empty Operation")
            tracker.update(1)
            tracker.finish()

            # Should handle gracefully
            mock_logger.info.assert_called()


class TestOptimizeForLargeDatasets:
    """Test large dataset optimization decorator."""

    def test_optimize_for_large_datasets_small_data(self):
        """Test decorator with small dataset."""
        with patch(
            "SquatchCut.core.performance_utils.check_system_resources"
        ) as mock_check:

            @optimize_for_large_datasets
            def process_data(items):
                return len(items)

            result = process_data([1, 2, 3])

            assert result == 3
            mock_check.assert_not_called()

    def test_optimize_for_large_datasets_large_data(self):
        """Test decorator with large dataset."""
        with patch(
            "SquatchCut.core.performance_utils.check_system_resources"
        ) as mock_check:
            with patch(
                "SquatchCut.core.performance_utils.validate_large_dataset_limits"
            ) as mock_validate:

                @optimize_for_large_datasets
                def process_data(items):
                    return len(items)

                large_data = list(range(200))
                result = process_data(large_data)

                assert result == 200
                mock_check.assert_called_once_with(200)
                mock_validate.assert_called_once_with(200)

    def test_optimize_for_large_datasets_no_list_args(self):
        """Test decorator with non-list arguments."""
        with patch(
            "SquatchCut.core.performance_utils.check_system_resources"
        ) as mock_check:

            @optimize_for_large_datasets
            def process_data(value):
                return value * 2

            result = process_data(42)

            assert result == 84
            mock_check.assert_not_called()

    def test_optimize_for_large_datasets_multiple_lists(self):
        """Test decorator with multiple list arguments."""
        with patch(
            "SquatchCut.core.performance_utils.check_system_resources"
        ) as mock_check:

            @optimize_for_large_datasets
            def process_data(items1, items2):
                return len(items1) + len(items2)

            large_data = list(range(150))
            small_data = [1, 2, 3]
            result = process_data(large_data, small_data)

            assert result == 153
            # Should check the first large dataset found
            mock_check.assert_called_once_with(150)
