"""
This project is designed for the Inkplate 10 display. However, since the server code is only generating an image, it can
be easily adapted to other display sizes and resolution by adjusting the config settings, HTML template and
CSS stylesheet.
"""

import datetime as dt
import tempfile
import time

import pytz
import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse

from config import DashboardConfig
from ics_cal.ics import IcsModule
from owm.owm import OWMModule
from render.render import RenderHelper

cfg = DashboardConfig.get_config()

app = FastAPI(title="Family E-Ink Dashboard Server", version="0.9.1")

logger = structlog.get_logger()

owmModule = OWMModule()
calModule = IcsModule()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get(
    "/test",
    summary="Background image for testing",
)
def get_background() -> FileResponse:
    return FileResponse("src/render/background.png", media_type="image/png")


@app.get("/image", summary="Rendered dashboard image")
def get_image() -> FileResponse:
    start_time = time.time()
    logger.info("Retrieving data...")

    # Retrieve Weather Data
    current_weather, hourly_forecast, daily_forecast = owmModule.get_weather(
        cfg.LAT, cfg.LNG, cfg.OWM_API_KEY, cfg.WEATHER_UNITS
    )

    currTime = dt.datetime.now(pytz.timezone(cfg.DISPLAY_TZ))
    calStartDatetime = currTime.replace(hour=0, minute=0, second=0, microsecond=0)
    calEndDatetime = calStartDatetime + dt.timedelta(days=cfg.NUM_CAL_DAYS_TO_QUERY, seconds=-1)

    events = calModule.get_events(
        cfg.ICS_URL,
        calStartDatetime,
        calEndDatetime,
        cfg.DISPLAY_TZ,
        cfg.NUM_CAL_DAYS_TO_QUERY,
    )

    end_time = time.time()
    logger.info(f"Completed data retrieval in {round(end_time - start_time, 3)} seconds.")

    # TODO: delete=False leads to accumulating temporary files in /tmp but is currently needed because the FileResponse is async.
    with tempfile.NamedTemporaryFile(suffix=".png", delete_on_close=False, delete=False) as tf:
        start_time = time.time()
        logger.info("Generating image...")

        renderService = RenderHelper(cfg)
        renderService.process_inputs(
            currTime,
            current_weather,
            hourly_forecast,
            daily_forecast,
            events[: cfg.NUM_DAYS_IN_TEMPLATE],
            tf.name,
        )

        end_time = time.time()
        logger.info(
            f"Completed image generation in {round(end_time - start_time, 3)} seconds, serving image now."
        )

        return FileResponse(tf.name, media_type="image/png")


if __name__ == "__main__":
    logger.info("Starting web server...")
    config = uvicorn.Config(app, host="127.0.0.1", port=5000, log_level="debug")
    server = uvicorn.Server(config)
    server.run()
