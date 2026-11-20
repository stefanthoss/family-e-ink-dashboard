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


class IcsModule:
    def __init__(self) -> None:
        self.logger = structlog.get_logger()

    def _retrieve_events(
        self,
        ics_url: str,
        calStartDatetime: dt.datetime,
        calEndDatetime: dt.datetime,
        localTZ: str,
        prefix: str = "",
        hides_location: bool = False,
        feed_number: int = 1,
    ) -> list[dict[str, Any]]:
        """The events of one calendar."""
        event_list = []

        try:
            response = requests.get(ics_url, timeout=10)
            response.raise_for_status()
            cal = icalendar.Calendar.from_ical(response.text)
        except requests.exceptions.RequestException as e:
            # Not the exception message: requests quotes the full URL there, including the
            # token and passphrase that unlock the calendar.
            status = status_of(e)
            detail = f"HTTP {status}" if status else type(e).__name__
            self.logger.error(
                f"Error downloading ICS feed {feed_number} at {safe_url(ics_url)}: {detail}"
            )
            return []
        except ValueError as e:
            self.logger.error(
                f"Error parsing ICS feed {feed_number} at {safe_url(ics_url)}: "
                f"{type(e).__name__} (message suppressed: it quotes calendar contents)"
            )
            return []

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

    def get_events(
        self,
        ics_urls: list[str],
        calStartDatetime: dt.datetime,
        calEndDatetime: dt.datetime,
        displayTZ: str,
        prefixes: list[str] | None = None,
        hide_locations: list[bool] | None = None,
    ) -> dict[dt.date, list[dict[str, Any]]]:
        """One round of _retrieve_events per feed: the three lists are aligned by index, so feed n
        carries prefix n and the location setting of n."""
        self.logger.info("Retrieving events from ICS...")

        prefixes = prefixes or []
        hide_locations = hide_locations or []

        eventList: list[dict[str, Any]] = []
        for index, single_url in enumerate(ics_urls, start=1):
            eventList += self._retrieve_events(
                single_url,
                calStartDatetime,
                calEndDatetime,
                displayTZ,
                prefixes[index - 1] if index <= len(prefixes) else "",
                hide_locations[index - 1] if index <= len(hide_locations) else False,
                index,
            )
        eventList.sort(key=lambda k: k["startDatetime"])

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
