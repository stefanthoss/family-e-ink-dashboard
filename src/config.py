import os
import sys

import structlog

from owm.owm import WeatherUnits

logger = structlog.get_logger()

_current_config = None


class MagInkDashConfig:
    ICS_URL: str = os.getenv("ICS_URL")
    if not ICS_URL:
        logger.error("ICS_URL needs to be set.")
        sys.exit(1)
    OWM_API_KEY: str = os.getenv("OWM_API_KEY")
    if not OWM_API_KEY:
        logger.error("OWM_API_KEY needs to be set.")
        sys.exit(1)
    DISPLAY_TZ: str = os.getenv("DISPLAY_TZ", "America/Los_Angeles")
    NUM_CAL_DAYS_TO_QUERY: int = int(os.getenv("NUM_CAL_DAYS_TO_QUERY", 30))
    IMAGE_WIDTH: int = int(os.getenv("IMAGE_WIDTH", 1200))
    IMAGE_HEIGHT: int = int(os.getenv("IMAGE_HEIGHT", 825))
    LAT: float = float(os.getenv("LAT", 34.118333))
    LNG: float = float(os.getenv("LNG", -118.300333))
    WEATHER_UNITS: WeatherUnits = WeatherUnits[os.getenv("WEATHER_UNITS", "metric")]
    NUM_DAYS_IN_TEMPLATE: int = 5  # Not configurable because it's hard-coded in the HTML template

    def get_config():
        global _current_config
        if _current_config is None:
            _current_config = MagInkDashConfig()
        return _current_config
