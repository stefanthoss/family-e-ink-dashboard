"""
Tests for the redact module.
"""

import os
import sys

import pytest
import requests

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from redact import safe_url, status_of

FEED_URL = (
    "https://calendar.proton.me/api/calendar/v1/url/SECRETTOKEN/calendar.ics"
    "?PassphraseKey=SECRETPASSPHRASE%3D"
)


class TestSafeUrl:
    """Test suite for the safe_url function."""

    def test_keeps_only_a_short_prefix(self):
        assert safe_url(FEED_URL) == "https://calendar.pro…"

    def test_never_contains_the_token_or_passphrase(self):
        for secret in ("SECRETTOKEN", "SECRETPASSPHRASE", "PassphraseKey"):
            assert secret not in safe_url(FEED_URL)

    def test_short_urls_are_returned_unchanged(self):
        assert safe_url("short.ics") == "short.ics"

    def test_configurable_length(self):
        assert safe_url(FEED_URL, 30) == "https://calendar.proton.me/api…"


class TestStatusOf:
    """Test suite for the status_of function."""

    def test_returns_the_status_code_of_an_http_error(self):
        response = requests.Response()
        response.status_code = 422
        error = requests.exceptions.HTTPError("422 Error", response=response)

        assert status_of(error) == 422

    @pytest.mark.parametrize(
        "error",
        [
            requests.exceptions.ConnectionError("no route to host"),
            requests.exceptions.Timeout("timed out"),
            ValueError("not a calendar"),
        ],
    )
    def test_returns_none_when_the_request_never_got_a_response(self, error):
        assert status_of(error) is None
