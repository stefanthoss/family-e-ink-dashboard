import os
import sys

import structlog

from owm.owm import WeatherUnits

logger = structlog.get_logger()

_current_config: DashboardConfig | None = None


class DashboardConfig:
    def __init__(self) -> None:
        ics_url = os.getenv("ICS_URL")
        if not ics_url:
            logger.error("ICS_URL needs to be set.")
            sys.exit(1)
        self.ICS_URL: str = ics_url
        self.ICS_PREFIX: str = os.getenv("ICS_PREFIX", "")
        self.ICS_HIDE_LOCATION: str = os.getenv("ICS_HIDE_LOCATION", "")

        self.ICS_FEED_URLS: list[str] = self.split_feeds(ics_url)
        feeds = len(self.ICS_FEED_URLS)
        self.ICS_PREFIXES: list[str] = [
            self.parse_prefix(entry)
            for entry in self.align_options(self.ICS_PREFIX, "ICS_PREFIX", feeds)
        ]
        self.ICS_HIDE_LOCATIONS: list[bool] = [
            self.parse_bool(entry)
            for entry in self.align_options(self.ICS_HIDE_LOCATION, "ICS_HIDE_LOCATION", feeds)
        ]

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
        self.IMAGE_HEIGHT: int = int(os.getenv("IMAGE_HEIGHT", "825"))
        self.IMAGE_WIDTH: int = int(os.getenv("IMAGE_WIDTH", "1200"))
        self.NUM_CAL_DAYS_TO_QUERY: int = int(os.getenv("NUM_CAL_DAYS_TO_QUERY", "30"))
        self.SHOW_ADDITIONAL_WEATHER: bool = (
            os.getenv("SHOW_ADDITIONAL_WEATHER", "False").lower() == "true"
        )
        self.SHOW_MOON_PHASE: bool = os.getenv("SHOW_MOON_PHASE", "False").lower() == "true"
        self.USE_24H_FORMAT: bool = os.getenv("USE_24H_FORMAT", "True").lower() == "true"
        self.WEATHER_UNITS: WeatherUnits = WeatherUnits[os.getenv("WEATHER_UNITS", "metric")]

    @classmethod
    def get_config(cls) -> DashboardConfig:
        global _current_config
        if _current_config is None:
            _current_config = DashboardConfig()
        return _current_config

    @staticmethod
    def split_feeds(ics_url: str) -> list[str]:
        """Several calendars share one variable, separated by a pipe. A blank entry is not a feed."""
        urls = [single_url.strip() for single_url in ics_url.split("|")]
        return [single_url for single_url in urls if single_url]

    @staticmethod
    def warn_if_mismatch(name: str, entries: int, feeds: int) -> None:
        """Use an option list as far as it reaches, but say that it does not line up."""
        if entries == 0 or entries == feeds:
            return
        entry_word = "entry" if entries == 1 else "entries"
        mismatch = f"{name} does not match ICS_URL ({entries} {entry_word} / {feeds} feed(s))"
        if entries > feeds:
            logger.warning(f"{mismatch}, ignoring the extra {entries - feeds}.")
        else:
            logger.warning(f"{mismatch}, the last {feeds - entries} feed(s) use the default.")

    @staticmethod
    def align_options(raw: str, name: str, feeds: int) -> list[str]:
        """One entry per feed. Empty entries are kept so that entry n still belongs to feed n, and
        an option that is not set at all is not worth a warning."""
        if not raw:
            return [""] * feeds
        entries = raw.split("|")
        DashboardConfig.warn_if_mismatch(name, len(entries), feeds)
        return entries[:feeds] + [""] * max(feeds - len(entries), 0)

    @staticmethod
    def parse_prefix(entry: str) -> str:
        """A prefix is always followed by a space, so "School:" reads "School: Math Exam"."""
        prefix = entry.strip().strip("\"'")
        return f"{prefix} " if prefix else ""

    @staticmethod
    def parse_bool(entry: str) -> bool:
        """Reads "true" in any capitalisation, everything else is the default."""
        return entry.strip().strip("\"'").lower() == "true"
