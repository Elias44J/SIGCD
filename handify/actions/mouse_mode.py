
import time
from collections import deque

import pyautogui

from handify.config.manager import MOUSE_ROLES as ROLES

FROZEN_ROLES = ("left_click", "middle_click", "right_click", "scroll")


class MouseMode:

    def __init__(self, config):
        self.config = config
        self.cfg = config.settings()

        self.active = False       

        self.role = None          
        self.candidate = None     
        self.count = 0

        self.sx = None            
        self.sy = None

        self.rel_s = None         
        self.rel_acc = [0.0, 0.0] 
        self.history = deque(maxlen=12)

        self.press_time = 0.0
        self.dragging = False

        self.scroll_y = None
        self.scroll_acc = 0.0

        self.screen_w, self.screen_h = pyautogui.size()

    def reload(self):
        """Recarrega as configurações (chamar depois de salvar na UI)."""
        self.cfg = self.config.settings()

    def set_active(self, active):
        """Liga/desliga o modo mouse. Ao desligar, solta tudo."""
        if active == self.active:
            return

        if not active:
            self.release()
            self.sx = self.sy = None

        self.active = active

    def _to_screen(self, x, y):
        margin = self.cfg["margin"]

        if self.cfg["mirror"]:
            x = 1.0 - x

        nx = min(max((x - margin) / (1.0 - 2 * margin), 0.0), 1.0)
        ny = min(max((y - margin) / (1.0 - 2 * margin), 0.0), 1.0)

        px = 2 + nx * (self.screen_w - 5)
        py = 2 + ny * (self.screen_h - 5)
        return px, py

    def _move_to(self, x, y):
        pyautogui.moveTo(x, y, _pause=False)

    def _track(self, points):
        if self.cfg["move_mode"] == "relative":
            self._track_relative(points)
            return

        tx, ty = self._to_screen(*points[self.cfg["track_point"]])

        if self.sx is None:
            self.sx, self.sy = tx, ty
        else:
            a = self.cfg["smoothing"]
            self.sx += a * (tx - self.sx)
            self.sy += a * (ty - self.sy)

        self.history.append((self.sx, self.sy))
        self._move_to(self.sx, self.sy)

    @staticmethod
    def _clamp(value, limit):
        return min(max(value, 2.0), limit - 3.0)

    def _track_relative(self, points):
        x, y = points[self.cfg["track_point"]]

        if self.cfg["mirror"]:
            x = 1.0 - x

        if self.rel_s is None:
            self.rel_s = (x, y)
            self.rel_acc = [0.0, 0.0]
            px, py = pyautogui.position()
            self.sx, self.sy = float(px), float(py)
            return

        a = self.cfg["smoothing"]
        old_x, old_y = self.rel_s
        new_x = old_x + a * (x - old_x)
        new_y = old_y + a * (y - old_y)
        self.rel_s = (new_x, new_y)

        gain = self.cfg["gain"]
        dx = (new_x - old_x) * self.screen_w * gain
        dy = (new_y - old_y) * self.screen_h * gain

        dead = self.cfg["deadzone"]
        out = [0.0, 0.0]

        for i, delta in enumerate((dx, dy)):
            self.rel_acc[i] += delta

            if abs(self.rel_acc[i]) >= dead:
                out[i] = self.rel_acc[i]
                self.rel_acc[i] = 0.0

        if out[0] or out[1]:
            self.sx = self._clamp(self.sx + out[0], self.screen_w)
            self.sy = self._clamp(self.sy + out[1], self.screen_h)

        self.history.append((self.sx, self.sy))
        self._move_to(self.sx, self.sy)

    def _anchor(self):
        if not self.history:
            return self.sx, self.sy

        back = self.cfg["hold_frames"] + 1
        index = max(0, len(self.history) - 1 - back)
        return self.history[index]

    def process(self, role, points, now=None):
        if not self.active:
            return None

        now = time.monotonic() if now is None else now

        if points is None:
            self.rel_s = None
            self.candidate, self.count = None, 0
            if self.role is not None:
                self._transition(None, now, cancel=True)
            self.history.clear()
            return None

        dragging = self.role == "left_click" and self.dragging

        if self.cfg["move_mode"] == "relative":

            tracking = self.role == "clutch" or dragging
        else:
            tracking = self.role in (None, "clutch") or dragging

        if tracking:
            self._track(points)
        else:
            self.rel_s = None     

        # Debounce do papel
        raw = role if role in ROLES else None

        if raw == self.candidate:
            self.count += 1
        else:
            self.candidate, self.count = raw, 1

        need = self.cfg["hold_frames"] if raw else self.cfg["release_frames"]

        if self.count >= need and raw != self.role:
            self._transition(raw, now)

        self._continuous(points, now)

        return self.role

    def _transition(self, new, now, cancel=False):
        old = self.role

        # --- saindo do papel anterior ---
        if old == "left_click":
            if self.dragging:
                pyautogui.mouseUp()
                self.dragging = False
            elif new is None and not cancel:
                pyautogui.click()          

        if old == "scroll":
            self.scroll_y = None
            self.scroll_acc = 0.0

        self.role = new

        if new in FROZEN_ROLES:
            x, y = self._anchor()
            if x is not None:
                self._move_to(x, y)
                self.sx, self.sy = x, y

        if new == "left_click":
            self.press_time = now
        elif new == "right_click":
            pyautogui.click(button="right")
        elif new == "middle_click":
            pyautogui.click(button="middle")
        elif new == "scroll":
            self.scroll_y = None
            self.scroll_acc = 0.0

    def _continuous(self, points, now):
        if (
            self.role == "left_click"
            and not self.dragging
            and now - self.press_time > self.cfg["drag_after"]
        ):
            pyautogui.mouseDown()
            self.dragging = True

        # Rolagem: mover a mão para cima/baixo.
        if self.role == "scroll":
            y = points[self.cfg["track_point"]][1]

            if self.scroll_y is None:
                self.scroll_y = y
                return

            dy = self.scroll_y - y        

            if abs(dy) < 0.004:          
                return

            self.scroll_acc += dy * self.cfg["scroll_sensitivity"]
            steps = int(self.scroll_acc)

            if steps:
                pyautogui.scroll(steps)
                self.scroll_acc -= steps

            self.scroll_y = y

    def release(self):
        self.rel_s = None
        if self.dragging:
            pyautogui.mouseUp()
            self.dragging = False
        self.role = None
        self.candidate, self.count = None, 0
        self.scroll_y = None
        self.scroll_acc = 0.0
        self.history.clear()
