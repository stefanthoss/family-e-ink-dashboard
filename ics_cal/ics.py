"""
This is where we retrieve events from an ICS calendar.
"""

from ics_cal.icshelper import IcsHelper
import logging


class IcsModule:
    def __init__(self):
        self.logger = logging.getLogger('maginkdash')
        self.calHelper = IcsHelper()

    def get_day_in_cal(self, startDate, eventDate):
        delta = eventDate - startDate
        return delta.days

    def get_short_time(self, datetimeObj):
        datetime_str = ''
        if datetimeObj.minute > 0:
            datetime_str = '.{:02d}'.format(datetimeObj.minute)

        if datetimeObj.hour == 0:
            datetime_str = '12{}am'.format(datetime_str)
        elif datetimeObj.hour == 12:
            datetime_str = '12{}pm'.format(datetime_str)
        elif datetimeObj.hour > 12:
            datetime_str = '{}{}pm'.format(str(datetimeObj.hour % 12), datetime_str)
        else:
            datetime_str = '{}{}am'.format(str(datetimeObj.hour), datetime_str)
        return datetime_str

    def get_events(self, currDate, ics_url, calStartDatetime, calEndDatetime, displayTZ, numDays):
        eventList = self.calHelper.retrieve_events(ics_url, calStartDatetime, calEndDatetime, displayTZ)

        # check if event stretches across multiple days
        calList = []
        for i in range(numDays):
            calList.append([])
        for event in eventList:
            idx = self.get_day_in_cal(currDate, event['startDatetime'].date())
            if event['isMultiday']:
                end_idx = self.get_day_in_cal(currDate, event['endDatetime'].date())
                if idx < 0:
                    idx = 0
                if end_idx >= len(calList):
                    end_idx = len(calList) - 1
                for i in range(idx, end_idx + 1):
                    calList[i].append(event)
            elif idx >= 0:
                calList[idx].append(event)

        return calList
