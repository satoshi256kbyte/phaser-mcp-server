"""Tests for utility functions.

This module contains tests for the utility functions in the
phaser_mcp_server.utils module.
"""

from unittest.mock import MagicMock, patch

from phaser_mcp_server.utils import get_memory_usage


class TestMemoryUsage:
    """Tests for memory usage utility functions."""

    def test_get_memory_usage_with_psutil(self):
        """Test get_memory_usage when psutil is available."""
        # Mock psutil.Process and its memory_info method
        mock_process = MagicMock()
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 104857600  # 100 MB in bytes
        mock_process.memory_info.return_value = mock_memory_info

        # Patch psutil.Process to return our mock
        with patch("psutil.Process", return_value=mock_process):
            # Call the function
            memory_usage = get_memory_usage()

            # Verify the result (should be 100 MB)
            assert memory_usage == 100.0

    def test_get_memory_usage_without_psutil(self):
        """Test get_memory_usage when psutil is not available."""
        # Mock the psutil module to raise ImportError
        with patch.dict("sys.modules", {"psutil": None}):
            # Call the function
            memory_usage = get_memory_usage()

            # Verify the result (should be None)
            assert memory_usage is None

    def test_get_memory_usage_with_attribute_error(self):
        """Test get_memory_usage when an AttributeError occurs."""
        # Mock psutil.Process but make memory_info raise AttributeError
        mock_process = MagicMock()
        mock_process.memory_info.side_effect = AttributeError

        # Patch psutil.Process to return our mock
        with patch("psutil.Process", return_value=mock_process):
            # Call the function
            memory_usage = get_memory_usage()

            # Verify the result (should be None)
            assert memory_usage is None
