"""
This is where we retrieve events from an ICS calendar.
"""

import datetime as dt
from typing import Any, Dict, List

import icalendar
import pytz
import recurring_ical_events
import requests
import structlog


class IcsModule:
    def __init__(self) -> None:
        self.logger = structlog.get_logger()

    def _retrieve_events(
        self,
        ics_url: str,
        calStartDatetime: dt.datetime,
        calEndDatetime: dt.datetime,
        localTZ: str,
    ) -> List[Dict[str, Any]]:
        # Call the ICS calendar and return a list of events that fall within the specified dates
        event_list = []

        self.logger.info("Retrieving events from ICS...")
        ics_urls = ics_url.split("|")
        for ics_url in ics_urls:
            try:
                response = requests.get(ics_url, timeout=10)
                response.raise_for_status()
                cal = icalendar.Calendar.from_ical(response.text)
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error downloading ICS: {e}")
                continue
            except ValueError as e:
                self.logger.error(f"Error parsing ICS: {e}")
                continue

            cal_name = cal.get("X-WR-CALNAME", None)

            events = recurring_ical_events.of(cal).between(calStartDatetime, calEndDatetime)
            local_timezone = pytz.timezone(localTZ)

            for event in events:
                new_event: Dict[str, Any] = {"summary": str(event.get("SUMMARY"))}

                if "LOCATION" in event:
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
                    new_event["calendarName"] = cal_name

                    event_list.append(new_event)

        return sorted(event_list, key=lambda k: k["startDatetime"])

    def get_events(
        self,
        ics_url: str,
        calStartDatetime: dt.datetime,
        calEndDatetime: dt.datetime,
        displayTZ: str,
    ) -> Dict[dt.date, List[Dict[str, Any]]]:
        eventList = self._retrieve_events(ics_url, calStartDatetime, calEndDatetime, displayTZ)

        calDict: Dict[dt.date, List[Dict[str, Any]]] = {}

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
