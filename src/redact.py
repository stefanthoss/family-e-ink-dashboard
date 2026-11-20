"""
Calendar feed and weather API URLs must never be logged in full: a subscription URL carries
the token and passphrase that unlock the calendar, and the OpenWeatherMap URL carries the API
key. ``requests`` also repeats the URL -- query string included -- inside its exception
messages, so those messages cannot be logged verbatim either.
"""


def safe_url(url: str, length: int = 20) -> str:
    """The first ``length`` characters of ``url``, which is all a log line needs to place it."""
    return url[:length] + ("…" if len(url) > length else "")


def status_of(error: Exception) -> int | None:
    """The HTTP status code of a failed request, if the request got that far."""
    status = getattr(getattr(error, "response", None), "status_code", None)
    return status if isinstance(status, int) else None
