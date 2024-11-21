import logging
import os
import sys

from pytz import timezone

from owm.owm import WeatherUnits

logger = logging.getLogger('maginkdash')

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
    DISPLAY_TZ: timezone = timezone(os.getenv("DISPLAY_TZ", "America/Los_Angeles"))
    NUM_CAL_DATS_TO_SHOW: int = int(os.getenv("NUM_CAL_DATS_TO_SHOW", 5))
    IMAGE_WIDTH: int = int(os.getenv("IMAGE_WIDTH", 1200))
    IMAGE_HEIGHT: int = int(os.getenv("IMAGE_HEIGHT", 825))
    ROTATE_ANGLE: int = int(os.getenv("ROTATE_ANGLE", 0))
    LAT: float = float(os.getenv("LAT", 34.118333))
    LNG: float = float(os.getenv("LNG", -118.300333))
    WEATHER_UNITS: WeatherUnits = WeatherUnits[os.getenv("WEATHER_UNITS", "metric")]

    def get_config():
        global _current_config
        if _current_config is None:
            _current_config = MagInkDashConfig()
        return _current_config
