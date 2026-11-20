"""
This is where we retrieve events from an ICS calendar.
"""

import datetime as dt
from typing import Any

import icalendar
import pytz
import recurring_ical_events
import requests
import structlog

from redact import safe_url, status_of

TRUE_VALUES = ("true", "yes", "y", "on", "t", "1")
FALSE_VALUES = ("false", "no", "n", "off", "f", "0")


class IcsModule:
    def __init__(self) -> None:
        self.logger = structlog.get_logger()

    def _retrieve_events(
        self,
        ics_url: str,
        calStartDatetime: dt.datetime,
        calEndDatetime: dt.datetime,
        localTZ: str,
        prefixes: str = "",
        hide_locations: str = "",
    ) -> list[dict[str, Any]]:
        # Call the ICS calendar and return a list of events that fall within the specified dates
        event_list = []

        self.logger.info("Retrieving events from ICS...")
        ics_urls = [single_url.strip() for single_url in ics_url.split("|")]
        ics_urls = [single_url for single_url in ics_urls if single_url]
        feed_count = len(ics_urls)
        # The option lists keep their empty entries so that entry n still belongs to feed n.
        prefix_list = prefixes.split("|") if prefixes else []
        hide_list = hide_locations.split("|") if hide_locations else []
        self.warn_if_mismatch("ICS_PREFIX", len(prefix_list), feed_count)
        self.warn_if_mismatch("ICS_HIDE_LOCATION", len(hide_list), feed_count)

        for index, single_url in enumerate(ics_urls, start=1):
            # Which feed we are on matters when one of several calendars breaks.
            feed = f"{index}/{feed_count}"
            prefix = self.parse_prefix(prefix_list[index - 1]) if index <= len(prefix_list) else ""
            hides_location = (
                self.parse_bool(hide_list[index - 1], index) if index <= len(hide_list) else False
            )
            try:
                response = requests.get(single_url, timeout=10)
                response.raise_for_status()
                cal = icalendar.Calendar.from_ical(response.text)
            except requests.exceptions.RequestException as e:
                # Not the exception message: requests quotes the full URL there, including the
                # token and passphrase that unlock the calendar.
                status = status_of(e)
                detail = f"HTTP {status}" if status else type(e).__name__
                self.logger.error(
                    f"Error downloading ICS feed {feed} at {safe_url(single_url)}: {detail}"
                )
                continue
            except ValueError as e:
                # Not the message either: icalendar quotes the offending lines of the response,
                # and a "this link has expired" page can quote the feed URL right back at us.
                self.logger.error(
                    f"Error parsing ICS feed {feed} at {safe_url(single_url)}: "
                    f"{type(e).__name__} (message suppressed: it quotes calendar contents)"
                )
                continue

            events = recurring_ical_events.of(cal).between(calStartDatetime, calEndDatetime)
            local_timezone = pytz.timezone(localTZ)

            for event in events:
                new_event: dict[str, Any] = {"summary": f"{prefix}{event.get('SUMMARY')}"}

                if "LOCATION" in event and not hides_location:
                    new_event["location"] = str(event.get("LOCATION"))

                event_start = event.get("DTSTART").dt
                event_end = event.get("DTEND").dt

                if isinstance(event_start, dt.datetime):
                    new_event["startDatetime"] = event_start.astimezone(local_timezone)
                    new_event["endDatetime"] = event_end.astimezone(local_timezone)
                elif isinstance(event_start, dt.date):
                    # Convert date into datetime at midnight
                    new_event["startDatetime"] = local_timezone.localize(
                        dt.datetime.combine(event_start, dt.time(0, 0, 0))
                    )
                    new_event["endDatetime"] = local_timezone.localize(
                        dt.datetime.combine(event_end, dt.time(0, 0, 0))
                    ) - dt.timedelta(seconds=1)
                else:
                    raise TypeError(f"Unknown type {type(event_start)} for DTSTART")

                new_event["isMultiday"] = (
                    new_event["startDatetime"].date() != new_event["endDatetime"].date()
                )

                if (
                    new_event["endDatetime"] >= calStartDatetime
                    and new_event["startDatetime"] < calEndDatetime
                ):
                    # Don't show past days for ongoing multiday event
                    new_event["startDatetime"] = max(new_event["startDatetime"], calStartDatetime)
                    event_list.append(new_event)

        return sorted(event_list, key=lambda k: k["startDatetime"])

    def warn_if_mismatch(self, name: str, entries: int, feeds: int) -> None:
        """Use an option list as far as it reaches, but say that it does not line up."""
        if entries == 0 or entries == feeds:
            return
        entry_word = "entry" if entries == 1 else "entries"
        mismatch = f"{name} does not match ICS_URL ({entries} {entry_word} / {feeds} feed(s))"
        if entries > feeds:
            self.logger.warning(f"{mismatch}, ignoring the extra {entries - feeds}.")
        else:
            self.logger.warning(f"{mismatch}, the last {feeds - entries} feed(s) use the default.")

    @staticmethod
    def parse_prefix(entry: str) -> str:
        """A prefix is always followed by a space, so "School:" reads "School: Math Exam"."""
        prefix = entry.strip().strip("\"'")
        return f"{prefix} " if prefix else ""

    def parse_bool(self, entry: str, index: int) -> bool:
        """ICS_HIDE_LOCATION is the only option that holds a boolean, so its name is hardcoded."""
        value = entry.strip().strip("\"'").lower()
        if value in TRUE_VALUES:
            return True
        if value == "" or value in FALSE_VALUES:
            return False
        self.logger.warning(
            f'ICS_HIDE_LOCATION entry {index} is "{entry}", which is not a boolean, '
            "showing the location."
        )
        return False

    def get_events(
        self,
        ics_url: str,
        calStartDatetime: dt.datetime,
        calEndDatetime: dt.datetime,
        displayTZ: str,
        prefixes: str = "",
        hide_locations: str = "",
    ) -> dict[dt.date, list[dict[str, Any]]]:
        eventList = self._retrieve_events(
            ics_url, calStartDatetime, calEndDatetime, displayTZ, prefixes, hide_locations
        )

        calDict: dict[dt.date, list[dict[str, Any]]] = {}

        for event in eventList:
            if event["isMultiday"]:
                start_date = event["startDatetime"].date()
                end_date = event["endDatetime"].date()
                current_date = start_date
                while current_date <= end_date:
                    event_day = event.copy()
                    if current_date < end_date:
                        event_day["endDatetime"] = dt.datetime.combine(
                            current_date, dt.time(23, 59, 59)
                        )
                    else:
                        event_day["endDatetime"] = event["endDatetime"]

                    if current_date > start_date:
                        event_day["startDatetime"] = dt.datetime.combine(
                            current_date, dt.time(0, 0, 0)
                        )
                    else:
                        event_day["startDatetime"] = event["startDatetime"]

                    calDict.setdefault(current_date, []).append(event_day)
                    current_date += dt.timedelta(days=1)
            else:
                calDict.setdefault(event["startDatetime"].date(), []).append(event)

        return calDict
