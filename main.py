"""
main.py
Gesture Control — Beta v0.2
Glassmorphism · Fluid animations · Tray · Autostart
"""

import math
import time
import threading
import platform
import os
import sys
import tkinter as tk
from tkinter import font as tkfont
import cv2
import mediapipe as mp
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import pystray
from pystray import MenuItem as item

import system_control as sysctl

SYSTEM = platform.system()

# ── Autostart ────────────────────────────────────────────────────────────────

def _exe_path():
    if getattr(sys, 'frozen', False):
        return sys.executable
    return os.path.abspath(sys.argv[0])

def is_autostart_enabled():
    if SYSTEM == "Darwin":
        plist = os.path.expanduser("~/Library/LaunchAgents/com.gesturecontrol.app.plist")
        return os.path.exists(plist)
    elif SYSTEM == "Windows":
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "GestureControl")
            winreg.CloseKey(key)
            return True
        except Exception:
            return False
    else:
        desktop = os.path.expanduser("~/.config/autostart/gesturecontrol.desktop")
        return os.path.exists(desktop)

def enable_autostart():
    exe = _exe_path()
    if SYSTEM == "Darwin":
        plist = os.path.expanduser("~/Library/LaunchAgents/com.gesturecontrol.app.plist")
        os.makedirs(os.path.dirname(plist), exist_ok=True)
        with open(plist, "w") as f:
            f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.gesturecontrol.app</string>
    <key>ProgramArguments</key>
    <array><string>{exe}</string></array>
    <key>RunAtLoad</key><true/>
</dict>
</plist>""")
    elif SYSTEM == "Windows":
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "GestureControl", 0, winreg.REG_SZ, exe)
        winreg.CloseKey(key)
    else:
        desktop = os.path.expanduser("~/.config/autostart/gesturecontrol.desktop")
        os.makedirs(os.path.dirname(desktop), exist_ok=True)
        with open(desktop, "w") as f:
            f.write(f"[Desktop Entry]\nType=Application\nName=Gesture Control\nExec={exe}\nHidden=false\nX-GNOME-Autostart-enabled=true\n")

def disable_autostart():
    if SYSTEM == "Darwin":
        plist = os.path.expanduser("~/Library/LaunchAgents/com.gesturecontrol.app.plist")
        if os.path.exists(plist): os.remove(plist)
    elif SYSTEM == "Windows":
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "GestureControl")
            winreg.CloseKey(key)
        except Exception:
            pass
    else:
        desktop = os.path.expanduser("~/.config/autostart/gesturecontrol.desktop")
        if os.path.exists(desktop): os.remove(desktop)

# ── Easing ───────────────────────────────────────────────────────────────────

def ease_out_cubic(t):
    return 1 - (1 - t) ** 3

def ease_in_out_cubic(t):
    if t < 0.5:
        return 4 * t * t * t
    return 1 - (-2 * t + 2) ** 3 / 2

def lerp(a, b, t):
    return a + (b - a) * t

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

def lerp_color(c1, c2, t):
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex(lerp(r1, r2, t), lerp(g1, g2, t), lerp(b1, b2, t))

# ── Config ───────────────────────────────────────────────────────────────────

MIN_DIST        = 20
MAX_DIST        = 200
SMOOTHING       = 5
UPDATE_INTERVAL = 0.15

mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils

BG            = "#0a0a14"
GLASS         = "#13131f"
GLASS2        = "#1a1a2e"
BORDER        = "#ffffff14"
ACCENT_V      = "#7c6fff"
ACCENT_B      = "#ff6fb0"
TEXT          = "#f0f0f0"
TEXT2         = "#6666aa"
TRACK         = "#1e1e30"
BTN_IDLE      = "#1e1e30"
BTN_HOVER     = "#2a2a42"
BTN_ACTIVE    = ACCENT_V

TITLE_FONT = ("SF Pro Display", 13, "bold") if SYSTEM == "Darwin" else ("Segoe UI", 13, "bold")
BODY_FONT  = ("SF Pro Display", 10)         if SYSTEM == "Darwin" else ("Segoe UI", 10)
SMALL_FONT = ("SF Pro Display", 8)          if SYSTEM == "Darwin" else ("Segoe UI", 8)
MONO_FONT  = ("SF Mono", 9)                 if SYSTEM == "Darwin" else ("Consolas", 9)

# ── Animated Arc Slider ───────────────────────────────────────────────────────

class AnimatedSlider(tk.Canvas):
    ANIM_MS = 16
    ANIM_DURATION = 0.35

    def __init__(self, parent, color, label, **kw):
        super().__init__(parent, width=70, height=180,
                         bg=GLASS, highlightthickness=0, **kw)
        self.color  = color
        self.label  = label
        self._display = 50.0
        self._target  = 50.0
        self._anim_start = None
        self._anim_from  = 50.0
        self._animating  = False
        self._draw()

    def set(self, value):
        value = max(0.0, min(100.0, float(value)))
        if abs(value - self._target) < 0.5:
            return
        self._anim_from  = self._display
        self._target     = value
        self._anim_start = time.time()
        if not self._animating:
            self._animating = True
            self._tick()

    def _tick(self):
        now = time.time()
        t   = min(1.0, (now - self._anim_start) / self.ANIM_DURATION)
        et  = ease_out_cubic(t)
        self._display = lerp(self._anim_from, self._target, et)
        self._draw()
        if t < 1.0:
            self.after(self.ANIM_MS, self._tick)
        else:
            self._display   = self._target
            self._animating = False
            self._draw()

    def _draw(self):
        self.delete("all")
        W, H   = 70, 180
        cx     = W // 2
        top    = 12
        bot    = H - 36
        bar_h  = bot - top
        tw     = 6
        pct    = self._display / 100.0
        fill_y = bot - int(bar_h * pct)

        # Glow behind fill (fake blur via layered lines)
        glow_color = self.color + "33"
        for offset in range(6, 0, -2):
            self.create_line(cx, fill_y, cx, bot,
                             fill=self.color + f"{offset * 8:02x}",
                             width=tw + offset * 2, capstyle=tk.ROUND)

        # Track
        self.create_line(cx, top, cx, bot,
                         fill=TRACK, width=tw, capstyle=tk.ROUND)

        # Fill
        if fill_y < bot:
            self.create_line(cx, fill_y, cx, bot,
                             fill=self.color, width=tw, capstyle=tk.ROUND)

        # Knob glow
        for r in range(12, 5, -2):
            alpha = max(0, 60 - (12 - r) * 15)
            self.create_oval(cx - r, fill_y - r, cx + r, fill_y + r,
                             fill=self.color + f"{alpha:02x}", outline="")

        # Knob
        self.create_oval(cx - 6, fill_y - 6, cx + 6, fill_y + 6,
                         fill=self.color, outline="#ffffff44", width=1)

        # Value text
        self.create_text(cx, H - 18, text=f"{int(self._display)}%",
                         fill=TEXT, font=MONO_FONT)

        # Label
        self.create_text(cx, H - 6, text=self.label,
                         fill=TEXT2, font=SMALL_FONT)


# ── Animated Toggle ───────────────────────────────────────────────────────────

class AnimatedToggle(tk.Canvas):
    ANIM_MS = 16
    DURATION = 0.2

    def __init__(self, parent, command=None, initial=False, **kw):
        super().__init__(parent, width=44, height=24,
                         bg=GLASS, highlightthickness=0, **kw)
        self.on       = initial
        self.command  = command
        self._pos     = 1.0 if initial else 0.0
        self._target  = 1.0 if initial else 0.0
        self._from    = self._pos
        self._start   = None
        self._animating = False
        self.bind("<Button-1>", self._toggle)
        self._draw()

    def _toggle(self, _=None):
        self.on     = not self.on
        self._from  = self._pos
        self._target = 1.0 if self.on else 0.0
        self._start  = time.time()
        if not self._animating:
            self._animating = True
            self._tick()
        if self.command:
            self.command(self.on)

    def _tick(self):
        t  = min(1.0, (time.time() - self._start) / self.DURATION)
        et = ease_in_out_cubic(t)
        self._pos = lerp(self._from, self._target, et)
        self._draw()
        if t < 1.0:
            self.after(self.ANIM_MS, self._tick)
        else:
            self._pos = self._target
            self._animating = False
            self._draw()

    def _draw(self):
        self.delete("all")
        t      = self._pos
        track  = lerp_color(TRACK, ACCENT_V, t)
        knob_x = lerp(14, 30, t)
        # track
        self._rrect(2, 2, 42, 22, 11, fill=track, outline="")
        # knob shadow
        self.create_oval(knob_x - 10, 2, knob_x + 10, 22,
                         fill="#00000033", outline="")
        # knob
        self.create_oval(knob_x - 9, 3, knob_x + 9, 21,
                         fill="#ffffff", outline="")

    def _rrect(self, x1, y1, x2, y2, r, **kw):
        self.create_polygon(
            x1+r, y1, x2-r, y1, x2, y1+r, x2, y2-r,
            x2-r, y2, x1+r, y2, x1, y2-r, x1, y1+r,
            smooth=True, **kw)

    def set(self, value):
        if bool(value) != self.on:
            self._toggle()


# ── Animated Button ───────────────────────────────────────────────────────────

class AnimatedButton(tk.Canvas):
    DURATION = 0.15

    def __init__(self, parent, text, command=None, active_color=ACCENT_V, **kw):
        super().__init__(parent, width=220, height=36,
                         bg=BG, highlightthickness=0, cursor="hand2", **kw)
        self.text         = text
        self.command      = command
        self.active_color = active_color
        self._active      = False
        self._hover_t     = 0.0
        self._hover_tgt   = 0.0
        self._hover_from  = 0.0
        self._hover_start = None
        self._animating   = False

        self.bind("<Enter>",    self._on_enter)
        self.bind("<Leave>",    self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self._draw()

    def set_active(self, val):
        self._active = val
        self._draw()

    def _on_enter(self, _=None):
        self._hover_from  = self._hover_t
        self._hover_tgt   = 1.0
        self._hover_start = time.time()
        if not self._animating:
            self._animating = True
            self._tick()

    def _on_leave(self, _=None):
        self._hover_from  = self._hover_t
        self._hover_tgt   = 0.0
        self._hover_start = time.time()
        if not self._animating:
            self._animating = True
            self._tick()

    def _tick(self):
        t  = min(1.0, (time.time() - self._hover_start) / self.DURATION)
        et = ease_out_cubic(t)
        self._hover_t = lerp(self._hover_from, self._hover_tgt, et)
        self._draw()
        if t < 1.0:
            self.after(16, self._tick)
        else:
            self._hover_t   = self._hover_tgt
            self._animating = False
            self._draw()

    def _on_click(self, _=None):
        if self.command:
            self.command()

    def _draw(self):
        self.delete("all")
        W, H, r = 220, 36, 10
        if self._active:
            bg = self.active_color
            fg = "#ffffff"
        else:
            bg = lerp_color(BTN_IDLE, BTN_HOVER, self._hover_t)
            fg = TEXT
        self._rrect(0, 0, W, H, r, fill=bg, outline=BORDER, width=1)
        self.create_text(W // 2, H // 2, text=self.text,
                         fill=fg, font=BODY_FONT)

    def _rrect(self, x1, y1, x2, y2, r, **kw):
        self.create_polygon(
            x1+r, y1, x2-r, y1, x2, y1+r, x2, y2-r,
            x2-r, y2, x1+r, y2, x1, y2-r, x1, y1+r,
            smooth=True, **kw)


# ── Pulsing dot ───────────────────────────────────────────────────────────────

class PulsingDot(tk.Canvas):
    def __init__(self, parent, color, **kw):
        super().__init__(parent, width=16, height=16,
                         bg=BG, highlightthickness=0, **kw)
        self.color = color
        self._t    = 0.0
        self._tick()

    def _tick(self):
        self._t = (self._t + 0.04) % (2 * math.pi)
        scale   = 0.7 + 0.3 * (math.sin(self._t) * 0.5 + 0.5)
        self.delete("all")
        cx, cy = 8, 8
        r      = int(5 * scale)
        alpha  = int(180 + 75 * (math.sin(self._t) * 0.5 + 0.5))
        # outer glow
        self.create_oval(cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2,
                         fill=self.color + f"{alpha // 3:02x}", outline="")
        # dot
        self.create_oval(cx - r, cy - r, cx + r, cy + r,
                         fill=self.color, outline="")
        self.after(30, self._tick)


# ── Main App ──────────────────────────────────────────────────────────────────

class GestureControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gesture Control")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._hide_window)

        self.camera_visible = False
        self.running        = True
        self.cap            = None
        self.hands          = mp_hands.Hands(
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
        )
        self.brightness_history = []
        self.volume_history     = []
        self.last_update        = 0.0
        self.brightness         = sysctl.get_brightness() or 50
        self.volume             = sysctl.get_volume() or 50

        self._build_ui()
        self._start_camera()
        self._update_frame()
        self._start_tray()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        PAD = 20

        # Header
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=PAD, pady=(20, 0))

        tk.Label(header, text="Gesture Control",
                 fg=TEXT, bg=BG, font=TITLE_FONT).pack(side="left")
        tk.Label(header, text="v0.2",
                 fg=TEXT2, bg=BG, font=SMALL_FONT).pack(side="left", padx=(6, 0), pady=(4, 0))

        PulsingDot(header, ACCENT_V).pack(side="right", pady=(2, 0))

        # Divider
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", padx=PAD, pady=(12, 0))

        # Sliders
        sliders_outer = tk.Frame(self.root, bg=GLASS,
                                 highlightbackground=BORDER, highlightthickness=1)
        sliders_outer.pack(padx=PAD, pady=(14, 0))

        sliders_inner = tk.Frame(sliders_outer, bg=GLASS)
        sliders_inner.pack(padx=24, pady=20)

        # Volume column
        vol_col = tk.Frame(sliders_inner, bg=GLASS)
        vol_col.pack(side="left", padx=(0, 8))
        tk.Label(vol_col, text="VOLUMEN",
                 fg=TEXT2, bg=GLASS, font=SMALL_FONT).pack(pady=(0, 6))
        self.vol_slider = AnimatedSlider(vol_col, ACCENT_V, "vol")
        self.vol_slider.pack()
        self.vol_slider.set(self.volume)

        # Divider
        tk.Frame(sliders_inner, bg=BORDER, width=1).pack(side="left", fill="y", padx=8)

        # Brightness column
        bri_col = tk.Frame(sliders_inner, bg=GLASS)
        bri_col.pack(side="left", padx=(8, 0))
        tk.Label(bri_col, text="BRILLO",
                 fg=TEXT2, bg=GLASS, font=SMALL_FONT).pack(pady=(0, 6))
        self.bri_slider = AnimatedSlider(bri_col, ACCENT_B, "bri")
        self.bri_slider.pack()
        self.bri_slider.set(self.brightness)

        # Camera button
        cam_frame = tk.Frame(self.root, bg=BG)
        cam_frame.pack(pady=(14, 0))
        self.cam_btn = AnimatedButton(
            cam_frame, "▶   Mostrar cámara",
            command=self._toggle_camera
        )
        self.cam_btn.pack()

        # Camera feed (hidden)
        self.cam_label = tk.Label(self.root, bg=BG)

        # Divider
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", padx=PAD, pady=(14, 0))

        # Settings row
        settings = tk.Frame(self.root, bg=BG)
        settings.pack(fill="x", padx=PAD, pady=(10, 20))

        tk.Label(settings, text="Abrir al iniciar el dispositivo",
                 fg=TEXT, bg=BG, font=BODY_FONT).pack(side="left")

        self.autostart_toggle = AnimatedToggle(
            settings,
            command=self._on_autostart_toggle,
            initial=is_autostart_enabled()
        )
        self.autostart_toggle.pack(side="right")

    # ── Camera ───────────────────────────────────────────────────────────────

    def _start_camera(self):
        self.cap = cv2.VideoCapture(0)

    def _toggle_camera(self):
        self.camera_visible = not self.camera_visible
        if self.camera_visible:
            self.cam_btn.text = "■   Ocultar cámara"
            self.cam_btn.set_active(True)
            self.cam_label.pack(padx=20, pady=(10, 0))
        else:
            self.cam_btn.text = "▶   Mostrar cámara"
            self.cam_btn.set_active(False)
            self.cam_label.pack_forget()
        self.cam_btn._draw()

    def _update_frame(self):
        if not self.running:
            return
        if self.cap and self.cap.isOpened():
            ok, frame = self.cap.read()
            if ok:
                frame  = cv2.flip(frame, 1)
                h, w, _ = frame.shape
                rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = self.hands.process(rgb)

                hands_data = []
                if result.multi_hand_landmarks:
                    for hl in result.multi_hand_landmarks:
                        mp_draw.draw_landmarks(frame, hl, mp_hands.HAND_CONNECTIONS)
                        thumb = hl.landmark[4]
                        index = hl.landmark[8]
                        wrist = hl.landmark[0]
                        x1, y1 = int(thumb.x * w), int(thumb.y * h)
                        x2, y2 = int(index.x * w), int(index.y * h)
                        dist   = math.hypot(x2 - x1, y2 - y1)
                        pct    = float(np.clip(np.interp(dist, [MIN_DIST, MAX_DIST], [0, 100]), 0, 100))
                        cv2.line(frame, (x1, y1), (x2, y2), (124, 111, 255), 2)
                        cv2.circle(frame, (x1, y1), 6, (255, 111, 176), -1)
                        cv2.circle(frame, (x2, y2), 6, (255, 111, 176), -1)
                        hands_data.append((wrist.x * w, pct))

                vol_target = None
                bri_target = None
                cx = w / 2

                if len(hands_data) == 1:
                    x, pct = hands_data[0]
                    if x < cx: vol_target = pct
                    else:       bri_target = pct
                elif len(hands_data) >= 2:
                    hands_data.sort(key=lambda d: d[0])
                    vol_target = hands_data[0][1]
                    bri_target = hands_data[-1][1]

                now = time.time()
                if now - self.last_update > UPDATE_INTERVAL:
                    if vol_target is not None:
                        self.volume_history.append(vol_target)
                        if len(self.volume_history) > SMOOTHING:
                            self.volume_history.pop(0)
                        sv = int(round(sum(self.volume_history) / len(self.volume_history)))
                        if abs(sv - self.volume) >= 1:
                            if sysctl.set_volume(sv):
                                self.volume = sv
                    if bri_target is not None:
                        self.brightness_history.append(bri_target)
                        if len(self.brightness_history) > SMOOTHING:
                            self.brightness_history.pop(0)
                        sb = int(round(sum(self.brightness_history) / len(self.brightness_history)))
                        if abs(sb - self.brightness) >= 1:
                            if sysctl.set_brightness(sb):
                                self.brightness = sb
                    self.last_update = now

                self.vol_slider.set(self.volume)
                self.bri_slider.set(self.brightness)

                if self.camera_visible:
                    small = cv2.resize(frame, (280, 210))
                    img   = Image.fromarray(cv2.cvtColor(small, cv2.COLOR_BGR2RGB))
                    imgtk = ImageTk.PhotoImage(image=img)
                    self.cam_label.imgtk = imgtk
                    self.cam_label.configure(image=imgtk)

        self.root.after(30, self._update_frame)

    # ── Tray ─────────────────────────────────────────────────────────────────

    def _make_tray_icon(self):
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d   = ImageDraw.Draw(img)
        d.ellipse([4, 4, 60, 60], fill=(124, 111, 255, 230))
        d.text((16, 18), "GC", fill=(255, 255, 255, 255))
        return img

    def _start_tray(self):
        def show(_=None): self.root.after(0, self._show_window)
        def quit_app(_=None): self.root.after(0, self._quit)
        menu = pystray.Menu(
            item("Abrir", show, default=True),
            item("Salir", quit_app),
        )
        self.tray = pystray.Icon("GestureControl", self._make_tray_icon(),
                                 "Gesture Control", menu)
        threading.Thread(target=self.tray.run, daemon=True).start()

    # ── Window ───────────────────────────────────────────────────────────────

    def _hide_window(self):
        self.root.withdraw()

    def _show_window(self):
        self.root.deiconify()
        self.root.lift()

    def _on_autostart_toggle(self, value):
        if value: enable_autostart()
        else:     disable_autostart()

    def _quit(self):
        self.running = False
        if self.cap: self.cap.release()
        self.hands.close()
        try: self.tray.stop()
        except Exception: pass
        self.root.destroy()


# ── Entry ─────────────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    root.configure(bg=BG)
    app = GestureControlApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
