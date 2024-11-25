import datetime
import logging
import os
import time
from ctypes import POINTER, cast
from logging.handlers import RotatingFileHandler
from pathlib import Path

import typer
import wmi
from appdirs import user_data_dir
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# from typing import Optional

# from typing_extensions import Annotated

log_dir = Path(user_data_dir()) / "robolson" / "nightlight" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "nighlight_schedule.log"

logger = logging.getLogger()

logger.setLevel(logging.INFO)

handler = RotatingFileHandler(filename=log_file.absolute(), maxBytes=100_000, backupCount=2)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

handler.setFormatter(formatter)
logger.addHandler(handler)

# logging.basicConfig(filename=log_file, format="%(asctime)s %(levelname)s %(message)s")

main_app = typer.Typer()


logger.addHandler(handler)

if log_file.stat().st_size > 2 * 1024 * 1024:
    with open(log_file, "r") as fp:
        half_log = fp.readlines()
        half_log = half_log[int(len(half_log) / 2) :]
    with open(log_file, "w") as fp:
        fp.writelines(half_log)


def dim_audio_video():
    # <REDUCE SCREEN BRIGHTNESS>
    c = wmi.WMI(namespace="wmi")
    monitor = c.WmiMonitorBrightness()
    brightness = monitor[0].CurrentBrightness
    brightness *= 0.97
    brightness -= 1
    if brightness < 0:
        brightness = 0
    methods = c.WmiMonitorBrightnessMethods()[0]
    methods.WmiSetBrightness(brightness, 0)
    logger.warning(f"Brightness set to {brightness}")
    # </REDUCE SCREEN BRIGHTNESS>

    # <REDUCE SOUND VOLUME>
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    # Get current volume
    currentVolumeDb = volume.GetMasterVolumeLevel()
    if currentVolumeDb < -60:
        currentVolumeDb = -60
    volume.SetMasterVolumeLevel(currentVolumeDb - 0.7, None)
    logger.warning(f"Volume set to {currentVolumeDb - 0.7}")
    # </REDUCE SOUND VOLUME>


def set_loop(start_time: str = "20:00", end_time: str = "08:00"):
    current_time = datetime.datetime.now()
    start_hour = datetime.time.fromisoformat(start_time).hour
    end_hour = datetime.time.fromisoformat(end_time).hour

    while True:
        while current_time.hour >= start_hour or current_time.hour < end_hour:
            # while current_time.hour > 20 or current_time.hour < 8:
            dim_audio_video()
            time.sleep(60 * 5)
            current_time = datetime.datetime.now()
        night_time = datetime.datetime.combine(
            current_time.date(), datetime.time.fromisoformat("20:00:00")
        )
        while True:
            seconds_until_night = (night_time - datetime.datetime.now()).total_seconds()
            logger.info(f"Sleeping for {seconds_until_night / 3600:.3} hours.")
            time.sleep(60 * 60)
            differential = (datetime.datetime.now() - current_time).total_seconds() / 3600
            logger.info(f"Time elapsed is {differential} hours.")
            current_time = datetime.datetime.now()
            if seconds_until_night / 3600 > 16:
                logging.info(f"{seconds_until_night}")
                break


@main_app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if not ctx.invoked_subcommand:
        set_loop()


@main_app.command("log_file")
def logs():
    """Open the log file with your $env.EDITOR."""
    os.startfile(log_file)


if __name__ == "__main__":
    main_app()
