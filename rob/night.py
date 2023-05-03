import math
from ctypes import POINTER, cast

import wmi
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from rocketry import Rocketry
from rocketry.conds import cron, daily, every, hourly, time_of_day, weekly

app = Rocketry()


@app.task(every("5 minutes") & time_of_day.between("20:00", "08:00"))
def do_hourly_at_night():
    # <REDUCE SCREEN BRIGHTNESS>
    c = wmi.WMI(namespace="wmi")
    monitor = c.WmiMonitorBrightness()
    brightness = monitor[0].CurrentBrightness
    brightness *= 0.95
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
    volume.SetMasterVolumeLevel(currentVolumeDb - 1.0, None)
    # </REDUCE SOUND VOLUME>


if __name__ == "__main__":
    app.run()
