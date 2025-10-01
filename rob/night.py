import datetime
import logging
import os
import time
import winreg
from ctypes import POINTER, cast
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List

import wmi
from appdirs import user_data_dir
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

from .utilities import cli

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


logger.addHandler(handler)

if log_file.stat().st_size > 2 * 1024 * 1024:
    with open(log_file, "r") as fp:
        half_log = fp.readlines()
        half_log = half_log[int(len(half_log) / 2) :]
    with open(log_file, "w") as fp:
        fp.writelines(half_log)


class NightLight:
    def __init__(self):
        self._key_path = r"Software\Microsoft\Windows\CurrentVersion\CloudStore\Store\DefaultAccount\Current\default$windows.data.bluelightreduction.bluelightreductionstate\windows.data.bluelightreduction.bluelightreductionstate"
        self._registry_key = None
        try:
            self._registry_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, self._key_path, 0, winreg.KEY_ALL_ACCESS
            )
        except WindowsError:
            pass

    def supported(self) -> bool:
        return self._registry_key is not None

    def _get_data(self) -> bytes:
        try:
            data, _ = winreg.QueryValueEx(self._registry_key, "Data")
            return data
        except WindowsError as e:
            raise e

    def _hex_to_bytes(self, hex_str: str) -> List[int]:
        return [int(hex_str[i : i + 2], 16) for i in range(0, len(hex_str), 2)]

    def _bytes_to_hex(self, bytes_arr: List[int]) -> str:
        return "".join([f"{b:02x}" for b in bytes_arr])

    def enabled(self) -> bool:
        if not self.supported():
            return False
        try:
            data = self._get_data()
            bytes_arr = list(data)
            return bytes_arr[18] == 0x15  # 21 in decimal
        except:  # noqa: E722
            return False

    def enable(self):
        if self.supported() and not self.enabled():
            self.toggle()

    def disable(self):
        if self.supported() and self.enabled():
            self.toggle()

    def toggle(self):
        if not self.supported():
            return

        data = list(self._get_data())
        enabled = self.enabled()

        if enabled:
            # Disable night light
            new_data = [0] * 41
            new_data[:22] = data[:22]
            new_data[23:] = data[25:43]
            new_data[18] = 0x13
        else:
            # Enable night light
            new_data = [0] * 43
            new_data[:22] = data[:22]
            new_data[25:] = data[23:41]
            new_data[18] = 0x15
            new_data[23] = 0x10
            new_data[24] = 0x00

        # Increment the counter bytes
        for i in range(10, 15):
            if new_data[i] != 0xFF:
                new_data[i] += 1
                break

        try:
            winreg.SetValueEx(self._registry_key, "Data", 0, winreg.REG_BINARY, bytes(new_data))
        except WindowsError as e:
            raise e


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
    NightLight().enable()


def set_loop(start_time: str = "20:00", end_time: str = "08:00", always_on: bool = False):
    current_time = datetime.datetime.now()
    start_hour = datetime.time.fromisoformat(start_time).hour
    end_hour = datetime.time.fromisoformat(end_time).hour

    while True:
        while current_time.hour >= start_hour or current_time.hour < end_hour or always_on:
            # while current_time.hour > 20 or current_time.hour < 8:
            dim_audio_video()
            time.sleep(60 * 5)
            current_time = datetime.datetime.now()
        night_time = datetime.datetime.combine(current_time.date(), datetime.time.fromisoformat("20:00:00"))
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


@cli.cli("")
def main(once: bool = False, always_on: bool = False):
    if once:
        dim_audio_video()
        exit(0)

    # if not ctx.invoked_subcommand:
    else:
        set_loop(always_on=always_on)


@cli.cli("log_file")
def logs():
    """Open the log file with your $env.EDITOR."""
    os.startfile(log_file)


if __name__ == "__main__":
    cli.main(use_configs=True)
