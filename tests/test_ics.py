"""
Tests for the IcsModule.
"""

import datetime as dt
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
import pytz

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
        # Single day event
        (
            [
                {
                    "summary": "Test Event 1",
                    "location": "Test Location 1",
                    "startDatetime": dt.datetime(2024, 8, 27, 10, 0, 0),
                    "endDatetime": dt.datetime(2024, 8, 27, 11, 0, 0),
                    "isMultiday": False,
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
                        "calendarName": "Work",
                    }
                ]
            },
        ),
        # Multi-day event spanning two days
        (
            [
                {
                    "summary": "Multi-day Event",
                    "location": "Conference Center",
                    "startDatetime": dt.datetime(2024, 8, 28, 16, 0, 0),
                    "endDatetime": dt.datetime(2024, 8, 29, 12, 0, 0),
                    "isMultiday": True,
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
                        "calendarName": "Personal",
                    }
                ],
            },
        ),
        # Short event crossing midnight
        (
            [
                {
                    "summary": "Cross-midnight Event",
                    "location": "Dive Bar",
                    "startDatetime": dt.datetime(2024, 8, 28, 23, 0, 0),
                    "endDatetime": dt.datetime(2024, 8, 29, 0, 30, 0),
                    "isMultiday": True,
                    "calendarName": "Personal",
                }
            ],
            {
                dt.date(2024, 8, 28): [
                    {
                        "summary": "Cross-midnight Event",
                        "location": "Dive Bar",
                        "startDatetime": dt.datetime(2024, 8, 28, 23, 0, 0),
                        "endDatetime": dt.datetime(2024, 8, 28, 23, 59, 59),
                        "isMultiday": True,
                        "calendarName": "Personal",
                    }
                ],
                dt.date(2024, 8, 29): [
                    {
                        "summary": "Cross-midnight Event",
                        "location": "Dive Bar",
                        "startDatetime": dt.datetime(2024, 8, 29, 0, 0, 0),
                        "endDatetime": dt.datetime(2024, 8, 29, 0, 30, 0),
                        "isMultiday": True,
                        "calendarName": "Personal",
                    }
                ],
            },
        ),
        # All-day event
        (
            [
                {
                    "summary": "All-day Event",
                    "startDatetime": dt.datetime(2024, 8, 30, 0, 0, 0),
                    "endDatetime": dt.datetime(2024, 8, 30, 23, 59, 59),
                    "isMultiday": False,
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
                        "calendarName": "Family",
                    }
                ]
            },
        ),
        # No events
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


@pytest.mark.parametrize(
    "ics_content, expected_events",
    [
        # Single timed event
        (
            """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test Calendar//EN
X-WR-CALNAME:Work Calendar
BEGIN:VEVENT
DTSTART:20240827T100000Z
DTEND:20240827T110000Z
SUMMARY:Test Event 1
LOCATION:Test Location 1
UID:12345
END:VEVENT
END:VCALENDAR""",
            [
                {
                    "summary": "Test Event 1",
                    "location": "Test Location 1",
                    "startDatetime": dt.datetime(2024, 8, 27, 10, 0, 0, tzinfo=dt.timezone.utc),
                    "endDatetime": dt.datetime(2024, 8, 27, 11, 0, 0, tzinfo=dt.timezone.utc),
                    "isMultiday": False,
                    "calendarName": "Work Calendar",
                }
            ],
        ),
        # All-day event
        (
            """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test Calendar//EN
BEGIN:VEVENT
DTSTART;VALUE=DATE:20240827
DTEND;VALUE=DATE:20240828
SUMMARY:All-day Event
UID:12345
END:VEVENT
END:VCALENDAR""",
            [
                {
                    "summary": "All-day Event",
                    "startDatetime": dt.datetime(2024, 8, 27, 0, 0, 0, tzinfo=dt.timezone.utc),
                    "endDatetime": dt.datetime(2024, 8, 27, 23, 59, 59, tzinfo=dt.timezone.utc),
                    "isMultiday": False,
                    "calendarName": None,
                }
            ],
        ),
        # Multi-day event
        (
            """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test Calendar//EN
BEGIN:VEVENT
DTSTART:20240827T160000Z
DTEND:20240829T120000Z
SUMMARY:Multi-day Event
UID:12345
END:VEVENT
END:VCALENDAR""",
            [
                {
                    "summary": "Multi-day Event",
                    "startDatetime": dt.datetime(2024, 8, 27, 16, 0, 0, tzinfo=dt.timezone.utc),
                    "endDatetime": dt.datetime(2024, 8, 29, 12, 0, 0, tzinfo=dt.timezone.utc),
                    "isMultiday": True,
                    "calendarName": None,
                }
            ],
        ),
        # Short event crossing midnight
        (
            """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test Calendar//EN
X-WR-CALNAME:Personal
BEGIN:VEVENT
DTSTART:20240828T220000Z
DTEND:20240829T003000Z
SUMMARY:Cross-midnight Event
LOCATION:Dive Bar
UID:12345
END:VEVENT
END:VCALENDAR""",
            [
                {
                    "summary": "Cross-midnight Event",
                    "location": "Dive Bar",
                    "startDatetime": dt.datetime(2024, 8, 28, 22, 0, 0, tzinfo=dt.timezone.utc),
                    "endDatetime": dt.datetime(2024, 8, 29, 0, 30, 0, tzinfo=dt.timezone.utc),
                    "isMultiday": True,
                    "calendarName": "Personal",
                }
            ],
        ),
        # Recurring event (daily for 2 days)
        (
            """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test Calendar//EN
BEGIN:VEVENT
DTSTART:20240827T100000Z
DTEND:20240827T110000Z
SUMMARY:Recurring Event
RRULE:FREQ=DAILY;COUNT=2
UID:12345
END:VEVENT
END:VCALENDAR""",
            [
                {
                    "summary": "Recurring Event",
                    "startDatetime": dt.datetime(2024, 8, 27, 10, 0, 0, tzinfo=dt.timezone.utc),
                    "endDatetime": dt.datetime(2024, 8, 27, 11, 0, 0, tzinfo=dt.timezone.utc),
                    "isMultiday": False,
                    "calendarName": None,
                },
                {
                    "summary": "Recurring Event",
                    "startDatetime": dt.datetime(2024, 8, 28, 10, 0, 0, tzinfo=dt.timezone.utc),
                    "endDatetime": dt.datetime(2024, 8, 28, 11, 0, 0, tzinfo=dt.timezone.utc),
                    "isMultiday": False,
                    "calendarName": None,
                },
            ],
        ),
        # No events (empty calendar)
        (
            """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test Calendar//EN
END:VCALENDAR""",
            [],
        ),
        # Event without location
        (
            """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test Calendar//EN
BEGIN:VEVENT
DTSTART:20240827T140000Z
DTEND:20240827T150000Z
SUMMARY:No Location Event
UID:67890
END:VEVENT
END:VCALENDAR""",
            [
                {
                    "summary": "No Location Event",
                    "startDatetime": dt.datetime(2024, 8, 27, 14, 0, 0, tzinfo=dt.timezone.utc),
                    "endDatetime": dt.datetime(2024, 8, 27, 15, 0, 0, tzinfo=dt.timezone.utc),
                    "isMultiday": False,
                    "calendarName": None,
                }
            ],
        ),
    ],
)
@patch("ics_cal.ics.requests.get")
def test_retrieve_events_success(mock_get, ics_module, ics_content, expected_events):
    """Test _retrieve_events method with various calendar scenarios."""
    mock_response = MagicMock()
    mock_response.text = ics_content
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    cal_start = dt.datetime(2024, 8, 27, 0, 0, 0, tzinfo=dt.timezone.utc)
    cal_end = dt.datetime(2024, 8, 30, 0, 0, 0, tzinfo=dt.timezone.utc)
    display_tz = "UTC"

    events = ics_module._retrieve_events(
        "https://example.com/calendar.ics", cal_start, cal_end, display_tz
    )

    assert events == expected_events


@patch("ics_cal.ics.requests.get")
def test_retrieve_events_multiple_urls(mock_get, ics_module):
    """Test _retrieve_events method with multiple ICS URLs separated by pipe."""
    # Setup responses for two different calendars
    responses = [
        MagicMock(),
        MagicMock(),
    ]

    responses[0].text = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Calendar 1//EN
X-WR-CALNAME:Work
BEGIN:VEVENT
DTSTART:20240827T100000Z
DTEND:20240827T110000Z
SUMMARY:Work Event
UID:work1
END:VEVENT
END:VCALENDAR"""
    responses[0].raise_for_status.return_value = None

    responses[1].text = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Calendar 2//EN
X-WR-CALNAME:Personal
BEGIN:VEVENT
DTSTART:20240827T140000Z
DTEND:20240827T150000Z
SUMMARY:Personal Event
UID:personal1
END:VEVENT
END:VCALENDAR"""
    responses[1].raise_for_status.return_value = None

    mock_get.side_effect = responses

    cal_start = dt.datetime(2024, 8, 27, 0, 0, 0, tzinfo=dt.timezone.utc)
    cal_end = dt.datetime(2024, 8, 28, 0, 0, 0, tzinfo=dt.timezone.utc)
    display_tz = "UTC"

    # Test with pipe-separated URLs
    events = ics_module._retrieve_events(
        "https://example.com/calendar.ics|http://work.com/cal.ics", cal_start, cal_end, display_tz
    )

    assert len(events) == 2
    # Events should be sorted by start time
    assert events[0]["summary"] == "Work Event"
    assert events[0]["calendarName"] == "Work"
    assert events[1]["summary"] == "Personal Event"
    assert events[1]["calendarName"] == "Personal"


@patch("ics_cal.ics.requests.get")
def test_retrieve_events_timezone_conversion(mock_get, ics_module):
    """Test _retrieve_events method properly converts timezones."""
    mock_response = MagicMock()
    mock_response.text = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test Calendar//EN
BEGIN:VEVENT
DTSTART:20240827T100000Z
DTEND:20240827T110000Z
SUMMARY:UTC Event
UID:12345
END:VEVENT
END:VCALENDAR"""
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    cal_start = dt.datetime(2024, 8, 27, 0, 0, 0, tzinfo=dt.timezone.utc)
    cal_end = dt.datetime(2024, 8, 28, 0, 0, 0, tzinfo=dt.timezone.utc)
    display_tz = "Europe/Berlin"  # UTC+2 in summer

    events = ics_module._retrieve_events(
        "https://example.com/calendar.ics", cal_start, cal_end, display_tz
    )

    assert len(events) == 1
    event = events[0]

    # Event should be converted to Berlin timezone (UTC+2 in summer)
    berlin_tz = pytz.timezone("Europe/Berlin")
    expected_start = berlin_tz.localize(dt.datetime(2024, 8, 27, 12, 0, 0))  # 10 UTC + 2 hours DST
    expected_end = berlin_tz.localize(dt.datetime(2024, 8, 27, 13, 0, 0))  # 11 UTC + 2 hours DST

    assert event["startDatetime"] == expected_start
    assert event["endDatetime"] == expected_end


@patch("ics_cal.ics.requests.get")
def test_retrieve_events_filtering_by_date_range(mock_get, ics_module):
    """Test _retrieve_events method filters events by date range."""
    mock_response = MagicMock()
    mock_response.text = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test Calendar//EN
BEGIN:VEVENT
DTSTART:20240826T100000Z
DTEND:20240826T110000Z
SUMMARY:Before Range
UID:before
END:VEVENT
BEGIN:VEVENT
DTSTART:20240827T100000Z
DTEND:20240827T110000Z
SUMMARY:In Range
UID:in
END:VEVENT
BEGIN:VEVENT
DTSTART:20240829T100000Z
DTEND:20240829T110000Z
SUMMARY:After Range
UID:after
END:VEVENT
END:VCALENDAR"""
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    # Set range to only include Aug 27-28
    cal_start = dt.datetime(2024, 8, 27, 0, 0, 0, tzinfo=dt.timezone.utc)
    cal_end = dt.datetime(2024, 8, 28, 23, 59, 59, tzinfo=dt.timezone.utc)
    display_tz = "UTC"

    events = ics_module._retrieve_events(
        "https://example.com/calendar.ics", cal_start, cal_end, display_tz
    )

    assert len(events) == 1
    assert events[0]["summary"] == "In Range"
