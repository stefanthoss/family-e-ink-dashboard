"""
Tests for the IcsModule.
"""

import datetime as dt
import os
import sys
from unittest.mock import patch

import pytest

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ics_cal.ics import IcsModule


@pytest.fixture
def ics_module():
    """Provides an instance of IcsModule for testing."""
    return IcsModule()


@pytest.mark.parametrize(
    "mock_events, expected_events_by_day",
    [
        # Test case 1: Single day event
        (
            [
                {
                    "summary": "Test Event 1",
                    "location": "Test Location 1",
                    "startDatetime": dt.datetime(2024, 8, 27, 10, 0, 0),
                    "endDatetime": dt.datetime(2024, 8, 27, 11, 0, 0),
                    "isMultiday": False,
                    "allday": False,
                    "calendarName": "Work",
                }
            ],
            {
                dt.date(2024, 8, 27): [
                    {
                        "summary": "Test Event 1",
                        "location": "Test Location 1",
                        "startDatetime": dt.datetime(2024, 8, 27, 10, 0, 0),
                        "endDatetime": dt.datetime(2024, 8, 27, 11, 0, 0),
                        "isMultiday": False,
                        "allday": False,
                        "calendarName": "Work",
                    }
                ]
            },
        ),
        # Test case 2: Multi-day event spanning two days
        (
            [
                {
                    "summary": "Multi-day Event",
                    "location": "Conference Center",
                    "startDatetime": dt.datetime(2024, 8, 28, 16, 0, 0),
                    "endDatetime": dt.datetime(2024, 8, 29, 12, 0, 0),
                    "isMultiday": True,
                    "allday": False,
                    "calendarName": "Personal",
                }
            ],
            {
                dt.date(2024, 8, 28): [
                    {
                        "summary": "Multi-day Event",
                        "location": "Conference Center",
                        "startDatetime": dt.datetime(2024, 8, 28, 16, 0, 0),
                        "endDatetime": dt.datetime(2024, 8, 28, 23, 59, 59),
                        "isMultiday": True,
                        "allday": False,
                        "calendarName": "Personal",
                    }
                ],
                dt.date(2024, 8, 29): [
                    {
                        "summary": "Multi-day Event",
                        "location": "Conference Center",
                        "startDatetime": dt.datetime(2024, 8, 29, 0, 0, 0),
                        "endDatetime": dt.datetime(2024, 8, 29, 12, 0, 0),
                        "isMultiday": True,
                        "allday": False,
                        "calendarName": "Personal",
                    }
                ],
            },
        ),
        # Test case 3: All-day event
        (
            [
                {
                    "summary": "All-day Event",
                    "startDatetime": dt.datetime(2024, 8, 30, 0, 0, 0),
                    "endDatetime": dt.datetime(2024, 8, 30, 23, 59, 59),
                    "isMultiday": False,
                    "allday": True,
                    "calendarName": "Family",
                }
            ],
            {
                dt.date(2024, 8, 30): [
                    {
                        "summary": "All-day Event",
                        "startDatetime": dt.datetime(2024, 8, 30, 0, 0, 0),
                        "endDatetime": dt.datetime(2024, 8, 30, 23, 59, 59),
                        "isMultiday": False,
                        "allday": True,
                        "calendarName": "Family",
                    }
                ]
            },
        ),
        # Test case 4: No events
        ([], {}),
    ],
)
@patch("ics_cal.ics.IcsModule._retrieve_events")
def test_get_events(
    mock_retrieve_events,
    ics_module,
    mock_events,
    expected_events_by_day,
):
    """Test get_events method with various scenarios."""
    mock_retrieve_events.return_value = mock_events

    ics_url = "https://example.com/calendar.ics"
    cal_start = dt.datetime(2024, 8, 27, 0, 0, 0)
    cal_end = dt.datetime(2024, 8, 31, 0, 0, 0)
    display_tz = "Europe/Berlin"

    events_by_day = ics_module.get_events(ics_url, cal_start, cal_end, display_tz)

    assert events_by_day == expected_events_by_day
