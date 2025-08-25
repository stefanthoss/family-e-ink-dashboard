import datetime as dt
import pytest
import sys
import os

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from render.render import RenderHelper


class TestRenderHelper:
    """Test suite for RenderHelper class methods."""

    def test_extend_list_shorter_list(self):
        """Test extend_list when list is shorter than target length."""
        test_list = ["item1", "item2"]
        RenderHelper.extend_list(test_list, 5, "default")
        expected = ["item1", "item2", "default", "default", "default"]
        assert test_list == expected

    def test_extend_list_empty_list(self):
        """Test extend_list with empty list."""
        test_list = []
        RenderHelper.extend_list(test_list, 3, "default")
        expected = ["default", "default", "default"]
        assert test_list == expected

    def test_extend_list_exact_length(self):
        """Test extend_list when list is already the target length."""
        test_list = ["item1", "item2", "item3"]
        original_list = test_list.copy()
        RenderHelper.extend_list(test_list, 3, "default")
        assert test_list == original_list

    def test_extend_list_longer_list(self):
        """Test extend_list when list is longer than target length."""
        test_list = ["item1", "item2", "item3", "item4", "item5"]
        original_list = test_list.copy()
        RenderHelper.extend_list(test_list, 3, "default")
        assert test_list == original_list

    def test_extend_list_zero_length(self):
        """Test extend_list with zero target length."""
        test_list = ["item1", "item2"]
        original_list = test_list.copy()
        RenderHelper.extend_list(test_list, 0, "default")
        assert test_list == original_list

    def test_extend_list_different_default_values(self):
        """Test extend_list with different default value types."""
        test_list = [1, 2]
        RenderHelper.extend_list(test_list, 4, 0)
        assert test_list == [1, 2, 0, 0]

    @pytest.mark.parametrize(
        "datetime_obj,expected",
        [
            (dt.datetime(2024, 1, 1, 0, 0), "0:00"),
            (dt.datetime(2024, 1, 1, 9, 30), "9:30"),
            (dt.datetime(2024, 1, 1, 12, 0), "12:00"),
            (dt.datetime(2024, 1, 1, 23, 59), "23:59"),
            (dt.datetime(2024, 1, 1, 14, 5), "14:05"),
        ],
    )
    def test_get_short_time_24hour_format(self, datetime_obj, expected):
        """Test get_short_time with 24-hour format."""
        result = RenderHelper.get_short_time(datetime_obj, is24hour=True)
        assert result == expected

    @pytest.mark.parametrize(
        "datetime_obj,expected",
        [
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
        ],
    )
    def test_get_short_time_12hour_format(self, datetime_obj, expected):
        """Test get_short_time with 12-hour format."""
        result = RenderHelper.get_short_time(datetime_obj, is24hour=False)
        assert result == expected

    @pytest.mark.parametrize(
        "datetime_obj,expected",
        [
            (dt.datetime(2024, 1, 1, 0, 0), "12am"),
            (dt.datetime(2024, 1, 1, 5, 0), "5am"),
            (dt.datetime(2024, 1, 1, 12, 0), "12pm"),
            (dt.datetime(2024, 1, 1, 18, 0), "6pm"),
        ],
    )
    def test_get_short_time_zero_minutes(self, datetime_obj, expected):
        """Test get_short_time when minutes are zero in 12-hour format."""
        result = RenderHelper.get_short_time(datetime_obj, is24hour=False)
        assert result == expected
