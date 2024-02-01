import logging
from ctypes import POINTER, cast
from pathlib import Path

import wmi
from appdirs import user_data_dir
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from rocketry import Rocketry
from rocketry.conds import cron, daily, every, hourly, retry, time_of_day, weekly

log_dir = Path(user_data_dir()) / "robolson" / "nightlight" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "myapp.log"

logging.basicConfig(filename=log_file, format="%(asctime)s %(levelname)s %(message)s")

app = Rocketry()

logger = logging.getLogger()

if log_file.stat().st_size > 5 * 1024 * 1024:
    with open(log_file, "r") as fp:
        half_log = fp.readlines()
        half_log = half_log[int(len(half_log) / 2) :]
    with open(log_file, "w") as fp:
        fp.writelines(half_log)


@app.task(every("5 minutes") & time_of_day.between("20:00", "08:00") | retry(3))
def do_hourly_at_night():
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


if __name__ == "__main__":
    app.run()
