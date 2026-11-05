"""
This is where we retrieve weather forecast from OpenWeatherMap. Before doing so, make sure you have both the
signed up for an OWM account and also obtained a valid API key that is specified in the config.json file.
"""

import json
from enum import Enum
from typing import Any

import requests
import structlog

from redact import safe_url, status_of


class WeatherUnits(str, Enum):
    metric = "metric"
    imperial = "imperial"


class OwmModule:
    def __init__(self) -> None:
        self.logger = structlog.get_logger()

    def get_owm_weather(
        self, lat: float, lon: float, api_key: str, units: WeatherUnits
    ) -> dict[str, Any]:
        results: dict[str, Any] = {}

        url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={api_key}&exclude=minutely,alerts&units={units.value}"
        # The API key is part of the URL, so it must never be logged verbatim.
        label = safe_url(url)
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = json.loads(response.text)
        except requests.exceptions.RequestException as e:
            # Not the exception message: requests embeds the URL, API key included.
            status = status_of(e)
            detail = f"HTTP {status}" if status else type(e).__name__
            self.logger.error(f"OpenWeatherMap request failed at {label}: {detail}")
            return results
        except ValueError:
            self.logger.error(f"OpenWeatherMap response at {label} was not valid JSON.")
            return results

        if not isinstance(data, dict) or not all(
            key in data for key in ("current", "hourly", "daily")
        ):
            # OpenWeatherMap sometimes answers 200 with an error payload or a partial
            # forecast, notably around the 2.5 -> 3.0 (OneCall) API switch.
            self.logger.error(f"OpenWeatherMap sent an unexpected payload at {label}.")
            return results

        results["current_weather"] = data["current"]
        results["hourly_forecast"] = data["hourly"]
        results["daily_forecast"] = data["daily"]

        return results

    def get_weather(
        self,
        lat: float,
        lon: float,
        owm_api_key: str,
        units: WeatherUnits,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Retrieve the weather, falling back to empty structures when OpenWeatherMap cannot be
        used. Weather is optional for the dashboard: a failed request must only blank out the
        weather block, not the whole page (which is what indexing the result did before).
        """
        weather_results = self.get_owm_weather(lat, lon, owm_api_key, units)

        return (
            weather_results.get("current_weather") or {},
            weather_results.get("hourly_forecast") or [],
            weather_results.get("daily_forecast") or [],
        )
