"""
system_control.py
Funciones multiplataforma para leer y ajustar brillo y volumen del sistema.
"""
import platform
import subprocess
import sys
import os

SYSTEM = platform.system()

if SYSTEM not in ("Darwin", "Windows"):
    import screen_brightness_control as sbc

# ---------------------------------------------------------------------------
# BRILLO
# ---------------------------------------------------------------------------
def _brightness_bin():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'brightness_bin')
    return 'brightness'

def get_brightness():
    if SYSTEM == "Darwin":
        try:
            out = subprocess.check_output([_brightness_bin(), "-l"], stderr=subprocess.STDOUT)
            for line in out.decode().split("\n"):
                if "brightness" in line and "display" in line:
                    val = float(line.strip().split()[-1])
                    return round(val * 100)
            return None
        except Exception:
            return None
    try:
        return sbc.get_brightness()[0]
    except Exception:
        return None

def set_brightness(pct):
    pct = max(0, min(100, int(round(pct))))
    if SYSTEM == "Darwin":
        try:
            subprocess.run([_brightness_bin(), str(pct / 100)], check=True)
            return True
        except Exception:
            return False
    try:
        sbc.set_brightness(pct)
        return True
    except Exception:
        return False

# ---------------------------------------------------------------------------
# VOLUMEN
# ---------------------------------------------------------------------------
if SYSTEM == "Windows":
    from ctypes import POINTER, cast
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    def _windows_volume_interface():
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))

    def get_volume():
        try:
            vol = _windows_volume_interface()
            return round(vol.GetMasterVolumeLevelScalar() * 100)
        except Exception:
            return None

    def set_volume(pct):
        pct = max(0, min(100, int(round(pct))))
        try:
            vol = _windows_volume_interface()
            vol.SetMasterVolumeLevelScalar(pct / 100, None)
            return True
        except Exception:
            return False

elif SYSTEM == "Darwin":
    def get_volume():
        try:
            out = subprocess.check_output(
                ["osascript", "-e", "output volume of (get volume settings)"]
            )
            return int(out.decode().strip())
        except Exception:
            return None

    def set_volume(pct):
        pct = max(0, min(100, int(round(pct))))
        try:
            subprocess.run(
                ["osascript", "-e", f"set volume output volume {pct}"], check=True
            )
            return True
        except Exception:
            return False

elif SYSTEM == "Linux":
    def get_volume():
        try:
            out = subprocess.check_output(["pactl", "get-sink-volume", "@DEFAULT_SINK@"])
            for part in out.decode().split():
                if part.endswith("%"):
                    return int(part.replace("%", ""))
            return None
        except Exception:
            return None

    def set_volume(pct):
        pct = max(0, min(100, int(round(pct))))
        try:
            subprocess.run(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{pct}%"], check=True
            )
            return True
        except Exception:
            return False

else:
    def get_volume():
        return None

    def set_volume(pct):
        return False
