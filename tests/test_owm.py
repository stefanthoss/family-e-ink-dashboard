"""
Tests for the OpenWeatherMap module, focused on failure behaviour: the dashboard has to keep
rendering (with the weather block blanked out) when the API cannot be used.
"""

import json
import os
import sys
from unittest.mock import patch

import pytest
import requests

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from owm.owm import OwmModule, WeatherUnits

API_KEY = "sup3rs3cret-owm-key"

GOOD_PAYLOAD = json.dumps(
    {
        "current": {
            "dt": 1730000000,
            "temp": 20.5,
            "feels_like": 19.0,
            "sunrise": 1729990000,
            "sunset": 1730020000,
            "uvi": 3,
            "weather": [{"id": 800, "description": "clear sky"}],
        },
        "hourly": [{"dt": 1730000000, "temp": 20.0}],
        "daily": [
            {
                "dt": 1730000000,
                "moon_phase": 0.5,
                "pop": 0.4,
                "temp": {"min": 12.2, "max": 21.6},
                "weather": [{"id": 800, "description": "clear sky"}],
            }
        ]
        * 3,
    }
)


def make_response(status_code: int, body: str) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response._content = body.encode("utf-8")
    response.url = "https://api.openweathermap.org/data/3.0/onecall"
    response.reason = "Error"
    return response


@pytest.fixture
def owm_module():
    return OwmModule()


class TestGetWeather:
    @patch("owm.owm.requests.get")
    def test_returns_the_forecast_on_success(self, mock_get, owm_module):
        mock_get.return_value = make_response(200, GOOD_PAYLOAD)
        current, hourly, daily = owm_module.get_weather(
            27.0, -122.0, API_KEY, WeatherUnits.imperial
        )

        assert current["temp"] == 20.5
        assert len(hourly) == 1
        assert len(daily) == 3

    @patch("owm.owm.requests.get")
    def test_request_uses_a_timeout(self, mock_get, owm_module):
        """Without a timeout a hanging OWM request stalls the whole /image endpoint."""
        mock_get.return_value = make_response(200, GOOD_PAYLOAD)
        owm_module.get_owm_weather(27.0, -122.0, API_KEY, WeatherUnits.metric)

        assert mock_get.call_args.kwargs.get("timeout")

    @pytest.mark.parametrize(
        "response",
        [
            make_response(401, '{"cod":401,"message":"Invalid API key"}'),
            make_response(429, '{"message":"Your account is not subscribed"}'),
            make_response(500, "<html><body>Bad gateway</body></html>"),
        ],
    )
    @patch("owm.owm.requests.get")
    def test_error_response_yields_empty_structures(self, mock_get, owm_module, response):
        """Regression test: this used to raise KeyError and 500 the dashboard image."""
        mock_get.side_effect = requests.exceptions.HTTPError("error", response=response)
        current, hourly, daily = owm_module.get_weather(27.0, -122.0, API_KEY, WeatherUnits.metric)

        assert current == {}
        assert hourly == []
        assert daily == []

    @patch("owm.owm.requests.get")
    def test_connection_error_yields_empty_structures(self, mock_get, owm_module):
        mock_get.side_effect = requests.exceptions.ConnectionError("no route to host")
        current, _, daily = owm_module.get_weather(27.0, -122.0, API_KEY, WeatherUnits.metric)

        assert current == {}
        assert daily == []

    @pytest.mark.parametrize(
        "body",
        [
            "not json at all",
            json.dumps({"cod": 401, "message": "Invalid API key"}),  # 200 + error payload
            json.dumps({"current": {"temp": 20.0}, "hourly": []}),  # no "daily"
        ],
    )
    @patch("owm.owm.requests.get")
    def test_unexpected_payload_yields_empty_structures(self, mock_get, owm_module, body):
        mock_get.return_value = make_response(200, body)
        current, _, daily = owm_module.get_weather(27.0, -122.0, API_KEY, WeatherUnits.metric)

        assert current == {}
        assert daily == []

    @patch("owm.owm.requests.get")
    def test_api_key_never_appears_in_logs(self, mock_get, owm_module):
        mock_get.side_effect = requests.exceptions.ConnectionError(
            f"Max retries exceeded with url: /data/3.0/onecall?lat=27&lon=-122&appid={API_KEY}"
        )

        with patch.object(owm_module, "logger") as mock_logger:
            owm_module.get_weather(27.0, -122.0, API_KEY, WeatherUnits.metric)
            owm_module.get_owm_weather(27.0, -122.0, API_KEY, WeatherUnits.metric)

        logged = str(mock_logger.method_calls)
        assert API_KEY not in logged
