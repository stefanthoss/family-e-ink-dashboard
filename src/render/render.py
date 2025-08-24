"""
This script essentially generates a HTML file of the calendar I wish to display. It then fires up a headless Chrome
instance, sized to the resolution of the eInk display and takes a screenshot.
"""

import datetime as dt
import os
import pathlib
import string
import subprocess
from time import sleep
from typing import Any, Dict, List, Tuple

import structlog
from jinja2 import Environment, FileSystemLoader
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from config import DashboardConfig


class RenderHelper:
    def __init__(self, cfg: DashboardConfig) -> None:
        self.logger = structlog.get_logger()
        self.currPath = str(pathlib.Path(__file__).parent.absolute())
        self.htmlFile = "file://" + self.currPath + "/dashboard.html"
        self.cfg = cfg

    def set_viewport_size(self, driver: webdriver.Chrome) -> None:
        # Extract the current window size from the driver
        current_window_size = driver.get_window_size()

        # Extract the client window size from the html tag
        html = driver.find_element(By.TAG_NAME, "html")
        inner_width = int(html.get_attribute("clientWidth"))
        inner_height = int(html.get_attribute("clientHeight"))

        # "Internal width you want to set+Set "outer frame width" to window size
        target_width = self.cfg.IMAGE_WIDTH + (
            current_window_size["width"] - inner_width
        )
        target_height = self.cfg.IMAGE_HEIGHT + (
            current_window_size["height"] - inner_height
        )

        driver.set_window_rect(width=target_width, height=target_height)

    def get_screenshot(self, path_to_server_image: str) -> None:
        opts = Options()
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--force-device-scale-factor=1")
        opts.add_argument("--headless")
        opts.add_argument("--hide-scrollbars")
        opts.add_argument("--no-sandbox")

        # Try to automatically locate chromedriver, source: https://github.com/fdmarcin/MagInkDash-updated
        try:
            chromedriver_path = (
                subprocess.check_output(["which", "chromedriver"])
                .decode("utf-8")
                .strip()
            )
            self.logger.info(f"Found chromedriver at: {chromedriver_path}")
        except (subprocess.SubprocessError, FileNotFoundError):
            # Default paths to try if 'which' command fails
            possible_paths = [
                "/usr/bin/chromedriver",
                "/usr/local/bin/chromedriver",
                "/usr/lib/chromium-browser/chromedriver",
            ]

            chromedriver_path = None
            for path in possible_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    chromedriver_path = path
                    self.logger.info(
                        f"Found chromedriver at default location: {chromedriver_path}"
                    )
                    break

            if not chromedriver_path:
                self.logger.error(
                    "Could not find chromedriver. Please install it with 'sudo apt-get install chromium-chromedriver'"
                )
                raise FileNotFoundError("chromedriver executable not found in PATH")

        # Use the discovered chromedriver path
        service = Service(chromedriver_path)

        try:
            driver = webdriver.Chrome(service=service, options=opts)
            self.set_viewport_size(driver)
            driver.get(self.htmlFile)
            sleep(1)
            driver.get_screenshot_as_file(self.currPath + "/dashboard.png")
            driver.get_screenshot_as_file(path_to_server_image)
            driver.quit()  # Make sure to quit the driver to free resources
            self.logger.debug(
                f"Screenshot captured and saved to file {path_to_server_image}."
            )
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {str(e)}")
            raise

    def format_time(self, datetimeObj: dt.datetime) -> str:
        if self.cfg.USE_24H_FORMAT:
            return datetimeObj.strftime("%H:%M")
        else:
            return datetimeObj.strftime("%I:%M%p")

    def process_inputs(
        self,
        current_time: dt.datetime,
        current_weather: Dict[str, Any],
        hourly_forecast: List[Dict[str, Any]],
        daily_forecast: List[Dict[str, Any]],
        events: List[Tuple[dt.date, List[Dict[str, Any]]]],
        path_to_server_image: str,
    ) -> None:
        # Read html template
        environment = Environment(loader=FileSystemLoader(self.currPath))
        dashboard_template = environment.get_template("dashboard_template.html.j2")

        current_date = current_time.date()

        # Populate the date and events
        cal_events_days: List[str] = []
        cal_events_list: List[str] = []
        for d, e in events:
            cal_events_text = ""
            for event in e:
                cal_events_text += '<div class="event">'
                if event["allday"]:
                    cal_events_text += event["summary"]
                else:
                    cal_events_text += (
                        '<span class="event-time">'
                        + self.format_time(event["startDatetime"])
                        + "</span> "
                        + event["summary"]
                    )
                # Some clients set the location to empty string
                if "location" in event and event["location"] != "":
                    cal_events_text += (
                        '<span class="event-location"> at '
                        + event["location"]
                        + "</span>"
                    )
                if self.cfg.SHOW_CALENDAR_NAME and event["calendarName"] is not None:
                    cal_events_text += (
                        '<span class="event-calendar-name"> ('
                        + event["calendarName"]
                        + ")</span>"
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

        self.extend_list(cal_events_days, self.cfg.NUM_CAL_DAYS_TO_QUERY, "")
        self.extend_list(cal_events_list, self.cfg.NUM_CAL_DAYS_TO_QUERY, "")

        weather_add_info = "&nbsp;"
        if self.cfg.SHOW_ADDITIONAL_WEATHER:
            additional_infos = []
            if round(current_weather["temp"]) != round(current_weather["feels_like"]):
                additional_infos.append(
                    f"Feels Like {round(current_weather['feels_like'])}°"
                )
            if (current_weather["sunrise"] < current_weather["dt"]) and (
                current_weather["dt"] < current_weather["sunset"]
            ):
                additional_infos.append(f"UV Index {round(current_weather['uvi'])}")
            weather_add_info = " | ".join(additional_infos)

        today_moon_phase = ""
        if self.cfg.SHOW_MOON_PHASE:
            today_moon_phase = self.wi_moon_phase(daily_forecast[0]["moon_phase"])

        # Append the bottom and write the file
        htmlFile = open(self.currPath + "/dashboard.html", "w")
        htmlFile.write(
            dashboard_template.render(
                update_time=f"{current_time.strftime('%B %-d')}, {self.format_time(current_time)}",
                day=current_date.strftime("%-d"),
                month=current_date.strftime("%B"),
                weekday=current_date.strftime("%A"),
                dayaftertomorrow=(current_date + dt.timedelta(days=2)).strftime("%A"),
                cal_days=cal_events_days,
                cal_days_events=cal_events_list,
                # I'm choosing to show the forecast for the next hour instead of the current weather
                current_weather_text=string.capwords(
                    current_weather["weather"][0]["description"]
                ),
                current_weather_id=current_weather["weather"][0]["id"],
                current_weather_temp=f"{round(current_weather['temp'])}°",
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

    def extend_list(
        self, my_list: List[str], new_length: int, default_value: str
    ) -> None:
        return my_list.extend([default_value] * (new_length - len(my_list)))

    def wi_moon_phase(self, value: float) -> str:
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
