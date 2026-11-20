"""
Tests for the IcsModule.
"""

import datetime as dt
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
import pytz
import requests

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
                    "startDatetime": dt.datetime(2024, 8, 27, 10, 0, 0, tzinfo=dt.UTC),
                    "endDatetime": dt.datetime(2024, 8, 27, 11, 0, 0, tzinfo=dt.UTC),
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
                    "startDatetime": dt.datetime(2024, 8, 27, 0, 0, 0, tzinfo=dt.UTC),
                    "endDatetime": dt.datetime(2024, 8, 27, 23, 59, 59, tzinfo=dt.UTC),
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
                    "startDatetime": dt.datetime(2024, 8, 27, 16, 0, 0, tzinfo=dt.UTC),
                    "endDatetime": dt.datetime(2024, 8, 29, 12, 0, 0, tzinfo=dt.UTC),
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
                    "startDatetime": dt.datetime(2024, 8, 28, 22, 0, 0, tzinfo=dt.UTC),
                    "endDatetime": dt.datetime(2024, 8, 29, 0, 30, 0, tzinfo=dt.UTC),
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
                    "startDatetime": dt.datetime(2024, 8, 27, 10, 0, 0, tzinfo=dt.UTC),
                    "endDatetime": dt.datetime(2024, 8, 27, 11, 0, 0, tzinfo=dt.UTC),
                    "isMultiday": False,
                    "calendarName": None,
                },
                {
                    "summary": "Recurring Event",
                    "startDatetime": dt.datetime(2024, 8, 28, 10, 0, 0, tzinfo=dt.UTC),
                    "endDatetime": dt.datetime(2024, 8, 28, 11, 0, 0, tzinfo=dt.UTC),
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
                    "startDatetime": dt.datetime(2024, 8, 27, 14, 0, 0, tzinfo=dt.UTC),
                    "endDatetime": dt.datetime(2024, 8, 27, 15, 0, 0, tzinfo=dt.UTC),
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

    cal_start = dt.datetime(2024, 8, 27, 0, 0, 0, tzinfo=dt.UTC)
    cal_end = dt.datetime(2024, 8, 30, 0, 0, 0, tzinfo=dt.UTC)
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

    cal_start = dt.datetime(2024, 8, 27, 0, 0, 0, tzinfo=dt.UTC)
    cal_end = dt.datetime(2024, 8, 28, 0, 0, 0, tzinfo=dt.UTC)
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

    cal_start = dt.datetime(2024, 8, 27, 0, 0, 0, tzinfo=dt.UTC)
    cal_end = dt.datetime(2024, 8, 28, 0, 0, 0, tzinfo=dt.UTC)
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
    cal_start = dt.datetime(2024, 8, 27, 0, 0, 0, tzinfo=dt.UTC)
    cal_end = dt.datetime(2024, 8, 28, 23, 59, 59, tzinfo=dt.UTC)
    display_tz = "UTC"

    events = ics_module._retrieve_events(
        "https://example.com/calendar.ics", cal_start, cal_end, display_tz
    )

    assert len(events) == 1
    assert events[0]["summary"] == "In Range"


# Failure handling: a dead feed must not take the dashboard down, and a feed URL must never
# reach the logs -- it contains the token and passphrase that unlock the calendar.

SECRET_FEED_URL = (
    "https://calendar.proton.me/api/calendar/v1/url/SECRETFEEDTOKEN/calendar.ics"
    "?CacheKey=SECRETCACHEKEY%3D%3D&PassphraseKey=SECRETPASSPHRASE%3D"
)
SECRETS = ("SECRETFEEDTOKEN", "SECRETCACHEKEY", "SECRETPASSPHRASE")

WORK_ICS = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Work//EN
X-WR-CALNAME:Work
BEGIN:VEVENT
DTSTART:20240827T100000Z
DTEND:20240827T110000Z
SUMMARY:Work Event
UID:work1
END:VEVENT
END:VCALENDAR"""

CAL_START = dt.datetime(2024, 8, 27, 0, 0, 0, tzinfo=dt.UTC)
CAL_END = dt.datetime(2024, 8, 28, 0, 0, 0, tzinfo=dt.UTC)


def http_error(status_code: int, body: str, url: str = SECRET_FEED_URL):
    """Build the kind of exception requests raises for an error response."""
    response = requests.Response()
    response.status_code = status_code
    response._content = body.encode("utf-8")
    response.url = url
    response.reason = "Error"
    return requests.exceptions.HTTPError(f"{status_code} Error", response=response)


def calendar_response(ics_content: str = WORK_ICS):
    response = MagicMock()
    response.text = ics_content
    response.raise_for_status.return_value = None
    return response


@patch("ics_cal.ics.requests.get")
def test_revoked_feed_does_not_break_the_other_calendars(mock_get, ics_module):
    """The reported case: one revoked Proton link next to a working calendar."""
    mock_get.side_effect = [
        http_error(422, '{"Code":2501,"Error":"Link not found","Details":{}}'),
        calendar_response(),
    ]

    events = ics_module._retrieve_events(
        f"{SECRET_FEED_URL}|https://example.com/work.ics", CAL_START, CAL_END, "UTC"
    )

    assert [event["summary"] for event in events] == ["Work Event"]


@patch("ics_cal.ics.requests.get")
def test_every_feed_failing_returns_no_events_instead_of_raising(mock_get, ics_module):
    mock_get.side_effect = http_error(404, "no such calendar")

    events = ics_module._retrieve_events(SECRET_FEED_URL, CAL_START, CAL_END, "UTC")

    assert events == []


@patch("ics_cal.ics.requests.get")
def test_blank_url_entries_are_ignored(mock_get, ics_module):
    mock_get.return_value = calendar_response()

    events = ics_module._retrieve_events(f"  |{SECRET_FEED_URL}| ", CAL_START, CAL_END, "UTC")

    assert len(events) == 1
    assert mock_get.call_count == 1


@patch("ics_cal.ics.requests.get")
def test_unparsable_calendar_is_skipped_instead_of_raising(mock_get, ics_module):
    """A share link that turned into a web page is reported, not crashed on."""
    mock_get.return_value = calendar_response("<html><body>Link expired</body></html>")

    events = ics_module._retrieve_events(SECRET_FEED_URL, CAL_START, CAL_END, "UTC")

    assert events == []


class TestLogMessagesDoNotLeakFeedSecrets:
    @pytest.mark.parametrize(
        "error",
        [
            http_error(422, '{"Code":2501,"Error":"Link not found"}'),
            http_error(404, f"Calendar {SECRET_FEED_URL} does not exist"),
            requests.exceptions.ConnectionError(
                f"HTTPSConnectionPool(host='calendar.proton.me', port=443): "
                f"Max retries exceeded with url: {SECRET_FEED_URL}"
            ),
            requests.exceptions.ReadTimeout(f"Read timed out. (read timeout=10) {SECRET_FEED_URL}"),
            requests.exceptions.MissingSchema(f"Invalid URL {SECRET_FEED_URL}: no scheme"),
        ],
    )
    @patch("ics_cal.ics.requests.get")
    def test_download_failures(self, mock_get, ics_module, error):
        mock_get.side_effect = error

        with patch.object(ics_module, "logger") as mock_logger:
            ics_module._retrieve_events(SECRET_FEED_URL, CAL_START, CAL_END, "UTC")

        for call in mock_logger.method_calls:
            for secret in SECRETS:
                assert secret not in str(call)

    @patch("ics_cal.ics.requests.get")
    def test_parse_failures(self, mock_get, ics_module):
        """An 'expired link' page can quote the feed URL back at us, and icalendar logs it."""
        mock_get.return_value = calendar_response(
            f"<html>This link has expired: {SECRET_FEED_URL}</html>"
        )

        with patch.object(ics_module, "logger") as mock_logger:
            ics_module._retrieve_events(SECRET_FEED_URL, CAL_START, CAL_END, "UTC")

        for call in mock_logger.method_calls:
            for secret in SECRETS:
                assert secret not in str(call)

    @patch("ics_cal.ics.requests.get")
    def test_logs_the_status_code_of_a_failing_feed(self, mock_get, ics_module):
        mock_get.side_effect = http_error(422, '{"Code":2501,"Error":"Link not found"}')

        with patch.object(ics_module, "logger") as mock_logger:
            ics_module._retrieve_events(SECRET_FEED_URL, CAL_START, CAL_END, "UTC")

        message = str(mock_logger.error.call_args)
        assert "HTTP 422" in message
        for secret in SECRETS:
            assert secret not in message
