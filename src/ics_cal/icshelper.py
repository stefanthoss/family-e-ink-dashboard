#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This is where we retrieve events from the ICS calendar.
"""

from __future__ import print_function

import datetime as dt
import sys

import requests
import structlog
from ics import Calendar


class IcsHelper:
    def __init__(self):
        self.logger = structlog.get_logger()

    def to_datetime(self, isoDatetime, localTZ):
        # replace Z with +00:00 is a workaround until datetime library decides what to do with the Z notation
        to_datetime = dt.datetime.fromisoformat(isoDatetime.replace("Z", "+00:00"))
        return to_datetime.astimezone(localTZ)

    def adjust_end_time(self, endTime, localTZ):
        # check if end time is at 00:00 of next day, if so set to max time for day before
        if endTime.hour == 0 and endTime.minute == 0 and endTime.second == 0:
            newEndtime = localTZ.localize(
                dt.datetime.combine(endTime.date() - dt.timedelta(days=1), dt.datetime.max.time())
            )
            return newEndtime
        else:
            return endTime

    def is_multiday(self, start, end):
        # check if event stretches across multiple days
        return start.date() != end.date()

    def retrieve_events(self, ics_url, startDatetime, endDatetime, localTZ):
        # Call the Google Calendar API and return a list of events that fall within the specified dates
        event_list = []

        self.logger.info("Retrieving events from ICS...")

        response = requests.get(ics_url)
        if response.ok:
            cal = Calendar(response.text)
        else:
            self.logger.error(f"Received an error when downloading ICS: {response.text}")
            sys.exit(1)

        if not cal.events:
            self.logger.info("No upcoming calendar events found.")
        for event in cal.events:
            # extracting and converting events data into a new list
            new_event = {"summary": event.name}
            new_event["allday"] = event.all_day
            new_event["startDatetime"] = self.to_datetime(event.begin.isoformat(), localTZ)
            new_event["endDatetime"] = self.adjust_end_time(
                self.to_datetime(event.end.isoformat(), localTZ), localTZ
            )
            new_event["isMultiday"] = self.is_multiday(
                new_event["startDatetime"], new_event["endDatetime"]
            )
            event_list.append(new_event)

        # We need to sort eventList because the event will be sorted in "calendar order" instead of hours order
        # TODO: improve because of double cycle for now is not much cost
        event_list = sorted(event_list, key=lambda k: k["startDatetime"])
        return event_list
