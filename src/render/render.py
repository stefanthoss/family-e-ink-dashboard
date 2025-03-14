"""
This script essentially generates a HTML file of the calendar I wish to display. It then fires up a headless Chrome
instance, sized to the resolution of the eInk display and takes a screenshot.

This might sound like a convoluted way to generate the calendar, but I'm doing so mainly because (i) it's easier to
format the calendar exactly the way I want it using HTML/CSS, and (ii) I can delink the generation of the
calendar and refreshing of the eInk display.
"""

import datetime as dt
import pathlib
import string
from time import sleep

import structlog
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class RenderHelper:
    def __init__(self, cfg):
        self.logger = structlog.get_logger()
        self.currPath = str(pathlib.Path(__file__).parent.absolute())
        self.htmlFile = "file://" + self.currPath + "/dashboard.html"
        self.cfg = cfg

    def set_viewport_size(self, driver):
        # Extract the current window size from the driver
        current_window_size = driver.get_window_size()

        # Extract the client window size from the html tag
        html = driver.find_element(By.TAG_NAME, "html")
        inner_width = int(html.get_attribute("clientWidth"))
        inner_height = int(html.get_attribute("clientHeight"))

        # "Internal width you want to set+Set "outer frame width" to window size
        target_width = self.cfg.IMAGE_WIDTH + (current_window_size["width"] - inner_width)
        target_height = self.cfg.IMAGE_HEIGHT + (current_window_size["height"] - inner_height)

        driver.set_window_rect(width=target_width, height=target_height)

    def get_screenshot(self, path_to_server_image):
        opts = Options()
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--force-device-scale-factor=1")
        opts.add_argument("--headless")
        opts.add_argument("--hide-scrollbars")
        opts.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=opts)
        self.set_viewport_size(driver)
        driver.get(self.htmlFile)
        sleep(1)
        driver.get_screenshot_as_file(self.currPath + "/dashboard.png")
        driver.get_screenshot_as_file(path_to_server_image)
        self.logger.debug(f"Screenshot captured and saved to file {path_to_server_image}.")
        driver.close()

    def get_short_time(self, datetimeObj, is24hour=False):
        datetime_str = ""
        if is24hour:
            datetime_str = "{}:{:02d}".format(datetimeObj.hour, datetimeObj.minute)
        else:
            if datetimeObj.minute > 0:
                datetime_str = ":{:02d}".format(datetimeObj.minute)

            if datetimeObj.hour == 0:
                datetime_str = "12{}am".format(datetime_str)
            elif datetimeObj.hour == 12:
                datetime_str = "12{}pm".format(datetime_str)
            elif datetimeObj.hour > 12:
                datetime_str = "{}{}pm".format(str(datetimeObj.hour % 12), datetime_str)
            else:
                datetime_str = "{}{}am".format(str(datetimeObj.hour), datetime_str)
        return datetime_str

    def process_inputs(
        self,
        current_time,
        current_weather,
        hourly_forecast,
        daily_forecast,
        events,
        path_to_server_image,
    ):
        # Read html template
        with open(self.currPath + "/dashboard_template.html", "r") as file:
            dashboard_template = file.read()

        current_date = current_time.date()

        # Populate the date and events
        cal_events_days = []
        cal_events_list = []
        for d, e in events:
            cal_events_text = ""
            for event in e:
                cal_events_text += '<div class="event">'
                if event["isMultiday"] or event["allday"]:
                    cal_events_text += event["summary"]
                else:
                    cal_events_text += (
                        '<span class="event-time">'
                        + self.get_short_time(event["startDatetime"])
                        + "</span> "
                        + event["summary"]
                    )
                    if "location" in event:
                        cal_events_text += (
                            '<span class="event-location"> at ' + event["location"] + "</span>"
                        )
                cal_events_text += "</div>\n"
            if d == current_date:
                cal_events_days.append("Today")
            elif d == current_date + dt.timedelta(days=1):
                cal_events_days.append("Tomorrow")
            else:
                cal_events_days.append(d.strftime("%A (%B %-d)"))
            cal_events_list.append(cal_events_text)

        if len(cal_events_days) == 0:
            cal_events_days.append("Next Days")
            cal_events_list.append(
                '<div class="event"><span class="event-time">No Events</span></div>'
            )

        self.extend_list(cal_events_days, self.cfg.NUM_DAYS_IN_TEMPLATE, "")
        self.extend_list(cal_events_list, self.cfg.NUM_DAYS_IN_TEMPLATE, "")

        weather_add_info = "&nbsp;"
        if self.cfg.SHOW_ADDITIONAL_WEATHER:
            if round(current_weather["temp"]) != round(current_weather["feels_like"]):
                weather_add_info = f'Feels Like {round(current_weather["feels_like"])}°'
            if (current_weather["sunrise"] < current_weather["dt"]) and (
                current_weather["dt"] < current_weather["sunset"]
            ):
                if weather_add_info != "":
                    weather_add_info += " | "
                weather_add_info += f'UV Index {round(current_weather["uvi"])}'

        today_moon_phase = ""
        if self.cfg.SHOW_MOON_PHASE:
            today_moon_phase = self.wi_moon_phase(daily_forecast[0]['moon_phase'])

        # Append the bottom and write the file
        htmlFile = open(self.currPath + "/dashboard.html", "w")
        htmlFile.write(
            dashboard_template.format(
                update_time=current_time.strftime("%x %H:%M"),
                day=current_date.strftime("%-d"),
                month=current_date.strftime("%B"),
                weekday=current_date.strftime("%A"),
                dayaftertomorrow=(current_date + dt.timedelta(days=2)).strftime("%A"),
                cal_day_1=cal_events_days[0],
                cal_day_2=cal_events_days[1],
                cal_day_3=cal_events_days[2],
                cal_day_4=cal_events_days[3],
                cal_day_5=cal_events_days[4],
                cal_day_6=cal_events_days[5],
                cal_day_1_events=cal_events_list[0],
                cal_day_2_events=cal_events_list[1],
                cal_day_3_events=cal_events_list[2],
                cal_day_4_events=cal_events_list[3],
                cal_day_5_events=cal_events_list[4],
                cal_day_6_events=cal_events_list[5],
                # I'm choosing to show the forecast for the next hour instead of the current weather
                current_weather_text=string.capwords(current_weather["weather"][0]["description"]),
                current_weather_id=current_weather["weather"][0]["id"],
                current_weather_temp=f'{round(current_weather["temp"])}°',
                current_weather_add_info=weather_add_info,
                today_weather_id=daily_forecast[0]["weather"][0]["id"],
                tomorrow_weather_id=daily_forecast[1]["weather"][0]["id"],
                dayafter_weather_id=daily_forecast[2]["weather"][0]["id"],
                today_weather_pop=str(round(daily_forecast[0]["pop"] * 100)),
                tomorrow_weather_pop=str(round(daily_forecast[1]["pop"] * 100)),
                dayafter_weather_pop=str(round(daily_forecast[2]["pop"] * 100)),
                today_weather_min=str(round(daily_forecast[0]["temp"]["min"])),
                tomorrow_weather_min=str(round(daily_forecast[1]["temp"]["min"])),
                dayafter_weather_min=str(round(daily_forecast[2]["temp"]["min"])),
                today_weather_max=str(round(daily_forecast[0]["temp"]["max"])),
                tomorrow_weather_max=str(round(daily_forecast[1]["temp"]["max"])),
                dayafter_weather_max=str(round(daily_forecast[2]["temp"]["max"])),
                today_moon_phase=today_moon_phase,
            )
        )
        htmlFile.close()

        self.get_screenshot(path_to_server_image)

    def extend_list(self, my_list, new_length, default_value):
        return my_list.extend([default_value] * (new_length - len(my_list)))

    def wi_moon_phase(self, value):
        """
        This function translates a number representing the phase of the moon as returned by the
        OpenWeatherMap API into the equivalent Weather Icon name. The input value should be between
        0 and 1, inclusive, where 0 and 1 represents a new moon, 0.25 represents a first quarter
        moon, 0.5 represents a full moon, and 0.75 represents a last quarter moon.
        """

        phases = {
            0.0: "wi-moon-new",
            0.25: "wi-moon-first-quarter",
            0.5: "wi-moon-full",
            0.75: "wi-moon-third-quarter",
            1.0: "wi-moon-new",
        }

        if value in phases:
            return phases[value]
        elif value < 0.25:
            return f"wi-moon-waxing-crescent-{int(6 * value / 0.25)}"
        elif value < 0.5:
            return f"wi-moon-waxing-gibbous-{int((value - 0.25) * 6 / 0.25 + 1)}"
        elif value < 0.75:
            return f"wi-moon-waning-gibbous-{int((value - 0.5) * 6 / 0.25 + 1)}"
        else:
            return f"wi-moon-waning-crescent-{int((value - 0.75) * 6 / 0.25 + 1)}"
