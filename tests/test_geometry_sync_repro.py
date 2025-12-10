import pytest
from unittest.mock import MagicMock, patch
from SquatchCut.core import geometry_sync

def test_sync_source_panels_handles_stale_object_gracefully():
    # Setup mocks
    mock_app = MagicMock()
    mock_doc = MagicMock()
    mock_doc.Name = "SquatchCut"
    mock_app.ActiveDocument = mock_doc

    # Stale object
    class StaleWrapper:
        Name = "StalePanel"
        @property
        def Shape(self):
            raise ReferenceError("Cannot access attribute 'Shape' of deleted object")

    stale_obj = StaleWrapper()

    # Valid object
    valid_obj = MagicMock()
    valid_obj.Name = "ValidPanel"
    valid_obj.Shape.Vertexes = []

    with patch("SquatchCut.core.geometry_sync.App", mock_app), \
         patch("SquatchCut.core.geometry_sync.Gui", MagicMock()), \
         patch("SquatchCut.core.session.get_panels", return_value=["dummy_panel"]), \
         patch("SquatchCut.core.session_state.get_sheet_size", return_value=(1000, 1000)), \
         patch("SquatchCut.core.logger.warning") as mock_log_warning, \
         patch("SquatchCut.core.session.get_source_panel_objects") as mock_get_objects, \
         patch("SquatchCut.core.view_controller.show_source_view") as mock_show_view:

        # Initially return stale object
        mock_get_objects.return_value = [stale_obj]

        # When show_source_view is called, update return value to valid object
        def side_effect(*args, **kwargs):
            mock_get_objects.return_value = [valid_obj]

        mock_show_view.side_effect = side_effect

        geometry_sync.sync_source_panels_to_document()

        # Verify show_source_view was called
        mock_show_view.assert_called_once()

        # Verify the specific warning was NOT logged
        for call in mock_log_warning.call_args_list:
            assert "Failed to inspect source panel vertices" not in call[0][0]
