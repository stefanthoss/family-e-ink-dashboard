"""
This is where we retrieve events from an ICS calendar.
"""

import datetime as dt
from typing import Any, Dict, List, Tuple

import structlog

from ics_cal.icshelper import IcsHelper


class IcsModule:
    def __init__(self) -> None:
        self.logger = structlog.get_logger()
        self.calHelper = IcsHelper()

    def get_short_time(self, datetimeObj: dt.datetime) -> str:
        datetime_str = ""
        if datetimeObj.minute > 0:
            datetime_str = ".{:02d}".format(datetimeObj.minute)

        if datetimeObj.hour == 0:
            datetime_str = "12{}am".format(datetime_str)
        elif datetimeObj.hour == 12:
            datetime_str = "12{}pm".format(datetime_str)
        elif datetimeObj.hour > 12:
            datetime_str = "{}{}pm".format(str(datetimeObj.hour % 12), datetime_str)
        else:
            datetime_str = "{}{}am".format(str(datetimeObj.hour), datetime_str)
        return datetime_str

    def get_events(
        self,
        ics_url: str,
        calStartDatetime: dt.datetime,
        calEndDatetime: dt.datetime,
        displayTZ: str,
        numDays: int,
    ) -> List[Tuple[dt.date, List[Dict[str, Any]]]]:
        eventList = self.calHelper.retrieve_events(
            ics_url, calStartDatetime, calEndDatetime, displayTZ
        )

        calDict: Dict[dt.date, List[Dict[str, Any]]] = {}

        for event in eventList:
            if event["isMultiday"]:
                numDays = (event["endDatetime"].date() - event["startDatetime"].date()).days
                for day in range(0, numDays + 1):
                    event_day = event.copy()
                    if day > 0:
                        # Set start time to midnight since event has started before this day
                        event_day["startDatetime"] = event_day["startDatetime"].replace(
                            hour=0, minute=0, second=0, microsecond=0
                        ) + dt.timedelta(days=day)
                        event_day["allday"] = True

                    calDict.setdefault(event_day["startDatetime"].date(), []).append(event_day)
            else:
                calDict.setdefault(event["startDatetime"].date(), []).append(event)

        return sorted(calDict.items(), key=lambda x: x[0])
