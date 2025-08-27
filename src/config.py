import os
import sys
from typing import Optional

import structlog

from owm.owm import WeatherUnits

logger = structlog.get_logger()

_current_config: Optional["DashboardConfig"] = None


class DashboardConfig:
    def __init__(self) -> None:
        ics_url = os.getenv("ICS_URL")
        if not ics_url:
            logger.error("ICS_URL needs to be set.")
            sys.exit(1)
        self.ICS_URL: str = ics_url

        owm_api_key = os.getenv("OWM_API_KEY")
        if not owm_api_key:
            logger.error("OWM_API_KEY needs to be set.")
            sys.exit(1)
        self.OWM_API_KEY: str = owm_api_key

        if os.getenv("LAT") and os.getenv("LNG"):
            self.LAT: float = float(os.getenv("LAT"))
            self.LNG: float = float(os.getenv("LNG"))
        else:
            logger.error("LAT and LNG need to be set.")
            sys.exit(1)

        self.DISPLAY_TZ: str = os.getenv("DISPLAY_TZ", "America/Los_Angeles")
        self.NUM_CAL_DAYS_TO_QUERY: int = int(os.getenv("NUM_CAL_DAYS_TO_QUERY", "30"))
        self.IMAGE_WIDTH: int = int(os.getenv("IMAGE_WIDTH", "1200"))
        self.IMAGE_HEIGHT: int = int(os.getenv("IMAGE_HEIGHT", "825"))
        self.WEATHER_UNITS: WeatherUnits = WeatherUnits[os.getenv("WEATHER_UNITS", "metric")]
        self.SHOW_ADDITIONAL_WEATHER: bool = (
            os.getenv("SHOW_ADDITIONAL_WEATHER", "False").lower() == "true"
        )
        self.SHOW_MOON_PHASE: bool = os.getenv("SHOW_MOON_PHASE", "False").lower() == "true"
        self.SHOW_CALENDAR_NAME: bool = os.getenv("SHOW_CALENDAR_NAME", "False").lower() == "true"

    @classmethod
    def get_config(cls) -> "DashboardConfig":
        global _current_config
        if _current_config is None:
            _current_config = DashboardConfig()
        return _current_config
