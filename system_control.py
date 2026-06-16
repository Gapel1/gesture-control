"""
system_control.py
Funciones multiplataforma para leer y ajustar brillo y volumen del sistema.

Brillo  -> usa la librería screen_brightness_control (Windows/macOS/Linux)
Volumen -> implementación específica por sistema operativo:
    - Windows: pycaw
    - macOS:   osascript (built-in, no requiere instalación extra)
    - Linux:   pactl (pulseaudio-utils)
"""

import platform
import subprocess

import screen_brightness_control as sbc

SYSTEM = platform.system()  # 'Windows', 'Darwin' (macOS) o 'Linux'


# ---------------------------------------------------------------------------
# BRILLO
# ---------------------------------------------------------------------------
def get_brightness():
    """Devuelve el brillo actual (0-100) o None si no se puede leer."""
    try:
        return sbc.get_brightness()[0]
    except Exception:
        return None


def set_brightness(pct):
    """Intenta fijar el brillo. Devuelve True si tuvo éxito."""
    pct = max(0, min(100, int(round(pct))))
    try:
        sbc.set_brightness(pct)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# VOLUMEN (implementación según sistema operativo)
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

elif SYSTEM == "Darwin":  # macOS

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
