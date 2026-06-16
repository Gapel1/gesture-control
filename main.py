"""
main.py
Gesture Control - Beta v0.1
App de escritorio para controlar brillo y volumen del sistema con gestos
de mano, usando MediaPipe + OpenCV + Tkinter.

CÓMO USARLA
    - Pellizca (junta pulgar e índice) con la mano en el lado IZQUIERDO
      de la imagen de la cámara -> controla el VOLUMEN.
    - Pellizca con la mano en el lado DERECHO -> controla el BRILLO.
    - Puedes usar una sola mano (controla lo que corresponda según el lado
      en que la pongas) o las dos al mismo tiempo.

INSTALACIÓN
    pip install -r requirements.txt

    macOS:   brew install brightness   (necesario para que el brillo de la
             pantalla integrada funcione; el volumen no necesita nada extra)
    Linux:   necesitas "pactl" instalado (pulseaudio-utils, viene por
             defecto en la mayoría de distros)
"""

import math
import time
import tkinter as tk
from tkinter import ttk

import cv2
import mediapipe as mp
import numpy as np
from PIL import Image, ImageTk

import system_control as sysctl

# ---------------------- Configuración ajustable ----------------------
MIN_DIST = 20
MAX_DIST = 200
SMOOTHING = 5
UPDATE_INTERVAL = 0.15
# -----------------------------------------------------------------------

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


class GestureControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gesture Control — Beta v0.1")
        self.root.resizable(False, False)

        self.cap = cv2.VideoCapture(0)
        self.hands = mp_hands.Hands(
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
        )

        self.brightness_history = []
        self.volume_history = []
        self.last_update = 0.0

        self.brightness = sysctl.get_brightness() or 50
        self.volume = sysctl.get_volume() or 50

        self._build_ui()
        self._update_frame()

    # ------------------------------------------------------------------
    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.grid(row=0, column=0)

        self.video_label = ttk.Label(main_frame)
        self.video_label.grid(row=0, column=0, rowspan=3, padx=(0, 15))

        ttk.Label(main_frame, text="Volumen", font=("Helvetica", 12, "bold")).grid(
            row=0, column=1
        )
        self.volume_bar = ttk.Progressbar(
            main_frame, orient="vertical", length=200, maximum=100
        )
        self.volume_bar.grid(row=1, column=1, padx=10)
        self.volume_value_label = ttk.Label(main_frame, text="50%")
        self.volume_value_label.grid(row=2, column=1)

        ttk.Label(main_frame, text="Brillo", font=("Helvetica", 12, "bold")).grid(
            row=0, column=2
        )
        self.brightness_bar = ttk.Progressbar(
            main_frame, orient="vertical", length=200, maximum=100
        )
        self.brightness_bar.grid(row=1, column=2, padx=10)
        self.brightness_value_label = ttk.Label(main_frame, text="50%")
        self.brightness_value_label.grid(row=2, column=2)

        self.status_label = ttk.Label(
            self.root,
            text="Beta v0.1 — más funciones próximamente",
            foreground="gray",
        )
        self.status_label.grid(row=1, column=0, pady=(0, 10))

    # ------------------------------------------------------------------
    def _update_frame(self):
        ok, frame = self.cap.read()
        if ok:
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.hands.process(rgb)

            hands_data = []  # lista de (x_muñeca, porcentaje_pellizco)

            if result.multi_hand_landmarks:
                for hand_landmarks in result.multi_hand_landmarks:
                    mp_draw.draw_landmarks(
                        frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                    )

                    thumb_tip = hand_landmarks.landmark[4]
                    index_tip = hand_landmarks.landmark[8]
                    wrist = hand_landmarks.landmark[0]

                    x1, y1 = int(thumb_tip.x * w), int(thumb_tip.y * h)
                    x2, y2 = int(index_tip.x * w), int(index_tip.y * h)

                    dist = math.hypot(x2 - x1, y2 - y1)
                    pct = float(
                        np.clip(np.interp(dist, [MIN_DIST, MAX_DIST], [0, 100]), 0, 100)
                    )

                    cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                    cv2.circle(frame, (x1, y1), 8, (255, 0, 255), -1)
                    cv2.circle(frame, (x2, y2), 8, (255, 0, 255), -1)

                    hands_data.append((wrist.x * w, pct))

            # Asignar mano izquierda -> volumen, mano derecha -> brillo
            vol_target = None
            bright_target = None
            center_x = w / 2

            if len(hands_data) == 1:
                x, pct = hands_data[0]
                if x < center_x:
                    vol_target = pct
                else:
                    bright_target = pct
            elif len(hands_data) >= 2:
                hands_data.sort(key=lambda hd: hd[0])
                vol_target = hands_data[0][1]
                bright_target = hands_data[-1][1]

            now = time.time()
            if now - self.last_update > UPDATE_INTERVAL:
                if vol_target is not None:
                    self.volume_history.append(vol_target)
                    if len(self.volume_history) > SMOOTHING:
                        self.volume_history.pop(0)
                    smoothed = sum(self.volume_history) / len(self.volume_history)
                    target_int = int(round(smoothed))
                    if abs(target_int - self.volume) >= 1:
                        if sysctl.set_volume(target_int):
                            self.volume = target_int

                if bright_target is not None:
                    self.brightness_history.append(bright_target)
                    if len(self.brightness_history) > SMOOTHING:
                        self.brightness_history.pop(0)
                    smoothed = sum(self.brightness_history) / len(self.brightness_history)
                    target_int = int(round(smoothed))
                    if abs(target_int - self.brightness) >= 1:
                        if sysctl.set_brightness(target_int):
                            self.brightness = target_int

                self.last_update = now

            self.volume_bar["value"] = self.volume
            self.volume_value_label.config(text=f"{self.volume}%")
            self.brightness_bar["value"] = self.brightness
            self.brightness_value_label.config(text=f"{self.brightness}%")

            cv2.putText(
                frame,
                "Izquierda = Volumen | Derecha = Brillo",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
            )

            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        self.root.after(15, self._update_frame)

    # ------------------------------------------------------------------
    def on_close(self):
        self.cap.release()
        self.hands.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = GestureControlApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
