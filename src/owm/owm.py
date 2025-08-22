"""
This is where we retrieve weather forecast from OpenWeatherMap. Before doing so, make sure you have both the
signed up for an OWM account and also obtained a valid API key that is specified in the config.json file.
"""

import json
import sys
from enum import Enum
from typing import Any, Dict, List, Tuple

import requests
import structlog


class WeatherUnits(str, Enum):
    metric = "metric"
    imperial = "imperial"


class OwmModule:
    def __init__(self) -> None:
        self.logger = structlog.get_logger()

    def get_owm_weather(
        self, lat: float, lon: float, api_key: str, units: WeatherUnits
    ) -> Dict[str, Any]:
        url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={api_key}&exclude=minutely,alerts&units={units.value}"
        response = requests.get(url)

        if response.ok:
            data = json.loads(response.text)
            curr_weather = data["current"]
            hourly_forecast = data["hourly"]
            daily_forecast = data["daily"]
            results = {
                "current_weather": curr_weather,
                "hourly_forecast": hourly_forecast,
                "daily_forecast": daily_forecast,
            }
            return results
        else:
            self.logger.error(f"OpenWeatherMap returned error: {response.text}")
            sys.exit(1)

    def get_weather(
        self,
        lat: float,
        lon: float,
        owm_api_key: str,
        units: WeatherUnits,
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
        weather_results = self.get_owm_weather(lat, lon, owm_api_key, units)
        current_weather = weather_results["current_weather"]
        hourly_forecast = weather_results["hourly_forecast"]
        daily_forecast = weather_results["daily_forecast"]

        return current_weather, hourly_forecast, daily_forecast
