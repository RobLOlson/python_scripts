import logging
from ctypes import POINTER, cast
from pathlib import Path

import wmi
from appdirs import user_log_dir
from comtypes import CLSCTX_ALL, logging
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from rocketry import Rocketry
from rocketry.conds import cron, daily, every, hourly, retry, time_of_day, weekly

log_dir = Path(user_log_dir(appname="nightlight"))
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "myapp.log"

logging.basicConfig(filename=log_file, format="%(asctime)s %(levelname)s %(message)s")

app = Rocketry()


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
    # </REDUCE SCREEN BRIGHTNESS>

    # <REDUCE SOUND VOLUME>
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    # Get current volume
    currentVolumeDb = volume.GetMasterVolumeLevel()
    volume.SetMasterVolumeLevel(currentVolumeDb - 0.7, None)
    # </REDUCE SOUND VOLUME>


if __name__ == "__main__":
    app.run()
