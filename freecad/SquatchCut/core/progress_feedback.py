"""Progress feedback system for long-running nesting operations.

This module provides progress reporting, cancellation support, and user feedback
for complex shape-based nesting operations that may take significant time.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from SquatchCut.core import logger


class OperationStatus(Enum):
    """Status of a long-running operation."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ProgressStage(Enum):
    """Stages of a nesting operation for progress reporting."""

    INITIALIZING = "initializing"
    ANALYZING_SHAPES = "analyzing_shapes"
    SIMPLIFYING_GEOMETRY = "simplifying_geometry"
    PLACING_SHAPES = "placing_shapes"
    OPTIMIZING_LAYOUT = "optimizing_layout"
    CALCULATING_RESULTS = "calculating_results"
    FINALIZING = "finalizing"


@dataclass
class ProgressUpdate:
    """Progress update information for UI feedback."""

    operation_id: str
    stage: ProgressStage
    progress_percent: float  # 0.0 to 100.0
    current_item: int
    total_items: int
    current_description: str
    elapsed_time: float
    estimated_remaining: float | None = None
    can_cancel: bool = True
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Ensure progress percent is within valid range."""
        self.progress_percent = max(0.0, min(100.0, self.progress_percent))


@dataclass
class OperationResult:
    """Result of a completed operation with progress tracking."""

    operation_id: str
    status: OperationStatus
    result_data: Any | None = None
    error_message: str | None = None
    total_time: float = 0.0
    final_progress: ProgressUpdate | None = None


# Type alias for progress callback function
ProgressCallback = Callable[[ProgressUpdate], None]
CancellationCheck = Callable[[], bool]


class ProgressTracker:
    """Tracks progress for a single long-running operation."""

    def __init__(
        self,
        operation_id: str,
        total_items: int,
        progress_callback: ProgressCallback | None = None,
        cancellation_check: CancellationCheck | None = None,
    ):
        """Initialize progress tracker.

        Args:
            operation_id: Unique identifier for the operation
            total_items: Total number of items to process
            progress_callback: Function to call with progress updates
            cancellation_check: Function to check if operation should be cancelled
        """
        self.operation_id = operation_id
        self.total_items = total_items
        self.progress_callback = progress_callback
        self.cancellation_check = cancellation_check

        self.start_time = time.time()
        self.current_item = 0
        self.current_stage = ProgressStage.INITIALIZING
        self.current_description = "Starting operation..."
        self.warnings: list[str] = []
        self.cancelled = False

        # Stage weights for overall progress calculation
        self.stage_weights = {
            ProgressStage.INITIALIZING: 5,
            ProgressStage.ANALYZING_SHAPES: 10,
            ProgressStage.SIMPLIFYING_GEOMETRY: 15,
            ProgressStage.PLACING_SHAPES: 50,
            ProgressStage.OPTIMIZING_LAYOUT: 15,
            ProgressStage.CALCULATING_RESULTS: 3,
            ProgressStage.FINALIZING: 2,
        }

        self._stage_progress = 0.0  # Progress within current stage (0.0-1.0)

        # Send initial progress update
        self._send_progress_update()

    def set_stage(self, stage: ProgressStage, description: str = "") -> None:
        """Set the current operation stage.

        Args:
            stage: The new stage
            description: Description of what's happening in this stage
        """
        self.current_stage = stage
        self.current_description = description or stage.value.replace("_", " ").title()
        self._stage_progress = 0.0

        logger.info(
            f"[Progress] {self.operation_id}: {self.current_stage.value} - {self.current_description}"
        )
        self._send_progress_update()

    def update_progress(
        self,
        current_item: int | None = None,
        stage_progress: float | None = None,
        description: str | None = None,
    ) -> bool:
        """Update progress within the current stage.

        Args:
            current_item: Current item number being processed
            stage_progress: Progress within current stage (0.0-1.0)
            description: Updated description

        Returns:
            True if operation should continue, False if cancelled
        """
        if current_item is not None:
            self.current_item = current_item
            # Calculate stage progress from item count if not explicitly provided
            if stage_progress is None and self.total_items > 0:
                self._stage_progress = min(1.0, current_item / self.total_items)

        if stage_progress is not None:
            self._stage_progress = max(0.0, min(1.0, stage_progress))

        if description is not None:
            self.current_description = description

        # Check for cancellation
        if self.cancellation_check and self.cancellation_check():
            self.cancelled = True
            logger.info(f"[Progress] {self.operation_id}: Operation cancelled by user")
            return False

        self._send_progress_update()
        return True

    def add_warning(self, warning: str) -> None:
        """Add a warning message to the progress update."""
        self.warnings.append(warning)
        logger.warning(f"[Progress] {self.operation_id}: {warning}")
        self._send_progress_update()

    def finish(self, success: bool = True, error_message: str | None = None) -> None:
        """Mark the operation as finished."""
        if success and not self.cancelled:
            self.set_stage(ProgressStage.FINALIZING, "Operation completed successfully")
            self._stage_progress = 1.0
        elif self.cancelled:
            self.current_description = "Operation cancelled"
        else:
            self.current_description = (
                f"Operation failed: {error_message or 'Unknown error'}"
            )

        self._send_progress_update()

    def _calculate_overall_progress(self) -> float:
        """Calculate overall progress percentage across all stages."""
        total_weight = sum(self.stage_weights.values())
        completed_weight = 0.0

        # Add weight for completed stages
        stage_order = list(ProgressStage)
        current_stage_index = stage_order.index(self.current_stage)

        for i, stage in enumerate(stage_order):
            if i < current_stage_index:
                completed_weight += self.stage_weights[stage]
            elif i == current_stage_index:
                completed_weight += self.stage_weights[stage] * self._stage_progress
                break

        return (completed_weight / total_weight) * 100.0

    def _estimate_remaining_time(self) -> float | None:
        """Estimate remaining time based on current progress."""
        elapsed = time.time() - self.start_time
        progress_percent = self._calculate_overall_progress()

        if progress_percent > 5.0 and elapsed > 1.0:  # Need some progress to estimate
            total_estimated = elapsed / (progress_percent / 100.0)
            remaining = total_estimated - elapsed
            return max(0.0, remaining)

        return None

    def _send_progress_update(self) -> None:
        """Send progress update to callback if available."""
        if not self.progress_callback:
            return

        elapsed = time.time() - self.start_time
        progress_percent = self._calculate_overall_progress()
        estimated_remaining = self._estimate_remaining_time()

        update = ProgressUpdate(
            operation_id=self.operation_id,
            stage=self.current_stage,
            progress_percent=progress_percent,
            current_item=self.current_item,
            total_items=self.total_items,
            current_description=self.current_description,
            elapsed_time=elapsed,
            estimated_remaining=estimated_remaining,
            can_cancel=not self.cancelled,
            warnings=self.warnings.copy(),
        )

        try:
            self.progress_callback(update)
        except Exception as e:
            logger.error(f"[Progress] Error in progress callback: {e}")


class ProgressManager:
    """Manages multiple concurrent progress tracking operations."""

    def __init__(self):
        """Initialize progress manager."""
        self.active_operations: dict[str, ProgressTracker] = {}
        self.completed_operations: list[OperationResult] = []
        self._lock = threading.Lock()
        self._operation_counter = 0

    def start_operation(
        self,
        operation_name: str,
        total_items: int,
        progress_callback: ProgressCallback | None = None,
        cancellation_check: CancellationCheck | None = None,
    ) -> str:
        """Start tracking a new operation.

        Args:
            operation_name: Human-readable name for the operation
            total_items: Total number of items to process
            progress_callback: Function to call with progress updates
            cancellation_check: Function to check for cancellation

        Returns:
            Operation ID for tracking
        """
        with self._lock:
            self._operation_counter += 1
            operation_id = f"{operation_name}_{self._operation_counter}"

            tracker = ProgressTracker(
                operation_id=operation_id,
                total_items=total_items,
                progress_callback=progress_callback,
                cancellation_check=cancellation_check,
            )

            self.active_operations[operation_id] = tracker

            logger.info(
                f"[Progress] Started tracking operation: {operation_id} ({total_items} items)"
            )
            return operation_id

    def get_tracker(self, operation_id: str) -> ProgressTracker | None:
        """Get the progress tracker for an operation."""
        with self._lock:
            return self.active_operations.get(operation_id)

    def finish_operation(
        self,
        operation_id: str,
        success: bool = True,
        result_data: Any | None = None,
        error_message: str | None = None,
    ) -> OperationResult:
        """Finish tracking an operation.

        Args:
            operation_id: ID of the operation to finish
            success: Whether the operation completed successfully
            result_data: Result data from the operation
            error_message: Error message if operation failed

        Returns:
            OperationResult with final status
        """
        with self._lock:
            tracker = self.active_operations.pop(operation_id, None)

            if not tracker:
                logger.warning(f"[Progress] Unknown operation ID: {operation_id}")
                return OperationResult(
                    operation_id=operation_id,
                    status=OperationStatus.FAILED,
                    error_message="Unknown operation",
                )

            # Finish the tracker
            tracker.finish(success, error_message)

            # Determine final status
            if tracker.cancelled:
                status = OperationStatus.CANCELLED
            elif success:
                status = OperationStatus.COMPLETED
            else:
                status = OperationStatus.FAILED

            # Create result
            result = OperationResult(
                operation_id=operation_id,
                status=status,
                result_data=result_data,
                error_message=error_message,
                total_time=time.time() - tracker.start_time,
                final_progress=ProgressUpdate(
                    operation_id=operation_id,
                    stage=tracker.current_stage,
                    progress_percent=(
                        100.0 if success else tracker._calculate_overall_progress()
                    ),
                    current_item=tracker.current_item,
                    total_items=tracker.total_items,
                    current_description=tracker.current_description,
                    elapsed_time=time.time() - tracker.start_time,
                    can_cancel=False,
                    warnings=tracker.warnings,
                ),
            )

            self.completed_operations.append(result)

            logger.info(
                f"[Progress] Finished operation: {operation_id} ({status.value})"
            )
            return result

    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel an active operation.

        Args:
            operation_id: ID of the operation to cancel

        Returns:
            True if operation was cancelled, False if not found
        """
        with self._lock:
            tracker = self.active_operations.get(operation_id)
            if tracker:
                tracker.cancelled = True
                logger.info(f"[Progress] Cancelled operation: {operation_id}")
                return True
            return False

    def get_active_operations(self) -> list[str]:
        """Get list of active operation IDs."""
        with self._lock:
            return list(self.active_operations.keys())

    def get_operation_summary(self) -> dict[str, Any]:
        """Get summary of all operations."""
        with self._lock:
            active_count = len(self.active_operations)
            completed_count = len(self.completed_operations)

            if completed_count > 0:
                success_count = sum(
                    1
                    for op in self.completed_operations
                    if op.status == OperationStatus.COMPLETED
                )
                cancelled_count = sum(
                    1
                    for op in self.completed_operations
                    if op.status == OperationStatus.CANCELLED
                )
                failed_count = sum(
                    1
                    for op in self.completed_operations
                    if op.status == OperationStatus.FAILED
                )

                avg_time = (
                    sum(op.total_time for op in self.completed_operations)
                    / completed_count
                )
            else:
                success_count = cancelled_count = failed_count = 0
                avg_time = 0.0

            return {
                "active_operations": active_count,
                "completed_operations": completed_count,
                "success_rate": (
                    success_count / completed_count if completed_count > 0 else 0.0
                ),
                "cancellation_rate": (
                    cancelled_count / completed_count if completed_count > 0 else 0.0
                ),
                "failure_rate": (
                    failed_count / completed_count if completed_count > 0 else 0.0
                ),
                "average_completion_time": avg_time,
            }


# Global progress manager instance
_global_progress_manager: ProgressManager | None = None


def get_progress_manager() -> ProgressManager:
    """Get the global progress manager instance."""
    global _global_progress_manager
    if _global_progress_manager is None:
        _global_progress_manager = ProgressManager()
    return _global_progress_manager


def with_progress_tracking(
    operation_name: str,
    total_items: int,
    progress_callback: ProgressCallback | None = None,
    cancellation_check: CancellationCheck | None = None,
):
    """Decorator for adding progress tracking to functions.

    Usage:
        @with_progress_tracking("shape_nesting", total_items=10)
        def nest_shapes(shapes, progress_tracker=None):
            for i, shape in enumerate(shapes):
                if not progress_tracker.update_progress(current_item=i):
                    return None  # Cancelled
                # ... process shape
            return result
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            manager = get_progress_manager()
            operation_id = manager.start_operation(
                operation_name, total_items, progress_callback, cancellation_check
            )

            tracker = manager.get_tracker(operation_id)

            try:
                # Add tracker to function arguments
                result = func(*args, progress_tracker=tracker, **kwargs)
                manager.finish_operation(operation_id, success=True, result_data=result)
                return result
            except Exception as e:
                manager.finish_operation(
                    operation_id, success=False, error_message=str(e)
                )
                raise

        return wrapper

    return decorator
