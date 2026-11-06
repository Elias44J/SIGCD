import time

import pyautogui


class ActionExecutor:

    def __init__(self):

        pyautogui.PAUSE = 0.03

    def execute(self, action):

        if not action:
            return

        action_type = action.get("type")

        # Ações de mouse podem apontar para uma posição fixa ou predefinida.
        position = action.get("position")
        if position and action_type in ("click", "double_click", "scroll", "hscroll"):
            x, y = self.resolve_position(position)
            pyautogui.moveTo(x, y)

        if action_type == "key":

            key = action["key"]

            if len(key) > 1 and key not in pyautogui.KEYBOARD_KEYS:
                for char in key:
                    if char == " ":
                        pyautogui.press("space")
                    else:
                        pyautogui.press(char)
            else:
                pyautogui.press(key)

        elif action_type in "hotkey":

            keys = action.get("keys", [])

            if keys:
                pyautogui.hotkey(
                    *keys
                )

        elif action_type == "delay":

            time.sleep(
                max(
                    0.0,
                    float(
                        action.get(
                            "seconds",
                            0
                        )
                    )
                )
            )

        elif action_type == "click":

            pyautogui.click(
                button=action.get("button", "left")
            )

        elif action_type == "double_click":

            pyautogui.doubleClick(
                button=action.get(
                    "button",
                    "left"
                )
            )

        elif action_type == "mouse_down":

            pyautogui.mouseDown(
                button=action.get(
                    "button",
                    "left"
                )
            )

        elif action_type == "mouse_up":

            pyautogui.mouseUp(
                button=action.get(
                    "button",
                    "left"
                )
            )

        elif action_type == "hold":

            key = action["key"]

            pyautogui.keyDown(key)

            try:

                time.sleep(
                    max(
                        0.0,
                        float(
                            action.get(
                                "duration",
                                1
                            )
                        )
                    )
                )

            finally:

                pyautogui.keyUp(key)

        elif action_type == "move_relative":

            pyautogui.moveRel(
                int(
                    action.get(
                        "x",
                        0
                    )
                ),

                int(
                    action.get(
                        "y",
                        0
                    )
                ),

                duration=max(
                    0.0,
                    float(
                        action.get(
                            "duration",
                            0
                        )
                    )
                )
            )

        elif action_type == "move_absolute":

            pyautogui.moveTo(
                int(action["x"]),
                int(action["y"]),

                duration=max(
                    0.0,
                    float(
                        action.get(
                            "duration",
                            0
                        )
                    )
                )
            )

        elif action_type == "scroll":

            pyautogui.scroll(
                int(
                    action.get(
                        "amount",
                        1
                    )
                )
            )

        elif action_type == "hscroll":

            pyautogui.hscroll(
                int(
                    action.get(
                        "amount",
                        1
                    )
                )
            )

        elif action_type == "special":

            self.special(
                action.get("command")
            )

        elif action_type == "sequence":

            actions = action.get("actions", [])

            for item in actions:

                self.execute(item)

        else:

            raise ValueError(
                f"Tipo de ação desconhecido: "
                f"{action_type}"
            )

    @staticmethod
    def resolve_position(position):
        mode = position.get("mode", "preset")
        if mode == "custom":
            return int(position["x"]), int(position["y"])

        width, height = pyautogui.size()
        presets = {
            "center": (width // 2, height // 2),
            "top_center": (width // 2, height // 4),
            "bottom_center": (width // 2, (height * 3) // 4),
        }
        return presets.get(position.get("value", "center"), presets["center"])

    def special(self, command):

        if command == "screenshot":

            pyautogui.screenshot()

        else:

            raise ValueError(
                f"Comando especial desconhecido: "
                f"{command}"
            )

    def execute_sequence(self, sequence):
        if not sequence:
            return

        # Cada caractere do texto vira uma tecla.
        for char in sequence:


            if char == " ":
                pyautogui.press("space")

            elif char == "\n":
                pyautogui.press("enter")

            else:
                pyautogui.press(char)

            time.sleep(0.01)