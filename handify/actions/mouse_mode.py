"""
Mouse por gestos.

O modo mouse só fica ligado depois do gesto de ativação (ver
actions/activation.py); enquanto desligado, nada aqui mexe no cursor.

Cada "botão" do mouse (clique esquerdo, do meio, direito e rolagem) tem o
seu próprio gesto, gravado na aba Mouse (mouse.json), independente dos
gestos do teclado.

Dois jeitos de mover o cursor (ajuste "move_mode"):
  absolute  a posição da mão na câmera é a posição na tela;
  relative  o cursor só anda enquanto o gesto de EMBREAGEM ("clutch") é
            mantido, pelo deslocamento da mão. Soltar a embreagem permite
            reposicionar a mão sem mexer o cursor, como levantar o mouse.

Uso (a cada frame):
    role = mouse_mode.process(role_reconhecido, recognizer.last_points)
"""
import time
from collections import deque

import pyautogui

from handify.config.manager import MOUSE_ROLES as ROLES

FROZEN_ROLES = ("left_click", "middle_click", "right_click", "scroll")


class MouseMode:

    def __init__(self, config):
        self.config = config
        self.cfg = config.settings()

        self.active = False       # modo mouse ligado (por gesto de ativação)

        self.role = None          # papel estável atual
        self.candidate = None     # papel visto neste frame (antes do debounce)
        self.count = 0

        self.sx = None            # posição suavizada do cursor
        self.sy = None

        self.rel_s = None         # relativo: posição suavizada da mão
        self.rel_acc = [0.0, 0.0] # relativo: movimento acumulado (zona morta)
        self.history = deque(maxlen=12)

        self.press_time = 0.0
        self.dragging = False

        self.scroll_y = None
        self.scroll_acc = 0.0

        self.screen_w, self.screen_h = pyautogui.size()

    # -----------------------------------------------------
    # Configuração
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Posição do cursor
    # -----------------------------------------------------

    def _to_screen(self, x, y):
        margin = self.cfg["margin"]

        if self.cfg["mirror"]:
            x = 1.0 - x

        nx = min(max((x - margin) / (1.0 - 2 * margin), 0.0), 1.0)
        ny = min(max((y - margin) / (1.0 - 2 * margin), 0.0), 1.0)

        # 2 px de folga: não aciona o FAILSAFE do pyautogui nos cantos.
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
        """
        Move o cursor pelo DESLOCAMENTO da mão, não pela posição dela.

        - A posição da mão é suavizada (média móvel) para tirar tremor.
        - Zona morta por acúmulo: movimentos minúsculos somam até passar
          de `deadzone` px e só então saem. Tremor (vai e volta) se anula,
          mas movimento lento e real NÃO é descartado.
        - O cursor parte de onde ele já está (o mouse físico pode ter
          sido usado) e nunca dá salto ao reengatar a embreagem.
        """
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
        """
        Posição de onde o gesto COMEÇOU. Enquanto o gesto é confirmado
        (hold_frames) a mão já se mexeu um pouco; voltamos alguns frames
        para o clique cair onde o usuário estava apontando.
        """
        if not self.history:
            return self.sx, self.sy

        back = self.cfg["hold_frames"] + 1
        index = max(0, len(self.history) - 1 - back)
        return self.history[index]

    # -----------------------------------------------------
    # Loop principal
    # -----------------------------------------------------

    def process(self, role, points, now=None):
        """
        role:   botão do mouse cujo gesto foi reconhecido neste frame
                ("left_click", "middle_click", "right_click", "scroll")
                ou None
        points: lista de 21 (x, y) em coordenadas da imagem (ou None)
        Retorna o papel estável atual (ou None).
        """
        if not self.active:
            return None

        now = time.monotonic() if now is None else now

        # Mão saiu da câmera: solta tudo, sem clicar.
        if points is None:
            self.rel_s = None
            self.candidate, self.count = None, 0
            if self.role is not None:
                self._transition(None, now, cancel=True)
            self.history.clear()
            return None

        # Cursor só anda quando não está "travado" por um gesto de botão.
        dragging = self.role == "left_click" and self.dragging

        if self.cfg["move_mode"] == "relative":
            # Só com a embreagem (ou arrastando) a mão move o cursor.
            tracking = self.role == "clutch" or dragging
        else:
            tracking = self.role in (None, "clutch") or dragging

        if tracking:
            self._track(points)
        else:
            self.rel_s = None     # a próxima embreagem recomeça do zero

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

    # -----------------------------------------------------
    # Transições entre papéis
    # -----------------------------------------------------

    def _transition(self, new, now, cancel=False):
        old = self.role

        # --- saindo do papel anterior ---
        if old == "left_click":
            if self.dragging:
                pyautogui.mouseUp()
                self.dragging = False
            elif new is None and not cancel:
                pyautogui.click()          # toque rápido = clique

        if old == "scroll":
            self.scroll_y = None
            self.scroll_acc = 0.0

        self.role = new

        # --- entrando no novo papel ---
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
        # Segurou o pinch esquerdo tempo suficiente: começa a arrastar.
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

            dy = self.scroll_y - y        # mão sobe -> rola para cima

            if abs(dy) < 0.004:           # zona morta
                return

            self.scroll_acc += dy * self.cfg["scroll_sensitivity"]
            steps = int(self.scroll_acc)

            if steps:
                pyautogui.scroll(steps)
                self.scroll_acc -= steps

            self.scroll_y = y

    # -----------------------------------------------------
    # Limpeza
    # -----------------------------------------------------

    def emergency_stop(self):
        """
        Parada de emergência: solta QUALQUER botão preso e desliga o modo
        mouse. Não faz clique nenhum.
        """
        for button in ("left", "middle", "right"):
            try:
                pyautogui.mouseUp(button=button)
            except Exception:
                pass

        self.dragging = False
        self.set_active(False)
        self.release()

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
