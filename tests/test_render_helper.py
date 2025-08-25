import datetime as dt
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from render.render import RenderHelper
from config import DashboardConfig


class TestRenderHelper:
    """Test suite for RenderHelper class methods."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock DashboardConfig for testing."""
        config = MagicMock(spec=DashboardConfig)
        return config

    @pytest.fixture
    def render_helper(self, mock_config):
        """Create a RenderHelper instance with mocked config."""
        with patch("render.render.structlog.get_logger"):
            return RenderHelper(mock_config)

    def test_extend_list_shorter_list(self, render_helper):
        """Test extend_list when list is shorter than target length."""
        test_list = ["item1", "item2"]
        render_helper.extend_list(test_list, 5, "default")
        expected = ["item1", "item2", "default", "default", "default"]
        assert test_list == expected

    def test_extend_list_empty_list(self, render_helper):
        """Test extend_list with empty list."""
        test_list = []
        render_helper.extend_list(test_list, 3, "default")
        expected = ["default", "default", "default"]
        assert test_list == expected

    def test_extend_list_exact_length(self, render_helper):
        """Test extend_list when list is already the target length."""
        test_list = ["item1", "item2", "item3"]
        original_list = test_list.copy()
        render_helper.extend_list(test_list, 3, "default")
        assert test_list == original_list

    def test_extend_list_longer_list(self, render_helper):
        """Test extend_list when list is longer than target length."""
        test_list = ["item1", "item2", "item3", "item4", "item5"]
        original_list = test_list.copy()
        render_helper.extend_list(test_list, 3, "default")
        assert test_list == original_list

    def test_extend_list_zero_length(self, render_helper):
        """Test extend_list with zero target length."""
        test_list = ["item1", "item2"]
        original_list = test_list.copy()
        render_helper.extend_list(test_list, 0, "default")
        assert test_list == original_list

    def test_extend_list_different_default_values(self, render_helper):
        """Test extend_list with different default value types."""
        test_list = [1, 2]
        render_helper.extend_list(test_list, 4, 0)
        assert test_list == [1, 2, 0, 0]

    def test_get_short_time_24hour_format(self, render_helper):
        """Test get_short_time with 24-hour format."""
        # Test various times in 24-hour format
        time_cases = [
            (dt.datetime(2024, 1, 1, 0, 0), "0:00"),
            (dt.datetime(2024, 1, 1, 9, 30), "9:30"),
            (dt.datetime(2024, 1, 1, 12, 0), "12:00"),
            (dt.datetime(2024, 1, 1, 23, 59), "23:59"),
            (dt.datetime(2024, 1, 1, 14, 5), "14:05"),
        ]

        for datetime_obj, expected in time_cases:
            result = render_helper.get_short_time(datetime_obj, is24hour=True)
            assert result == expected, (
                f"Failed for {datetime_obj}: expected {expected}, got {result}"
            )

    def test_get_short_time_12hour_format(self, render_helper):
        """Test get_short_time with 12-hour format."""
        test_cases = [
            # Midnight cases
            (dt.datetime(2024, 1, 1, 0, 0), "12am"),
            (dt.datetime(2024, 1, 1, 0, 30), "12:30am"),
            # Morning cases
            (dt.datetime(2024, 1, 1, 1, 0), "1am"),
            (dt.datetime(2024, 1, 1, 9, 15), "9:15am"),
            (dt.datetime(2024, 1, 1, 11, 45), "11:45am"),
            # Noon cases
            (dt.datetime(2024, 1, 1, 12, 0), "12pm"),
            (dt.datetime(2024, 1, 1, 12, 30), "12:30pm"),
            # Afternoon/Evening cases
            (dt.datetime(2024, 1, 1, 13, 0), "1pm"),
            (dt.datetime(2024, 1, 1, 15, 20), "3:20pm"),
            (dt.datetime(2024, 1, 1, 23, 59), "11:59pm"),
        ]

        for datetime_obj, expected in test_cases:
            result = render_helper.get_short_time(datetime_obj, is24hour=False)
            assert result == expected, (
                f"Failed for {datetime_obj}: expected {expected}, got {result}"
            )

    def test_get_short_time_zero_minutes(self, render_helper):
        """Test get_short_time when minutes are zero in 12-hour format."""
        # When minutes are 0, they should not be displayed
        test_cases = [
            (dt.datetime(2024, 1, 1, 0, 0), "12am"),
            (dt.datetime(2024, 1, 1, 5, 0), "5am"),
            (dt.datetime(2024, 1, 1, 12, 0), "12pm"),
            (dt.datetime(2024, 1, 1, 18, 0), "6pm"),
        ]

        for datetime_obj, expected in test_cases:
            result = render_helper.get_short_time(datetime_obj, is24hour=False)
            assert result == expected, (
                f"Failed for {datetime_obj}: expected {expected}, got {result}"
            )
