import os
import sys
from unittest.mock import patch

import pytest

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config import DashboardConfig
from owm.owm import WeatherUnits


class TestDashboardConfig:
    """Test suite for DashboardConfig class."""

    def setup_method(self):
        """Clear any existing global config before each test."""
        import config

        config._current_config = None

    @patch.dict(
        os.environ,
        {
            "ICS_URL": "https://example.com/calendar.ics",
            "OWM_API_KEY": "test_api_key",
            "LAT": "37.7749",
            "LNG": "-122.4194",
        },
        clear=True,
    )
    def test_init_with_minimal_required_env_vars(self):
        """Test DashboardConfig initialization with only required environment variables."""
        config = DashboardConfig()

        # Required variables
        assert config.ICS_URL == "https://example.com/calendar.ics"
        assert config.OWM_API_KEY == "test_api_key"
        assert config.LAT == 37.7749
        assert config.LNG == -122.4194

        # Default values
        assert config.DISPLAY_TZ == "America/Los_Angeles"
        assert config.NUM_CAL_DAYS_TO_QUERY == 30
        assert config.IMAGE_WIDTH == 1200
        assert config.IMAGE_HEIGHT == 825
        assert config.WEATHER_UNITS == WeatherUnits.metric
        assert config.SHOW_ADDITIONAL_WEATHER == False
        assert config.SHOW_MOON_PHASE == False

    @patch.dict(
        os.environ,
        {
            "ICS_URL": "https://example.com/calendar.ics",
            "OWM_API_KEY": "test_api_key",
            "LAT": "40.7128",
            "LNG": "-74.0060",
            "DISPLAY_TZ": "America/New_York",
            "NUM_CAL_DAYS_TO_QUERY": "45",
            "IMAGE_WIDTH": "1600",
            "IMAGE_HEIGHT": "900",
            "WEATHER_UNITS": "imperial",
            "SHOW_ADDITIONAL_WEATHER": "true",
            "SHOW_MOON_PHASE": "True",
            "ICS_PREFIX": "|School:",
            "ICS_HIDE_LOCATION": "true",
        },
        clear=True,
    )
    def test_init_with_all_env_vars_set(self):
        """Test DashboardConfig initialization with all environment variables set."""
        config = DashboardConfig()

        assert config.ICS_URL == "https://example.com/calendar.ics"
        assert config.OWM_API_KEY == "test_api_key"
        assert config.LAT == 40.7128
        assert config.LNG == -74.0060
        assert config.DISPLAY_TZ == "America/New_York"
        assert config.NUM_CAL_DAYS_TO_QUERY == 45
        assert config.IMAGE_WIDTH == 1600
        assert config.IMAGE_HEIGHT == 900
        assert config.WEATHER_UNITS == WeatherUnits.imperial
        assert config.SHOW_ADDITIONAL_WEATHER == True
        assert config.SHOW_MOON_PHASE == True
        assert config.ICS_PREFIX == "|School:"
        assert config.ICS_HIDE_LOCATION == "true"

    @patch.dict(os.environ, {}, clear=True)
    @patch("config.logger")
    def test_missing_ics_url_exits(self, mock_logger):
        """Test that missing ICS_URL causes system exit."""
        with pytest.raises(SystemExit) as exc_info:
            DashboardConfig()

        assert exc_info.value.code == 1
        mock_logger.error.assert_called_with("ICS_URL needs to be set.")

    @patch.dict(os.environ, {"ICS_URL": "https://example.com/calendar.ics"}, clear=True)
    @patch("config.logger")
    def test_missing_owm_api_key_exits(self, mock_logger):
        """Test that missing OWM_API_KEY causes system exit."""
        with pytest.raises(SystemExit) as exc_info:
            DashboardConfig()

        assert exc_info.value.code == 1
        mock_logger.error.assert_called_with("OWM_API_KEY needs to be set.")

    @patch.dict(
        os.environ,
        {"ICS_URL": "https://example.com/calendar.ics", "OWM_API_KEY": "test_api_key"},
        clear=True,
    )
    @patch("config.logger")
    def test_missing_lat_lng_exits(self, mock_logger):
        """Test that missing LAT and LNG causes system exit."""
        with pytest.raises(SystemExit) as exc_info:
            DashboardConfig()

        assert exc_info.value.code == 1
        mock_logger.error.assert_called_with("LAT and LNG need to be set.")

    @patch.dict(
        os.environ,
        {
            "ICS_URL": "https://example.com/calendar.ics",
            "OWM_API_KEY": "test_api_key",
            "LAT": "37.7749",
        },
        clear=True,
    )
    @patch("config.logger")
    def test_missing_lng_only_exits(self, mock_logger):
        """Test that missing only LNG (with LAT present) causes system exit."""
        with pytest.raises(SystemExit) as exc_info:
            DashboardConfig()

        assert exc_info.value.code == 1
        mock_logger.error.assert_called_with("LAT and LNG need to be set.")

    @patch.dict(
        os.environ,
        {
            "ICS_URL": "https://example.com/calendar.ics",
            "OWM_API_KEY": "test_api_key",
            "LNG": "-122.4194",
        },
        clear=True,
    )
    @patch("config.logger")
    def test_missing_lat_only_exits(self, mock_logger):
        """Test that missing only LAT (with LNG present) causes system exit."""
        with pytest.raises(SystemExit) as exc_info:
            DashboardConfig()

        assert exc_info.value.code == 1
        mock_logger.error.assert_called_with("LAT and LNG need to be set.")

    @patch.dict(
        os.environ,
        {
            "ICS_URL": "https://example.com/calendar.ics",
            "OWM_API_KEY": "test_api_key",
            "LAT": "37.7749",
            "LNG": "-122.4194",
            "SHOW_ADDITIONAL_WEATHER": "true",
            "SHOW_MOON_PHASE": "TRUE",
        },
        clear=True,
    )
    def test_boolean_env_vars_true_values(self):
        """Test boolean environment variables with various true values."""
        config = DashboardConfig()

        assert config.SHOW_ADDITIONAL_WEATHER == True
        assert config.SHOW_MOON_PHASE == True

    @patch.dict(
        os.environ,
        {
            "ICS_URL": "https://example.com/calendar.ics",
            "OWM_API_KEY": "test_api_key",
            "LAT": "37.7749",
            "LNG": "-122.4194",
            "SHOW_ADDITIONAL_WEATHER": "false",
            "SHOW_MOON_PHASE": "False",
        },
        clear=True,
    )
    def test_boolean_env_vars_false_values(self):
        """Test boolean environment variables with various false values."""
        config = DashboardConfig()

        assert config.SHOW_ADDITIONAL_WEATHER == False
        assert config.SHOW_MOON_PHASE == False

    @patch.dict(
        os.environ,
        {
            "ICS_URL": "https://example.com/calendar.ics",
            "OWM_API_KEY": "test_api_key",
            "LAT": "-90.0",
            "LNG": "180.0",
        },
        clear=True,
    )
    def test_extreme_lat_lng_values(self):
        """Test with extreme but valid latitude and longitude values."""
        config = DashboardConfig()

        assert config.LAT == -90.0
        assert config.LNG == 180.0

    @patch.dict(
        os.environ,
        {
            "ICS_URL": "https://example.com/calendar.ics",
            "OWM_API_KEY": "test_api_key",
            "LAT": "37.7749",
            "LNG": "-122.4194",
            "WEATHER_UNITS": "metric",
        },
        clear=True,
    )
    def test_weather_units_metric(self):
        """Test WEATHER_UNITS with metric value."""
        config = DashboardConfig()
        assert config.WEATHER_UNITS == WeatherUnits.metric

    @patch.dict(
        os.environ,
        {
            "ICS_URL": "https://example.com/calendar.ics",
            "OWM_API_KEY": "test_api_key",
            "LAT": "37.7749",
            "LNG": "-122.4194",
            "WEATHER_UNITS": "imperial",
        },
        clear=True,
    )
    def test_weather_units_imperial(self):
        """Test WEATHER_UNITS with imperial value."""
        config = DashboardConfig()
        assert config.WEATHER_UNITS == WeatherUnits.imperial

    @patch.dict(
        os.environ,
        {
            "ICS_URL": "https://example.com/calendar.ics",
            "OWM_API_KEY": "test_api_key",
            "LAT": "37.7749",
            "LNG": "-122.4194",
            "NUM_CAL_DAYS_TO_QUERY": "0",
            "IMAGE_WIDTH": "1",
            "IMAGE_HEIGHT": "1",
        },
        clear=True,
    )
    def test_integer_edge_cases(self):
        """Test integer environment variables with edge case values."""
        config = DashboardConfig()

        assert config.NUM_CAL_DAYS_TO_QUERY == 0
        assert config.IMAGE_WIDTH == 1
        assert config.IMAGE_HEIGHT == 1

    @patch("config.DashboardConfig.__init__")
    def test_get_config_singleton_pattern(self, mock_init):
        """Test that get_config() implements singleton pattern correctly."""
        mock_init.return_value = None

        # First call should create instance
        config1 = DashboardConfig.get_config()
        assert mock_init.call_count == 1

        # Second call should return same instance
        config2 = DashboardConfig.get_config()
        assert mock_init.call_count == 1  # Should not be called again
        assert config1 is config2

    def test_get_config_returns_same_instance(self):
        """Test that get_config returns the same instance on multiple calls."""
        with patch.dict(
            os.environ,
            {
                "ICS_URL": "https://example.com/calendar.ics",
                "OWM_API_KEY": "test_api_key",
                "LAT": "37.7749",
                "LNG": "-122.4194",
            },
            clear=True,
        ):
            config1 = DashboardConfig.get_config()
            config2 = DashboardConfig.get_config()

            assert config1 is config2
            assert id(config1) == id(config2)


class TestPerFeedOptions:
    """ICS_URL and its two per feed options are read once, when the config is built."""

    @pytest.mark.parametrize(
        ("ics_url", "expected"),
        [
            ("https://example.com/a.ics", ["https://example.com/a.ics"]),
            (
                "https://example.com/a.ics|https://example.com/b.ics",
                ["https://example.com/a.ics", "https://example.com/b.ics"],
            ),
            ("  |https://example.com/a.ics| ", ["https://example.com/a.ics"]),
            ("| |", []),
        ],
    )
    def test_split_feeds(self, ics_url, expected):
        assert DashboardConfig.split_feeds(ics_url) == expected

    @pytest.mark.parametrize(
        ("entry", "expected"),
        [
            ("School:", "School: "),
            ("School", "School "),
            ("  School:  ", "School: "),
            ('"School:"', "School: "),
            ("", ""),
            ("   ", ""),
        ],
    )
    def test_parse_prefix(self, entry, expected):
        assert DashboardConfig.parse_prefix(entry) == expected

    @pytest.mark.parametrize("entry", ["true", "True", "TRUE", '"true"', " true "])
    def test_parse_bool_reads_true(self, entry):
        assert DashboardConfig.parse_bool(entry) is True

    @pytest.mark.parametrize(
        "entry", ["false", "False", "FALSE", "", "  ", "maybe", "yes", "on", "1", "0"]
    )
    def test_parse_bool_reads_false(self, entry):
        assert DashboardConfig.parse_bool(entry) is False

    @patch.dict(
        os.environ,
        {
            "ICS_URL": "https://a.ics|https://b.ics",
            "OWM_API_KEY": "test_api_key",
            "LAT": "1",
            "LNG": "1",
            "ICS_PREFIX": "|School:",
            "ICS_HIDE_LOCATION": "false|TRUE",
        },
        clear=True,
    )
    def test_every_entry_belongs_to_its_own_feed(self):
        config = DashboardConfig()

        assert config.ICS_FEED_URLS == ["https://a.ics", "https://b.ics"]
        assert config.ICS_PREFIXES == ["", "School: "]
        assert config.ICS_HIDE_LOCATIONS == [False, True]

    @patch.dict(
        os.environ,
        {
            "ICS_URL": "https://a.ics|https://b.ics|https://c.ics",
            "OWM_API_KEY": "test_api_key",
            "LAT": "1",
            "LNG": "1",
            "ICS_PREFIX": "Home:",
            "ICS_HIDE_LOCATION": "true|true|true|true",
        },
        clear=True,
    )
    @patch("config.logger")
    def test_a_list_that_does_not_line_up_is_used_as_far_as_it_reaches(self, mock_logger):
        config = DashboardConfig()

        assert config.ICS_PREFIXES == ["Home: ", "", ""]
        assert config.ICS_HIDE_LOCATIONS == [True, True, True]
        warnings = [call.args[0] for call in mock_logger.warning.call_args_list]
        assert "ICS_PREFIX does not match ICS_URL (1 entry / 3 feed(s))" in warnings[0]
        assert "the last 2 feed(s) use the default" in warnings[0]
        assert "ICS_HIDE_LOCATION does not match ICS_URL (4 entries / 3 feed(s))" in warnings[1]
        assert "ignoring the extra 1" in warnings[1]

    @patch.dict(
        os.environ,
        {
            "ICS_URL": "https://a.ics|https://b.ics",
            "OWM_API_KEY": "test_api_key",
            "LAT": "1",
            "LNG": "1",
        },
        clear=True,
    )
    @patch("config.logger")
    def test_absent_options_stay_silent(self, mock_logger):
        config = DashboardConfig()

        assert config.ICS_PREFIXES == ["", ""]
        assert config.ICS_HIDE_LOCATIONS == [False, False]
        mock_logger.warning.assert_not_called()
