import time
import uuid
import tempfile
from pathlib import Path

import cv2

from PySide6.QtCore import QTimer, Qt, QSettings, QPoint, QPointF, QRectF, QSize
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QIcon
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QCheckBox,
    QFrame,
    QFormLayout,
    QMessageBox,
    QInputDialog,
    QProgressBar,
    QScrollArea,
    QTabWidget,
)

from handify.config.manager import (
    ConfigManager,
    MouseConfig,
    MOUSE_ROLES,
    MOUSE_ACTIVATION,
)
from handify.actions.executor import ActionExecutor
from handify.actions.mouse_mode import MouseMode
from handify.actions.activation import ActivationGesture

from handify.recognition.gesture_recognizer import GestureRecognizer
from handify.recognition.controller import GestureController


# =========================================================
# TEMA
# =========================================================
# Grafite azulado + índigo suave como destaque.
# Verde = sucesso, âmbar = aviso, coral = erro.

STYLE_TEMPLATE = """
* {
    font-family: "Inter", "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
    color: @text;
}

QMainWindow, QScrollArea, QScrollArea > QWidget > QWidget {
    background: @bg;
}

QDialog, QInputDialog, QMessageBox {
    background: @bg;
}
QDialog QLabel, QInputDialog QLabel, QMessageBox QLabel {
    background: transparent;
    color: @text;
    font-size: 13px;
}
QDialog QPushButton, QMessageBox QPushButton {
    min-width: 84px;
}
QDialog QPushButton:default, QMessageBox QPushButton:default {
    background: @accent;
    border-color: @accent;
    color: #FFFFFF;
}

QFrame#card {
    background: @card;
    border: 1px solid @border;
    border-radius: 12px;
}

QTabWidget::pane {
    border: none;
    background: transparent;
}
QTabBar {
    background: transparent;
}
QTabBar::tab {
    background: @btn;
    color: @muted;
    border: 1px solid @btnborder;
    border-radius: 8px;
    padding: 8px 26px;
    margin-right: 6px;
    margin-bottom: 8px;
    font-weight: 600;
}
QTabBar::tab:hover {
    background: @btnhover;
}
QTabBar::tab:selected {
    background: @accent;
    border-color: @accent;
    color: #FFFFFF;
}

QLabel#cardTitle {
    font-size: 15px;
    font-weight: 600;
    color: @title;
}

QLabel#muted {
    color: @muted;
}

QLabel#video {
    background: @video;
    border: 1px solid @border;
    border-radius: 12px;
    color: @videotext;
    font-size: 15px;
}

QLabel#gestureName {
    font-size: 22px;
    font-weight: 600;
    color: @gesture;
}

QLabel#status {
    background: @surface;
    border-radius: 8px;
    padding: 9px 12px;
    color: @statustext;
}
QLabel#status[kind="ok"]    { background: @okbg; color: @okfg; }
QLabel#status[kind="warn"]  { background: @warnbg; color: @warnfg; }
QLabel#status[kind="error"] { background: @errbg; color: @errfg; }

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background: @field;
    border: 1px solid @inputborder;
    border-radius: 8px;
    padding: 7px 10px;
    min-height: 20px;
    selection-background-color: @accent;
}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: @hoverborder;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: @focus;
}
QComboBox::drop-down { border: none; width: 26px; }
QComboBox QAbstractItemView {
    background: @card;
    border: 1px solid @inputborder;
    selection-background-color: @selected;
    outline: none;
}

QSpinBox, QDoubleSpinBox {
    padding-right: 30px;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 26px;
    margin: 1px 1px 0 0;
    border: none;
    border-left: 1px solid @inputborder;
    border-top-right-radius: 7px;
    background: transparent;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 26px;
    margin: 0 1px 1px 0;
    border: none;
    border-left: 1px solid @inputborder;
    border-bottom-right-radius: 7px;
    background: transparent;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background: @surface;
}

QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed,
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {
    background: @btnpressed;
}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image: url(@uparrow);
    width: 12px;
    height: 12px;
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: url(@downarrow);
    width: 12px;
    height: 12px;
}

QPushButton {
    background: @btn;
    border: 1px solid @btnborder;
    border-radius: 8px;
    padding: 9px 16px;
    font-weight: 500;
}
QPushButton:hover   { background: @btnhover; }
QPushButton:pressed { background: @btnpressed; }
QPushButton:focus   { border-color: @focus; }

QPushButton#primary {
    background: @accent;
    border: 1px solid @accent;
    color: #FFFFFF;
    font-weight: 600;
}
QPushButton#primary:hover   { background: @accenthover; }
QPushButton#primary:pressed { background: @accentpressed; }

QPushButton#danger {
    background: transparent;
    border: 1px solid @dangerborder;
    color: @errfg;
}
QPushButton#danger:hover { background: @errbg; }

QListWidget {
    background: @field;
    border: 1px solid @border;
    border-radius: 10px;
    padding: 4px;
    outline: none;
}
QListWidget::item {
    padding: 9px 10px;
    border-radius: 7px;
}
QListWidget::item:hover    { background: @surface; }
QListWidget::item:selected { background: @selected; color: @selectedtext; }

QCheckBox { spacing: 8px; }
QCheckBox::indicator {
    width: 18px; height: 18px;
    border-radius: 5px;
    border: 1px solid @hoverborder;
    background: @field;
}
QCheckBox::indicator:checked {
    background: @accent;
    border-color: @accent;
}

QProgressBar {
    background: @field;
    border: none;
    border-radius: 4px;
    max-height: 8px;
    min-height: 8px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: @accent;
    border-radius: 4px;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: @scroll;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QFrame#divider { background: @border; }

QToolTip {
    background: @surface;
    color: @text;
    border: 1px solid @btnborder;
    padding: 4px 8px;
}
"""

PALETTES = {
    "light": {
        "bg": "#EEF0F6", "field": "#F6F7FB", "card": "#FFFFFF",
        "border": "#DDE1EC", "title": "#151A2B", "text": "#232A3D",
        "muted": "#6A7390", "video": "#E4E8F2", "videotext": "#7A829C",
        "surface": "#EDF0F8", "statustext": "#4A5270",
        "okbg": "#DDF3E5", "okfg": "#1F6B3F",
        "warnbg": "#FBEFD0", "warnfg": "#7A5A10",
        "errbg": "#FBE1E3", "errfg": "#A12B36",
        "inputborder": "#CBD1E1", "hoverborder": "#AEB6CE",
        "focus": "#6F7DFF", "accent": "#5A69F0",
        "accenthover": "#6D7BFF", "accentpressed": "#4A58DB",
        "selected": "#DDE1FF", "selectedtext": "#1D2250",
        "btn": "#EEF0F8", "btnborder": "#D3D8E6",
        "btnhover": "#E3E7F4", "btnpressed": "#D8DDEE",
        "dangerborder": "#EBC3C7", "scroll": "#C3C9DA",
        "gesture": "#4A58DB",
    },
    "dark": {
        "bg": "#171A23", "field": "#171A23", "card": "#1F2330",
        "border": "#2C3142", "title": "#F4F6FC", "text": "#E6E9F2",
        "muted": "#8B93AA", "video": "#0F1117", "videotext": "#6B7390",
        "surface": "#232838", "statustext": "#B9C0D6",
        "okbg": "#1E3329", "okfg": "#8FE0B0",
        "warnbg": "#3A3120", "warnfg": "#F0CD85",
        "errbg": "#3C2326", "errfg": "#F2A0A6",
        "inputborder": "#333A50", "hoverborder": "#4A5273",
        "focus": "#7C8CFF", "accent": "#6F7DFF",
        "accenthover": "#8290FF", "accentpressed": "#5E6BEA",
        "selected": "#343C66", "selectedtext": "#FFFFFF",
        "btn": "#2A3042", "btnborder": "#353C52",
        "btnhover": "#333A52", "btnpressed": "#262B3C",
        "dangerborder": "#5A3A40", "scroll": "#343B52",
        "gesture": "#A9B4FF",
    },
}


# =========================================================
# ÍCONES DAS SETAS DOS SPINBOXES
# =========================================================

_ARROW_CACHE = {}


def make_arrow_icons(theme, color):
    """Gera (uma vez por tema) os PNGs das setas e devolve os caminhos."""

    if theme in _ARROW_CACHE:
        return _ARROW_CACHE[theme]

    folder = Path(tempfile.gettempdir()) / "handify_icons"
    folder.mkdir(exist_ok=True)

    paths = {}

    for name in ("up", "down"):

        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor(color))
        pen.setWidthF(2.4)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)

        c = pixmap.rect().center()

        if name == "up":
            points = [c + QPoint(-6, 3), c + QPoint(0, -3), c + QPoint(6, 3)]
        else:
            points = [c + QPoint(-6, -3), c + QPoint(0, 3), c + QPoint(6, -3)]

        painter.drawPolyline(points)
        painter.end()

        path = folder / f"{theme}_{name}.png"
        pixmap.save(str(path), "PNG")

        paths[name] = path.as_posix()

    _ARROW_CACHE[theme] = paths
    return paths


def make_theme_icon(kind, color):
    """Desenha os ícones de lua/sol sem depender de fontes de emoji."""
    size = 48
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(3.2)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    if kind == "moon":
        # Silhueta de lua crescente, preenchida para ficar legível em 22 px.
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(34, 7)
        path.cubicTo(17, 8, 8, 21, 13, 33)
        path.cubicTo(19, 45, 35, 44, 41, 31)
        path.cubicTo(31, 37, 22, 30, 22, 21)
        path.cubicTo(22, 15, 27, 9, 34, 7)
        path.closeSubpath()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(color))
        painter.drawPath(path)
    else:
        painter.drawEllipse(QRectF(16, 16, 16, 16))
        import math
        for angle in range(0, 360, 45):
            radians = math.radians(angle)
            x1 = 24 + math.cos(radians) * 14
            y1 = 24 + math.sin(radians) * 14
            x2 = 24 + math.cos(radians) * 19
            y2 = 24 + math.sin(radians) * 19
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    painter.end()
    return QIcon(pixmap)


def make_tab_icon(kind, color_off, color_on):
    """
    Ícone desenhado em código ('keyboard' ou 'mouse').
    Estado Off = aba inativa (cor suave); On = aba selecionada (branco).
    """

    icon = QIcon()
    size = 48     # desenhado grande e reduzido: fica nítido em telas HiDPI

    for state, color in ((QIcon.Off, color_off), (QIcon.On, color_on)):

        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor(color))
        pen.setWidthF(3.2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        if kind == "keyboard":

            # corpo do teclado
            painter.drawRoundedRect(QRectF(4, 11, 40, 26), 5, 5)

            # fileiras de teclas
            for row_y in (18.5, 25.5):
                for x in (11, 18, 25, 32, 39):
                    painter.drawPoint(QPointF(x, row_y))

            # barra de espaço
            painter.drawLine(QPointF(14, 32), QPointF(34, 32))

        else:

            # corpo do mouse
            painter.drawRoundedRect(QRectF(13, 5, 22, 38), 11, 11)

            # divisória dos botões e roda de rolagem
            painter.drawLine(QPointF(24, 5), QPointF(24, 18))
            painter.drawLine(QPointF(13, 18), QPointF(35, 18))
            painter.drawLine(QPointF(24, 11), QPointF(24, 14))

        painter.end()

        icon.addPixmap(pixmap, QIcon.Normal, state)

    return icon


def build_style(theme):
    """Gera a folha de estilo (QSS) para o tema 'light' ou 'dark'."""

    palette = dict(PALETTES.get(theme, PALETTES["light"]))

    arrows = make_arrow_icons(theme, palette["muted"])
    palette["uparrow"] = arrows["up"]
    palette["downarrow"] = arrows["down"]

    style = STYLE_TEMPLATE

    # Nomes maiores primeiro (@selectedtext antes de @selected, etc.)
    for key in sorted(palette, key=len, reverse=True):
        style = style.replace("@" + key, palette[key])

    return style


def make_card(title=None, subtitle=None):
    """Cria um painel arredondado e devolve (frame, layout)."""

    frame = QFrame()
    frame.setObjectName("card")

    layout = QVBoxLayout(frame)
    layout.setContentsMargins(18, 16, 18, 18)
    layout.setSpacing(12)

    if title:
        label = QLabel(title)
        label.setObjectName("cardTitle")
        layout.addWidget(label)

    if subtitle:
        hint = QLabel(subtitle)
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        layout.addWidget(hint)

    return frame, layout


# =========================================================
# PRÉ-VISUALIZAÇÃO DA MÃO
# =========================================================

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]


def sample_to_points(sample):
    """Converte uma amostra em 21 pares (x, y). Devolve [] se não reconhecer."""

    if sample is None:
        return []

    try:
        sample = list(sample)

        if not sample:
            return []

        if isinstance(sample[0], (list, tuple)):
            points = [(float(p[0]), float(p[1])) for p in sample]

        else:
            flat = [float(v) for v in sample]

            if len(flat) == 63:
                stride = 3
            elif len(flat) == 42:
                stride = 2
            else:
                return []

            points = [
                (flat[i], flat[i + 1])
                for i in range(0, len(flat), stride)
            ]

    except (TypeError, ValueError, IndexError):
        return []

    return points if len(points) == 21 else []


class HandPreview(QWidget):
    """Desenha o esqueleto da mão a partir de uma amostra."""

    def __init__(self, parent=None):
        
        super().__init__(parent)

        self.points = []
        self.line_color = QColor("#8B93AA")
        self.dot_color = QColor("#6F7DFF")

        self.setMinimumSize(160, 160)

    def set_colors(self, line, dot):

        self.line_color = QColor(line)
        self.dot_color = QColor(dot)
        self.update()

    def set_sample(self, sample):

        self.points = sample_to_points(sample)
        self.update()

    def paintEvent(self, event):

        if not self.points:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]

        min_x, min_y = min(xs), min(ys)

        span_x = (max(xs) - min_x) or 1.0
        span_y = (max(ys) - min_y) or 1.0

        margin = 14
        size = min(self.width(), self.height()) - 2 * margin
        scale = size / max(span_x, span_y)

        offset_x = (self.width() - span_x * scale) / 2
        offset_y = (self.height() - span_y * scale) / 2

        mapped = [
            QPointF(
                offset_x + (x - min_x) * scale,
                offset_y + (y - min_y) * scale,
            )
            for x, y in self.points
        ]

        pen = QPen(self.line_color)
        pen.setWidthF(2.2)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        for a, b in HAND_CONNECTIONS:
            painter.drawLine(mapped[a], mapped[b])

        painter.setPen(Qt.NoPen)
        painter.setBrush(self.dot_color)

        for point in mapped:
            painter.drawEllipse(point, 3.5, 3.5)

        painter.end()


class MainWindow(QMainWindow):

    # Rótulo da ação -> campos relevantes no formulário
    ACTION_FIELDS = {
        "Tecla": ["key"],
        "Combinação": ["keys"],
        "Sequência": ["sequence"],
        "Clique": ["button"],
        "Duplo clique": ["button"],
        "Rolagem": ["amount"],
        "Rolagem horizontal": ["amount"],
        "Comando especial": ["special"],
    }

    def __init__(self):

        super().__init__()

        self.setWindowTitle("SIGCD — Gestos personalizados")
        self.resize(1240, 760)
        self.setMinimumSize(1000, 640)

        self.settings = QSettings("handify", "sigcd")
        self.theme = self.settings.value("theme", "light")
        self.apply_theme(self.theme, save=False)

        self.config = ConfigManager()
        self.executor = ActionExecutor()
        self.recognizer = GestureRecognizer()
        self.controller = GestureController(self.config, self.executor)
        self.mouse_config = MouseConfig()
        self.mouse_mode = MouseMode(self.mouse_config)
        self.mouse_cfg = self.mouse_config.settings()
        self.activation = ActivationGesture(
            hold=self.mouse_cfg["activation_hold"]
        )

        self.capture_store = None
        self.last_mouse_role = None

        self.camera = cv2.VideoCapture(0, cv2.CAP_V4L2)

        if not self.camera.isOpened():
            self.camera = cv2.VideoCapture(0)

        self.current_sample = None
        self.capture_gesture_id = None
        self.capture_samples = []
        self.capture_countdown = 5
        self.capture_target = 10
        self.is_capturing = False

        # Timer da contagem regressiva
        self.countdown_timer = QTimer(self)
        self.countdown_timer.setInterval(1000)
        self.countdown_timer.timeout.connect(self.update_countdown)

        # Timer de coleta das amostras
        self.sample_timer = QTimer(self)
        self.sample_timer.setInterval(150)
        self.sample_timer.timeout.connect(self.collect_sample)

        self.build_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_frame)
        self.timer.start(30)

    # =====================================================
    # INTERFACE
    # =====================================================

    def build_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(20)

        root.addLayout(self.build_camera_panel(), 3)
        root.addWidget(self.build_side_panel(), 2)

        self.refresh_list()
        self.update_action_fields()
        self.apply_theme(self.theme, save=False)
        self.update_mode_badge()

    # -----------------------------------------------------
    # Câmera
    # -----------------------------------------------------

    def build_camera_panel(self):

        left = QVBoxLayout()
        left.setSpacing(14)

        self.video = QLabel("Aguardando câmera…")
        self.video.setObjectName("video")
        self.video.setMinimumSize(640, 480)
        self.video.setAlignment(Qt.AlignCenter)

        left.addWidget(self.video, 1)

        # Modo atual (teclado / mouse)

        self.mode_badge = QLabel("")
        self.mode_badge.setObjectName("status")
        self.mode_badge.setAlignment(Qt.AlignCenter)
        self.mode_badge.setMinimumHeight(34)
        self.mode_badge.setToolTip(
            "O modo mouse liga e desliga segurando o gesto de ativação "
            "(aba Mouse)."
        )

        left.addWidget(self.mode_badge)

        # Gesto detectado

        info, info_layout = make_card()

        caption = QLabel("Gesto detectado")
        caption.setObjectName("muted")

        self.detected = QLabel("")
        self.detected.setObjectName("gestureName")
        self.detected.setMinimumHeight(32)
        self.detected.setToolTip("Identificação do gesto realizado")

        top = QHBoxLayout()
        top.addWidget(caption)
        top.addStretch()

        self.confidence = QLabel("")
        self.confidence.setObjectName("muted")
        top.addWidget(self.confidence)

        self.confidence_bar = QProgressBar()
        self.confidence_bar.setRange(0, 100)
        self.confidence_bar.setValue(0)
        self.confidence_bar.setTextVisible(False)

        info_layout.setSpacing(6)
        info_layout.addLayout(top)
        info_layout.addWidget(self.detected)
        info_layout.addWidget(self.confidence_bar)

        left.addWidget(info)

        self.capture_button = QPushButton("Capturar amostra do gesto atual")
        self.capture_button.setObjectName("primary")
        self.capture_button.setCursor(Qt.PointingHandCursor)
        self.capture_button.clicked.connect(self.capture_gesture)

        left.addWidget(self.capture_button)

        self.capture_progress = QLabel("")
        self.capture_progress.setObjectName("muted")
        self.capture_progress.setAlignment(Qt.AlignCenter)
        self.capture_progress.hide()

        left.addWidget(self.capture_progress)

        return left

    # -----------------------------------------------------
    # Painel lateral
    # -----------------------------------------------------

    def build_side_panel(self):

        container = QWidget()

        column = QVBoxLayout(container)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(10)

        self.theme_button = QPushButton()
        self.theme_button.setCursor(Qt.PointingHandCursor)
        self.theme_button.setFixedSize(40, 40)
        self.theme_button.setToolTip("Ativar modo escuro")
        self.theme_button.clicked.connect(self.toggle_theme)

        # Duas abas: gestos que digitam (teclado) e gestos que movem o
        # mouse. Cada uma tem a sua configuração e o seu arquivo JSON.
        self.tabs = QTabWidget()
        self.tabs.setUsesScrollButtons(False)
        self.tabs.setIconSize(QSize(20, 20))
        self.tabs.addTab(self.build_keyboard_tab(), "Teclado")
        self.tabs.addTab(self.build_mouse_tab(), "Mouse")
        # O botão de tema ocupa o canto superior direito da própria barra
        # de abas, mantendo tema, Teclado e Mouse alinhados na mesma linha.
        self.tabs.setCornerWidget(self.theme_button, Qt.TopRightCorner)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.update_tab_icons()

        column.addWidget(self.tabs, 1)

        self.status = QLabel("Pronto.")
        self.status.setObjectName("status")
        self.status.setWordWrap(True)

        column.addWidget(self.status)

        container.setMinimumWidth(400)

        return container

    def wrap_scroll(self, content):

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(content)

        return scroll

    def build_keyboard_tab(self):

        content = QWidget()

        right = QVBoxLayout(content)
        right.setContentsMargins(0, 4, 8, 0)
        right.setSpacing(14)

        right.addWidget(self.build_gesture_card())
        right.addWidget(self.build_form_card())

        save_button = QPushButton("Salvar configuração")
        save_button.setObjectName("primary")
        save_button.setCursor(Qt.PointingHandCursor)
        save_button.clicked.connect(self.save_gesture)

        test_button = QPushButton("Testar ação")
        test_button.setCursor(Qt.PointingHandCursor)
        test_button.clicked.connect(self.test_action)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addWidget(test_button)
        actions.addWidget(save_button, 1)

        right.addLayout(actions)
        right.addStretch()

        return self.wrap_scroll(content)

    def build_gesture_card(self):

        card, layout = make_card("Gestos cadastrados")

        self.gesture_combo = QComboBox()
        self.gesture_combo.setCursor(Qt.PointingHandCursor)
        self.gesture_combo.setToolTip("Selecione um gesto cadastrado")
        self.gesture_combo.currentIndexChanged.connect(
            self.on_gesture_changed
        )

        layout.addWidget(self.gesture_combo)

        # Pré-visualização da amostra salva

        preview_caption = QLabel("Amostra mais recente")
        preview_caption.setObjectName("muted")
        layout.addWidget(preview_caption)

        self.preview = HandPreview()
        layout.addWidget(self.preview)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        new_button = QPushButton("Novo gesto")
        new_button.setCursor(Qt.PointingHandCursor)
        new_button.clicked.connect(self.new_gesture)

        delete_button = QPushButton("Excluir")
        delete_button.setObjectName("danger")
        delete_button.setCursor(Qt.PointingHandCursor)
        delete_button.clicked.connect(self.delete_gesture)

        buttons.addWidget(new_button, 1)
        buttons.addWidget(delete_button)

        layout.addLayout(buttons)

        return card

    def build_form_card(self):

        card, layout = make_card("Configuração do gesto")

        self.form = QFormLayout()
        self.form.setHorizontalSpacing(14)
        self.form.setVerticalSpacing(10)
        self.form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        form = self.form

        # Nome

        self.name_edit = QLineEdit()
        form.addRow("Nome", self.name_edit)

        # Ação

        self.action_combo = QComboBox()
        self.action_combo.addItems(list(self.ACTION_FIELDS.keys()))
        self.action_combo.currentTextChanged.connect(
            self.update_action_fields
        )
        form.addRow("Ação", self.action_combo)

        # Tecla

        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("enter, space, f5…")
        form.addRow("Tecla", self.key_edit)

        # Combinação

        self.keys_edit = QLineEdit()
        self.keys_edit.setPlaceholderText("ctrl+shift+esc")
        form.addRow("Combinação", self.keys_edit)

        # Sequência

        self.sequence_edit = QLineEdit()
        self.sequence_edit.setPlaceholderText(
            "ctrl+c | delay:0.2 | ctrl+v"
        )
        self.sequence_edit.setToolTip(
            "Separe os passos com |. Use delay:segundos para pausas."
        )
        form.addRow("Sequência", self.sequence_edit)

        # Botão

        self.button_combo = QComboBox()
        self.button_combo.addItems(["left", "right", "middle"])
        form.addRow("Botão", self.button_combo)

        # Duração (usada apenas por 'hold')

        self.duration = QDoubleSpinBox()
        self.duration.setRange(0, 60)
        self.duration.setDecimals(2)
        self.duration.setSuffix(" s")
        self.duration.setValue(1)
        form.addRow("Duração", self.duration)

        # Quantidade

        self.amount_spin = QSpinBox()
        self.amount_spin.setRange(-1000, 1000)
        self.amount_spin.setValue(50)
        self.amount_spin.setToolTip(
            "Valores negativos rolam no sentido contrário."
        )
        form.addRow("Rolagem", self.amount_spin)

        # Especial

        self.special_combo = QComboBox()
        self.special_combo.addItems(["screenshot"])
        form.addRow("Especial", self.special_combo)

        layout.addLayout(form)

        # Divisor

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setObjectName("divider")
        layout.addWidget(divider)

        # Ajustes gerais

        general = QFormLayout()
        general.setHorizontalSpacing(14)
        general.setVerticalSpacing(10)
        general.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.min_confidence = QSpinBox()
        self.min_confidence.setRange(0, 100)
        self.min_confidence.setSingleStep(5)
        self.min_confidence.setSuffix(" %")
        self.min_confidence.setValue(65)
        self.min_confidence.setToolTip(
            "Só executa a ação acima desta confiança."
        )
        general.addRow("Confiança mínima", self.min_confidence)

        self.cooldown = QDoubleSpinBox()
        self.cooldown.setRange(0, 60)
        self.cooldown.setDecimals(2)
        self.cooldown.setSuffix(" s")
        self.cooldown.setValue(0.5)
        self.cooldown.setToolTip(
            "Tempo de espera antes de repetir a ação."
        )
        general.addRow("Cooldown", self.cooldown)

        self.enabled = QCheckBox("Gesto ativado")
        self.enabled.setChecked(True)
        general.addRow(self.enabled)

        layout.addLayout(general)

        # Campos que podem ser mostrados/ocultados

        self.field_widgets = {
            "key": self.key_edit,
            "keys": self.keys_edit,
            "sequence": self.sequence_edit,
            "button": self.button_combo,
            "amount": self.amount_spin,
            "special": self.special_combo,
        }

        return card

    # =====================================================
    # TEMA
    # =====================================================

    def apply_theme(self, theme, save=True):

        self.theme = theme
        self.setStyleSheet(build_style(theme))

        if hasattr(self, "theme_button"):
            # Ícone vetorial desenhado com QPainter (não depende de fonte emoji).
            icon_color = PALETTES.get(theme, PALETTES["light"])["muted"]
            self.theme_button.setText("")
            self.theme_button.setIcon(make_theme_icon("moon" if theme == "light" else "sun", icon_color))
            self.theme_button.setIconSize(QSize(22, 22))
            self.theme_button.setToolTip(
                "Ativar modo escuro" if theme == "light"
                else "Ativar modo claro"
            )

        palette = PALETTES.get(theme, PALETTES["light"])

        for name in ("preview", "mouse_preview"):
            if hasattr(self, name):
                getattr(self, name).set_colors(
                    palette["muted"], palette["accent"]
                )

        if hasattr(self, "tabs"):
            self.update_tab_icons()

        if save:
            self.settings.setValue("theme", theme)

    def update_tab_icons(self):
        """Ícones das abas, na cor do tema (branco quando selecionada)."""

        palette = PALETTES.get(self.theme, PALETTES["light"])

        for index, kind in enumerate(("keyboard", "mouse")):
            self.tabs.setTabIcon(
                index,
                make_tab_icon(kind, palette["muted"], "#FFFFFF")
            )

    def toggle_theme(self):

        self.apply_theme(
            "dark" if self.theme == "light" else "light"
        )

    # =====================================================
    # CAMPOS CONTEXTUAIS
    # =====================================================

    def update_action_fields(self, *_):
        """Mostra só os campos que a ação escolhida realmente usa."""

        visible = self.ACTION_FIELDS.get(
            self.action_combo.currentText(),
            []
        )

        for name, widget in self.field_widgets.items():

            show = name in visible

            widget.setVisible(show)

            label = self.form.labelForField(widget)

            if label:
                label.setVisible(show)

        # "Duração" só existe para 'hold', que não está na lista.
        self.duration.setVisible(False)

        label = self.form.labelForField(self.duration)

        if label:
            label.setVisible(False)

    # =====================================================
    # STATUS
    # =====================================================

    def set_status(self, text, kind="info"):

        self.status.setText(text)
        self.status.setProperty("kind", kind)

        # Reaplica o estilo para refletir a nova propriedade
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

    # =====================================================
    # LISTA
    # =====================================================

    def selected_id(self):

        # None quando o dropdown está vazio
        return self.gesture_combo.currentData()

    def refresh_list(self):

        current = self.selected_id()

        self.gesture_combo.blockSignals(True)
        self.gesture_combo.clear()

        for gesture_id, gesture in self.config.all_gestures().items():

            self.gesture_combo.addItem(
                gesture.get("name") or gesture_id,
                gesture_id
            )

        index = self.gesture_combo.findData(current) if current else -1

        if index < 0 and self.gesture_combo.count():
            index = 0

        self.gesture_combo.setCurrentIndex(index)
        self.gesture_combo.blockSignals(False)

        self.load_gesture(self.selected_id())

    def on_gesture_changed(self, index):

        self.load_gesture(self.gesture_combo.itemData(index))

    # =====================================================
    # NOVO GESTO
    # =====================================================

    def new_gesture(self):

        dialog = QInputDialog(self)
        dialog.setStyleSheet(build_style(self.theme))
        dialog.setWindowTitle("Novo gesto")
        dialog.setLabelText("Nome do gesto:")
        dialog.setTextValue("")
        dialog.setOkButtonText("Criar")
        dialog.setCancelButtonText("Cancelar")
        dialog.setMinimumWidth(380)

        if dialog.exec() != QInputDialog.Accepted:
            return

        name = dialog.textValue().strip()

        if not name:
            return

        gesture_id = uuid.uuid4().hex

        self.config.set(
            gesture_id,
            {
                "name": name,
                "samples": [],
                "enabled": True,
                "min_confidence": 0.65,
                "cooldown": 0.5,
                "action": {
                    "type": "key",
                    "key": "enter"
                }
            }
        )

        self.refresh_list()

        self.gesture_combo.setCurrentIndex(
            self.gesture_combo.findData(gesture_id)
        )

        self.set_status(
            "Gesto criado. Mostre a mão à câmera e capture algumas amostras.",
            "ok"
        )

    # =====================================================
    # EXCLUIR
    # =====================================================

    def delete_gesture(self):

        gesture_id = self.selected_id()

        if not gesture_id:
            return

        self.config.remove(gesture_id)
        self.refresh_list()

        self.set_status("Gesto removido.", "warn")

    # =====================================================
    # CAPTURAR
    # =====================================================

    def capture_gesture(self):

        # A aba ativa decide onde as amostras serão gravadas.
        if self.tabs.currentIndex() == 1:
            store = self.mouse_config
            gesture_id = self.mouse_role_combo.currentData()
        else:
            store = self.config
            gesture_id = self.selected_id()

        if not gesture_id:
            QMessageBox.warning(
                self,
                "Nenhum gesto",
                "Crie ou selecione um gesto primeiro."
            )
            return

        if self.is_capturing:
            return

        self.capture_store = store
        self.capture_gesture_id = gesture_id
        self.capture_samples = []
        self.capture_countdown = 5
        self.is_capturing = True

        self.capture_button.setEnabled(False)
        self.capture_progress.show()

        self.capture_progress.setText(
            "Prepare-se... 5"
        )

        self.set_status(
            "Captura iniciando em 5 segundos...",
            "warn"
        )

        self.countdown_timer.start()

    def update_countdown(self):

        self.capture_countdown -= 1

        if self.capture_countdown > 0:

            self.capture_progress.setText(
                f"Prepare-se... {self.capture_countdown}"
            )

            return

        self.countdown_timer.stop()

        self.capture_progress.setText(
            f"Capturando amostras: 0/{self.capture_target}"
        )

        self.set_status(
            "Capturando amostras do gesto...",
            "warn"
        )

        self.sample_timer.start()

    def collect_sample(self):

        if self.current_sample is None:
            return

        # Verifica se a amostra contém os 21 pontos da mão
        if not sample_to_points(self.current_sample):
            return

        # Guarda uma cópia independente da amostra
        sample = [
            list(point) if isinstance(point, (list, tuple)) else point
            for point in self.current_sample
        ]

        self.capture_samples.append(sample)

        count = len(self.capture_samples)

        self.capture_progress.setText(
            f"Capturando amostras: {count}/{self.capture_target}"
        )

        self.set_status(
            f"Coletando amostras: {count}/{self.capture_target}",
            "warn"
        )

        if count >= self.capture_target:
            self.finish_capture()

    def finish_capture(self):

        self.sample_timer.stop()
        self.countdown_timer.stop()

        gesture_id = self.capture_gesture_id

        store = self.capture_store

        gesture = store.get(gesture_id)

        if not gesture:
            self.cancel_capture()
            return

        gesture.setdefault("samples", [])

        # Adiciona as 10 novas amostras
        gesture["samples"].extend(self.capture_samples)

        # Persiste no JSON (keyboard.json ou mouse.json)
        store.set(gesture_id, gesture)

        # Atualiza a pré-visualização
        if store is self.mouse_config:
            self.refresh_mouse_roles()
        else:
            self.preview.set_sample(self.capture_samples[-1])

        total = len(gesture["samples"])

        self.capture_progress.setText(
            f"Captura concluída: {self.capture_target}/{self.capture_target}"
        )

        self.set_status(
            f"10 amostras salvas! Total do gesto: {total}.",
            "ok"
        )

        self.capture_button.setEnabled(True)

        self.capture_gesture_id = None
        self.capture_store = None
        self.capture_samples = []
        self.is_capturing = False

    def cancel_capture(self):

        self.countdown_timer.stop()
        self.sample_timer.stop()

        self.capture_button.setEnabled(True)
        self.capture_progress.hide()

        self.capture_gesture_id = None
        self.capture_store = None
        self.capture_samples = []
        self.is_capturing = False

        self.set_status(
            "Captura cancelada.",
            "error"
        )
    # =====================================================
    # CARREGAR
    # =====================================================

    def load_gesture(self, gesture_id):

        if not gesture_id:
            self.preview.set_sample(None)
            return

        gesture = self.config.get(gesture_id)

        if not gesture:
            self.preview.set_sample(None)
            return

        self.name_edit.setText(gesture.get("name", ""))
        self.enabled.setChecked(gesture.get("enabled", True))

        self.min_confidence.setValue(
            round(float(gesture.get("min_confidence", 0.65)) * 100)
        )

        self.cooldown.setValue(
            float(gesture.get("cooldown", 0.5))
        )

        action = gesture.get("action", {})
        action_type = action.get("type")

        labels = {
            "key": "Tecla",
            "hotkey": "Combinação",
            "sequence": "Sequência",
            "click": "Clique",
            "double_click": "Duplo clique",
            "scroll": "Rolagem",
            "hscroll": "Rolagem horizontal",
            "special": "Comando especial"
        }

        if action_type in labels:
            self.action_combo.setCurrentText(labels[action_type])

        self.key_edit.setText(action.get("key", ""))

        self.keys_edit.setText("+".join(action.get("keys", [])))

        self.sequence_edit.setText(
            self.sequence_to_text(action.get("actions", []))
        )

        self.button_combo.setCurrentText(action.get("button", "left"))

        self.duration.setValue(float(action.get("duration", 1)))

        self.amount_spin.setValue(int(action.get("amount", 5)))

        self.special_combo.setCurrentText(
            action.get("command", "screenshot")
        )

        samples = gesture.get("samples", [])
        self.preview.set_sample(samples[-1] if samples else None)

        self.update_action_fields()

    # =====================================================
    # SEQUÊNCIA → TEXTO
    # =====================================================

    def sequence_to_text(self, actions):

        parts = []

        for action in actions:

            action_type = action.get("type")

            if action_type == "delay":
                parts.append(f"delay:{action.get('seconds', 0)}")

            elif action_type == "key":
                parts.append(action.get("key", ""))

            elif action_type == "hotkey":
                parts.append("+".join(action.get("keys", [])))

        return " | ".join(parts)

    # =====================================================
    # CONSTRUIR AÇÃO
    # =====================================================

    def build_action(self):

        label = self.action_combo.currentText()

        if label == "Tecla":

            return {
                "type": "key",
                "key": self.key_edit.text().strip().lower()
            }

        if label == "Combinação":

            keys = [
                key.strip().lower()
                for key in self.keys_edit.text().split("+")
                if key.strip()
            ]

            return {"type": "hotkey", "keys": keys}

        if label == "Sequência":

            actions = []

            for part in self.sequence_edit.text().split("|"):

                part = part.strip()

                if not part:
                    continue

                if part.startswith("delay:"):

                    seconds = float(part.split(":", 1)[1])

                    actions.append(
                        {"type": "delay", "seconds": seconds}
                    )

                else:

                    keys = [
                        key.strip().lower()
                        for key in part.split("+")
                        if key.strip()
                    ]

                    if len(keys) == 1:
                        actions.append(
                            {"type": "key", "key": keys[0]}
                        )

                    else:
                        actions.append(
                            {"type": "hotkey", "keys": keys}
                        )

            return {"type": "sequence", "actions": actions}

        if label == "Clique":

            return {
                "type": "click",
                "button": self.button_combo.currentText()
            }

        if label == "Duplo clique":

            return {
                "type": "double_click",
                "button": self.button_combo.currentText()
            }

        if label == "Pressionar e segurar":

            return {
                "type": "hold",
                "key": self.key_edit.text().strip().lower(),
                "duration": self.duration.value()
            }

        if label == "Rolagem":

            return {
                "type": "scroll",
                "amount": self.amount_spin.value()
            }

        if label == "Rolagem horizontal":

            return {
                "type": "hscroll",
                "amount": self.amount_spin.value()
            }

        if label == "Comando especial":

            return {
                "type": "special",
                "command": self.special_combo.currentText()
            }

        raise ValueError("Ação inválida.")

    # =====================================================
    # SALVAR
    # =====================================================

    def save_gesture(self):

        gesture_id = self.selected_id()

        if not gesture_id:

            QMessageBox.warning(
                self,
                "Nenhum gesto",
                "Crie ou selecione um gesto."
            )

            return

        try:
            action = self.build_action()

        except Exception as exc:

            QMessageBox.critical(self, "Erro", str(exc))
            return

        gesture = self.config.get(gesture_id)

        gesture["name"] = self.name_edit.text().strip() or gesture_id
        gesture["enabled"] = self.enabled.isChecked()
        gesture["min_confidence"] = self.min_confidence.value() / 100
        gesture["cooldown"] = self.cooldown.value()
        gesture["action"] = action

        self.config.set(gesture_id, gesture)

        self.refresh_list()

        self.set_status("Configuração salva.", "ok")

    # =====================================================
    # TESTAR
    # =====================================================

    def test_action(self):

        try:

            self.executor.execute(self.build_action())

            self.set_status("Ação executada.", "ok")

        except Exception as exc:

            QMessageBox.critical(self, "Erro", str(exc))

    # =====================================================
    # FRAME
    # =====================================================

    def process_frame(self):

        ok, frame = self.camera.read()

        if not ok:
            return

        # Uma única detecção de mão por frame.
        #
        # Os modos são EXCLUSIVOS, então teclado e mouse não conflitam:
        #   modo teclado -> gestos do teclado
        #   modo mouse   -> gestos dos botões do mouse
        # O gesto de ativação (ex.: chifre, mantido ~1 s) vale nos dois
        # modos e liga/desliga o modo mouse.
        sample = self.recognizer.extract(frame)

        self.current_sample = sample

        cfg = self.mouse_cfg
        mouse_on = self.mouse_mode.active

        if mouse_on:
            main_source = "mouse"
            main_gestures = self.mouse_config.button_gestures()
        else:
            main_source = "keyboard"
            main_gestures = self.config.all_gestures()

        main_id, main_distance = self.recognizer.best_match(
            sample, main_gestures
        )

        # O gesto de ativação vale nos dois modos.
        special_id, special_distance = self.recognizer.best_match(
            sample, self.mouse_config.special_gestures()
        )

        threshold = self.recognizer.MATCH_THRESHOLD

        if special_distance < main_distance:
            source, gesture_id, distance = (
                "special", special_id, special_distance
            )
        else:
            source, gesture_id, distance = main_source, main_id, main_distance

        if gesture_id is None or distance > threshold:
            gesture_id, confidence = None, 0.0
        else:
            confidence = max(0.0, min(1.0, 1.0 - distance / threshold))

        accepted = confidence >= cfg["min_confidence"]

        keyboard_gesture = gesture_id if source == "keyboard" else None
        mouse_gesture = (
            gesture_id if source == "mouse" and accepted else None
        )
        activation_seen = (
            source == "special" and accepted and gesture_id == "activation"
        )
        # ---- Gesto de ativação: liga/desliga o modo mouse ---------------

        if not self.is_capturing:

            if self.mouse_config.activation_ready():

                if self.activation.update(activation_seen):
                    self.set_mouse_active(not mouse_on)
                    mouse_on = self.mouse_mode.active
                    keyboard_gesture = None
                    mouse_gesture = None


            else:
                self.activation.reset()

        # Enquanto o gesto de ativação está sendo segurado, o teclado fica
        # quieto para a pose não disparar atalhos sem querer.
        sequence_running = (
            self.activation.progress > 0
        )

        # ---- Painel "Gesto detectado" --------------------------------

        if gesture_id and not self.is_capturing:

            if source == "special":
                name = self.mouse_label(gesture_id)
            elif source == "mouse":
                name = f"Mouse · {MOUSE_ROLES[gesture_id]}"
            else:
                gesture = self.config.get(gesture_id)
                name = (gesture.get("name") or "").strip() or "Gesto sem nome"

            self.detected.setText(name)
            self.confidence.setText(f"{confidence:.0%}")
            self.confidence_bar.setValue(int(confidence * 100))

            # ---- Teclado: dispara a ação cadastrada ------------------

            if keyboard_gesture and not sequence_running:

                try:

                    executed = self.controller.process(
                        keyboard_gesture,
                        confidence
                    )

                    if executed:
                        self.set_status(f"Executado: {name}", "ok")

                except Exception as exc:

                    self.set_status(f"Erro: {exc}", "error")

        else:

            self.detected.setText("")
            self.confidence.setText("")
            self.confidence_bar.setValue(0)

        # ---- Mouse: cursor segue a mão + cliques/rolagem ---------------

        if not self.is_capturing:
            self.update_mouse(mouse_gesture)
        else:
            self.mouse_mode.release()

        # Mostrar câmera

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        height, width, channels = rgb.shape

        image = QImage(
            rgb.data,
            width,
            height,
            channels * width,
            QImage.Format_RGB888
        )

        pixmap = QPixmap.fromImage(image)

        self.video.setPixmap(
            pixmap.scaled(
                self.video.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

    # =====================================================
    # ABA MOUSE
    # =====================================================

    def build_mouse_tab(self):

        content = QWidget()

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 4, 8, 0)
        layout.setSpacing(14)

        layout.addWidget(self.build_mouse_gesture_card())
        layout.addWidget(self.build_mouse_settings_card())
        layout.addStretch()

        return self.wrap_scroll(content)

    def build_mouse_gesture_card(self):

        card, layout = make_card("Gestos do mouse")

        self.mouse_role_combo = QComboBox()
        self.mouse_role_combo.setCursor(Qt.PointingHandCursor)
        self.mouse_role_combo.currentIndexChanged.connect(
            self.on_mouse_role_changed
        )
        layout.addWidget(self.mouse_role_combo)

        preview_caption = QLabel("Amostra mais recente")
        preview_caption.setObjectName("muted")
        layout.addWidget(preview_caption)

        self.mouse_preview = HandPreview()
        layout.addWidget(self.mouse_preview)

        self.mouse_samples_label = QLabel("")
        self.mouse_samples_label.setObjectName("muted")
        layout.addWidget(self.mouse_samples_label)

        clear_button = QPushButton("Limpar amostras deste gesto")
        clear_button.setObjectName("danger")
        clear_button.setCursor(Qt.PointingHandCursor)
        clear_button.clicked.connect(self.clear_mouse_gesture)
        layout.addWidget(clear_button)

        self.refresh_mouse_roles()

        return card

    def build_mouse_settings_card(self):

        card, layout = make_card(
            "Cursor e cliques",
            "Com o modo mouse ligado, o cursor acompanha a posição da "
            "sua mão na câmera."
        )

        cfg = self.mouse_config.settings()

        form = QFormLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        self.mouse_track = QComboBox()
        self.mouse_track.addItem("Palma da mão", 9)
        self.mouse_track.addItem("Ponta do indicador", 8)
        self.mouse_track.setCurrentIndex(
            max(0, self.mouse_track.findData(cfg["track_point"]))
        )
        form.addRow("Cursor segue", self.mouse_track)

        clutch_info = QLabel(
            "O cursor só se movimenta enquanto você mantém o gesto de "
            "embreagem. Ao soltá-lo, a mão pode ser reposicionada sem "
            "mover o cursor, como levantar um mouse para reposicioná-lo."
        )
        clutch_info.setObjectName("muted")
        clutch_info.setWordWrap(True)
        form.addRow("Embreagem", clutch_info)

        self.mouse_gain = QDoubleSpinBox()
        self.mouse_gain.setRange(0.3, 8.0)
        self.mouse_gain.setSingleStep(0.1)
        self.mouse_gain.setSuffix(" ×")
        self.mouse_gain.setValue(float(cfg["gain"]))
        self.mouse_gain.setToolTip(
            "Modo relativo: quanto o cursor anda para cada movimento da "
            "mão. Maior = o cursor corre mais."
        )
        form.addRow("Ganho (relativo)", self.mouse_gain)

        self.mouse_deadzone = QDoubleSpinBox()
        self.mouse_deadzone.setRange(0.0, 15.0)
        self.mouse_deadzone.setSingleStep(0.5)
        self.mouse_deadzone.setSuffix(" px")
        self.mouse_deadzone.setValue(float(cfg["deadzone"]))
        self.mouse_deadzone.setToolTip(
            "Modo relativo: o movimento precisa acumular isto antes de "
            "mexer o cursor. Filtra tremor sem engolir movimento lento."
        )
        form.addRow("Zona morta (relativo)", self.mouse_deadzone)

        self.mouse_mirror = QCheckBox("Espelhar (mão à direita = cursor à direita)")
        self.mouse_mirror.setChecked(cfg["mirror"])
        form.addRow("", self.mouse_mirror)

        self.mouse_smoothing = QSpinBox()
        self.mouse_smoothing.setRange(5, 100)
        self.mouse_smoothing.setSuffix(" %")
        self.mouse_smoothing.setValue(round(cfg["smoothing"] * 100))
        self.mouse_smoothing.setToolTip(
            "Menor = cursor mais suave, porém com mais atraso."
        )
        form.addRow("Velocidade", self.mouse_smoothing)

        self.mouse_margin = QSpinBox()
        self.mouse_margin.setRange(0, 40)
        self.mouse_margin.setSuffix(" %")
        self.mouse_margin.setValue(round(cfg["margin"] * 100))
        self.mouse_margin.setToolTip(
            "Borda da câmera ignorada. Maior = alcança os cantos da tela "
            "movendo menos a mão."
        )
        form.addRow("Margem da câmera", self.mouse_margin)

        self.mouse_scroll = QSpinBox()
        self.mouse_scroll.setRange(20, 2000)
        self.mouse_scroll.setValue(int(cfg["scroll_sensitivity"]))
        form.addRow("Sensib. rolagem", self.mouse_scroll)

        self.mouse_drag = QDoubleSpinBox()
        self.mouse_drag.setRange(0.1, 3.0)
        self.mouse_drag.setSingleStep(0.05)
        self.mouse_drag.setSuffix(" s")
        self.mouse_drag.setValue(float(cfg["drag_after"]))
        self.mouse_drag.setToolTip(
            "Segurar o gesto de clique esquerdo por este tempo inicia "
            "um arraste."
        )
        form.addRow("Arrastar após", self.mouse_drag)

        self.mouse_activation_hold = QDoubleSpinBox()
        self.mouse_activation_hold.setRange(0.3, 3.0)
        self.mouse_activation_hold.setSingleStep(0.1)
        self.mouse_activation_hold.setSuffix(" s")
        self.mouse_activation_hold.setValue(float(cfg["activation_hold"]))
        self.mouse_activation_hold.setToolTip(
            "Quanto tempo manter o gesto de ativação para ligar/desligar "
            "o modo mouse. Maior = menos ativações acidentais."
        )
        form.addRow("Segurar para ativar", self.mouse_activation_hold)

        self.mouse_confidence = QSpinBox()
        self.mouse_confidence.setRange(10, 100)
        self.mouse_confidence.setSuffix(" %")
        self.mouse_confidence.setValue(round(cfg["min_confidence"] * 100))
        self.mouse_confidence.setToolTip(
            "Confiança mínima para aceitar um gesto do mouse."
        )
        form.addRow("Confiança mínima", self.mouse_confidence)

        layout.addLayout(form)

        save_button = QPushButton("Salvar configuração")
        save_button.setObjectName("primary")
        save_button.setCursor(Qt.PointingHandCursor)
        save_button.clicked.connect(self.save_mouse_configuration)
        layout.addWidget(save_button)

        # Só conecta os sinais depois de preencher os valores.
        for signal in (
            self.mouse_activation_hold.valueChanged,
            self.mouse_track.currentIndexChanged,
            self.mouse_gain.valueChanged,
            self.mouse_deadzone.valueChanged,
            self.mouse_mirror.toggled,
            self.mouse_smoothing.valueChanged,
            self.mouse_margin.valueChanged,
            self.mouse_scroll.valueChanged,
            self.mouse_drag.valueChanged,
            self.mouse_confidence.valueChanged,
        ):
            signal.connect(self.save_mouse_settings)

        return card

    def refresh_mouse_roles(self):
        """Atualiza a lista dos 4 botões com a contagem de amostras."""

        current = self.mouse_role_combo.currentData()

        self.mouse_role_combo.blockSignals(True)
        self.mouse_role_combo.clear()

        for key, label in MOUSE_ACTIVATION.items():
            total = len(self.mouse_config.get(key).get("samples", []))
            self.mouse_role_combo.addItem(
                f"{label}  ·  {total} amostras",
                key
            )

        self.mouse_role_combo.insertSeparator(self.mouse_role_combo.count())

        for key, label in MOUSE_ROLES.items():
            total = len(self.mouse_config.get(key).get("samples", []))
            self.mouse_role_combo.addItem(
                f"{label}  ·  {total} amostras",
                key
            )

        index = self.mouse_role_combo.findData(current) if current else 0
        self.mouse_role_combo.setCurrentIndex(max(0, index))
        self.mouse_role_combo.blockSignals(False)

        self.load_mouse_role()

    def on_mouse_role_changed(self, _index):
        self.load_mouse_role()

    def load_mouse_role(self):

        role = self.mouse_role_combo.currentData()

        if not role:
            return

        samples = self.mouse_config.get(role).get("samples", [])

        self.mouse_preview.set_sample(samples[-1] if samples else None)

        if role in MOUSE_ACTIVATION:
            what = "gesto de ativação"
        else:
            what = "gesto deste botão"

        if samples:
            self.mouse_samples_label.setText(
                f"{len(samples)} amostras gravadas para o {what}."
            )
        else:
            self.mouse_samples_label.setText(
                f"Nenhuma amostra ainda. Grave o {what}."
            )

    def clear_mouse_gesture(self):

        role = self.mouse_role_combo.currentData()

        if not role or self.is_capturing:
            return

        self.mouse_config.clear(role)
        self.refresh_mouse_roles()

        self.set_status(
            f"Amostras de «{self.mouse_label(role)}» removidas.",
            "warn"
        )

    @staticmethod
    def mouse_label(key):
        return (
            MOUSE_ACTIVATION.get(key)
            or MOUSE_ROLES.get(key, key)
        )

    def on_tab_changed(self, index):

        if index == 1:
            self.capture_button.setText(
                "Capturar amostra do gesto do mouse"
            )
        else:
            self.capture_button.setText(
                "Capturar amostra do gesto atual"
            )

    def save_mouse_configuration(self):
        self.save_mouse_settings()
        self.set_status("Configuração do mouse salva.", "ok")

    def save_mouse_settings(self, *_):

        cfg = self.mouse_config.settings()

        cfg["track_point"] = self.mouse_track.currentData()
        cfg["move_mode"] = "relative"
        cfg["gain"] = self.mouse_gain.value()
        cfg["deadzone"] = self.mouse_deadzone.value()
        cfg["mirror"] = self.mouse_mirror.isChecked()
        cfg["smoothing"] = self.mouse_smoothing.value() / 100
        cfg["margin"] = self.mouse_margin.value() / 100
        cfg["scroll_sensitivity"] = self.mouse_scroll.value()
        cfg["drag_after"] = self.mouse_drag.value()
        cfg["activation_hold"] = self.mouse_activation_hold.value()
        cfg["min_confidence"] = self.mouse_confidence.value() / 100

        self.mouse_config.save_settings(cfg)
        self.mouse_mode.reload()

        self.mouse_cfg = self.mouse_config.settings()
        self.activation.hold = self.mouse_cfg["activation_hold"]

        # Trocar de modo de movimento: recomeça a embreagem do zero.
        self.mouse_mode.rel_s = None

    # -----------------------------------------------------
    # Modo mouse (ligado pelo gesto de ativação)
    # -----------------------------------------------------

    def set_mouse_active(self, active):

        self.mouse_mode.set_active(active)
        self.last_mouse_role = None

        # Ao trocar de modo, nenhum gesto "antigo" continua valendo.
        self.controller.active_gesture = None
        self.controller.last_execution.clear()

        self.update_mode_badge()

        if active:
            self.set_status(
                "Modo mouse LIGADO — gestos do teclado pausados. "
                "Segure o gesto de ativação de novo para voltar.",
                "ok"
            )
        else:
            self.set_status(
                "Modo mouse DESLIGADO — gestos do teclado ativos.",
                "warn"
            )

    def update_mode_badge(self):

        if self.mouse_mode.active:
            text, kind = "Modo mouse: LIGADO", "ok"

        elif not self.mouse_config.activation_ready():
            text, kind = (
                "Modo teclado  ·  grave o gesto de ativação "
                "na aba Mouse", "info"
            )

        elif self.activation.progress:
            text, kind = (
                f"Segure o gesto… {self.activation.progress:.0%}", "warn"
            )

        else:
            text, kind = "Modo teclado", "info"

        if (
            self.mode_badge.text() == text
            and self.mode_badge.property("kind") == kind
        ):
            return

        self.mode_badge.setText(text)
        self.mode_badge.setProperty("kind", kind)
        self.mode_badge.style().unpolish(self.mode_badge)
        self.mode_badge.style().polish(self.mode_badge)

    def update_mouse(self, role):

        try:
            active = self.mouse_mode.process(
                role,
                self.recognizer.last_points
            )
        except Exception as exc:
            self.set_status(f"Erro no mouse: {exc}", "error")
            return

        if active != self.last_mouse_role:
            self.last_mouse_role = active

            if active:
                self.set_status(f"Mouse: {MOUSE_ROLES[active]}", "ok")

        # Mantém o selo em dia (progresso do gesto de ativação).
        self.update_mode_badge()

    # =====================================================
    # FECHAR
    # =====================================================

    def closeEvent(self, event):

        self.timer.stop()
        self.mouse_mode.release()

        self.camera.release()
        self.recognizer.close()
        event.accept()