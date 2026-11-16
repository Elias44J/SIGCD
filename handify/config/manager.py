import os
import sys
import copy
import json
from pathlib import Path


def _writable(folder):
    """True se der para criar a pasta e gravar nela."""
    try:
        folder.mkdir(parents=True, exist_ok=True)
        probe = folder / ".write_test"
        probe.touch()
        probe.unlink()
        return True
    except OSError:
        return False


def config_dir():
    # 1) Rodando como AppImage: o runtime define APPIMAGE com o caminho
    #    do arquivo .AppImage. Guarda os dados ao lado dele.
    appimage = os.environ.get("APPIMAGE")

    if appimage:
        folder = Path(appimage).resolve().parent / "handify_config"

        if _writable(folder):
            return folder

        # Pasta sem permissão de escrita (ex.: /opt): usa ~/.config
        fallback = Path.home() / ".config" / "handify"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback

    # 2) Executável do PyInstaller fora de AppImage
    if getattr(sys, "frozen", False):
        folder = Path(sys.executable).resolve().parent / "handify_config"

        if _writable(folder):
            return folder

        fallback = Path.home() / ".config" / "handify"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback

    # 3) Rodando pelo código (python main.py): mantém o comportamento atual
    return Path(__file__).resolve().parent


KEYBOARD_FILE = "keyboard.json"
MOUSE_FILE = "mouse.json"
LEGACY_FILE = "gestures.json"      # arquivo único das versões anteriores


# =========================================================
# MOUSE: papéis fixos e ajustes padrão
# =========================================================

MOUSE_ROLES = {
    "clutch": "Mover cursor (embreagem)",
    "left_click": "Clique esquerdo",
    "middle_click": "Clique do meio",
    "right_click": "Clique direito",
    "scroll": "Rolagem",
}

# Gesto que liga/desliga o modo mouse (ex.: o "chifre"). É gravado na aba
# Mouse como qualquer outro gesto.
MOUSE_ACTIVATION = {
    "activation": "Ativação do modo mouse",
}

MOUSE_DEFAULTS = {
    "move_mode": "relative",  # cursor controlado apenas pela embreagem
    "gain": 1.5,               # relativo: quantas telas por "tela de mão"
    "deadzone": 1.0,           # relativo: px acumulados antes de mover
    "track_point": 9,          # 9 = palma, 8 = ponta do indicador
    "mirror": True,
    "smoothing": 0.35,
    "margin": 0.15,
    "scroll_sensitivity": 250,
    "drag_after": 0.45,
    "min_confidence": 0.60,
    "hold_frames": 3,
    "release_frames": 3,
    "activation_hold": 1.0,    # segundos segurando o gesto de ativação
}


# =========================================================
# MIGRAÇÃO gestures.json -> keyboard.json + mouse.json
# =========================================================

def _read_json(path):
    try:
        with Path(path).open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary = path.with_suffix(".tmp")

    with temporary.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    temporary.replace(path)


def migrate_legacy(directory):
    directory = Path(directory)
    keyboard_path = directory / KEYBOARD_FILE
    mouse_path = directory / MOUSE_FILE
    legacy_path = directory / LEGACY_FILE

    if keyboard_path.exists() or not legacy_path.exists():
        return

    legacy = _read_json(legacy_path)

    gestures = legacy.get("gestures", {})
    if not isinstance(gestures, dict):
        gestures = {}

    old_mouse = legacy.get("mouse", {})
    if not isinstance(old_mouse, dict):
        old_mouse = {}

    mouse = {
        "settings": copy.deepcopy(MOUSE_DEFAULTS),
        "gestures": {
            role: {"name": label, "samples": []}
            for role, label in {**MOUSE_ACTIVATION, **MOUSE_ROLES}.items()
        },
    }

    for key, value in old_mouse.items():
        if key not in ("bindings", "min_confidence", "enabled") and key in MOUSE_DEFAULTS:
            mouse["settings"][key] = value

    for role, gesture_id in (old_mouse.get("bindings") or {}).items():
        if role in MOUSE_ROLES and gesture_id in gestures:
            moved = gestures.pop(gesture_id)
            mouse["gestures"][role]["samples"] = moved.get("samples", [])

    _write_json(keyboard_path, {"gestures": gestures})

    if not mouse_path.exists():
        _write_json(mouse_path, mouse)

class JsonStore:

    def __init__(self, path, default):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self._default = default

        if not self.path.exists():
            self.save(copy.deepcopy(default))

        self.data = self.load()

    def load(self):
        try:
            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, dict):
                raise ValueError("O arquivo de configuração precisa ser um objeto JSON.")

            return data

        except (json.JSONDecodeError, OSError, ValueError):
            return copy.deepcopy(self._default)

    def save(self, data=None):
        if data is not None:
            self.data = data

        _write_json(self.path, self.data)


class ConfigManager(JsonStore):
    """Gestos do teclado: cada gesto dispara uma ação (tecla, atalho...)."""

    def __init__(self, path=None):
        if path is None:
            migrate_legacy(config_dir())
            path = config_dir() / KEYBOARD_FILE

        super().__init__(path, {"gestures": {}})

        self.data.setdefault("gestures", {})

    def all_gestures(self):
        return self.data.setdefault("gestures", {})

    def get(self, gesture_id):
        return self.all_gestures().get(gesture_id)

    def set(self, gesture_id, gesture):
        self.all_gestures()[gesture_id] = gesture
        self.save()

    def remove(self, gesture_id):
        self.all_gestures().pop(gesture_id, None)
        self.save()

class MouseConfig(JsonStore):

    def __init__(self, path=None):
        if path is None:
            migrate_legacy(config_dir())
            path = config_dir() / MOUSE_FILE

        super().__init__(
            path,
            {"settings": copy.deepcopy(MOUSE_DEFAULTS), "gestures": {}}
        )

        self.data.setdefault("settings", {})
        for old in ("enabled", "activation_window", "emergency_hold"):   # chaves antigas
            self.data["settings"].pop(old, None)
        self.all_gestures()      # garante o gesto de ativação e os papéis do mouse

    def all_gestures(self):
        gestures = self.data.setdefault("gestures", {})

        for key, label in {**MOUSE_ACTIVATION, **MOUSE_ROLES}.items():
            entry = gestures.setdefault(key, {})
            entry.setdefault("name", label)
            entry.setdefault("samples", [])

        # descarta chaves desconhecidas
        for key in list(gestures):
            if (
                key not in MOUSE_ROLES
                and key not in MOUSE_ACTIVATION
            ):
                gestures.pop(key)

        return gestures

    def button_gestures(self):
        """Só os gestos dos botões (usados DENTRO do modo mouse)."""
        everything = self.all_gestures()
        return {role: everything[role] for role in MOUSE_ROLES}

    def activation_gestures(self):
        """Só o gesto de ativação."""
        everything = self.all_gestures()
        return {step: everything[step] for step in MOUSE_ACTIVATION}

    def special_gestures(self):
        """Gesto de ativação, válido em qualquer modo."""
        return self.activation_gestures()

    def activation_ready(self):
        """True quando o gesto de ativação já tem amostras gravadas."""
        return all(
            gesture.get("samples")
            for gesture in self.activation_gestures().values()
        )

    def get(self, key):
        return self.all_gestures().get(key)

    def set(self, key, gesture):
        self.all_gestures()[key] = gesture
        self.save()

    def clear(self, key):
        self.all_gestures()[key]["samples"] = []
        self.save()

    # ---- ajustes ---------------------------------------------------

    def settings(self):
        merged = copy.deepcopy(MOUSE_DEFAULTS)
        merged.update(self.data.get("settings", {}))
        merged.pop("enabled", None)
        merged.pop("activation_window", None)
        return merged

    def save_settings(self, settings):
        settings = dict(settings)
        settings.pop("enabled", None)
        self.data["settings"] = settings
        self.save()
