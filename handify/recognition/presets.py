"""
Gestos prontos.

Usa o reconhecedor de gestos do Google (gesture_recognizer.task) só como
"conferente": você faz a pose, ele confirma que é mesmo aquela pose e o app
grava as amostras de landmarks no mesmo formato dos gestos gravados à mão.
Depois disso o reconhecimento do dia a dia continua sendo o do Handify.

O modelo é carregado só quando alguém pede gestos prontos, para não pesar
na abertura do app.
"""
from pathlib import Path
import urllib.request

import cv2
import mediapipe as mp

from handify.recognition.gesture_recognizer import GestureRecognizer


MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task"
)

# Poses que o modelo do Google conhece -> nome em português.
CANNED = {
    "Closed_Fist": "Punho",
    "Open_Palm": "Palma aberta",
    "Pointing_Up": "Indicador para cima",
    "Victory": "Sinal de paz (V)",
    "Thumb_Up": "Joinha para cima",
    "Thumb_Down": "Joinha para baixo",
    "ILoveYou": "Polegar + indicador + mindinho",
}

# Sugestão completa: função do Handify -> pose do Google.
# (O clique do meio fica sem sugestão: não sobra pose pronta distinta.)
SUGGESTION = [
    ("activation", "ILoveYou"),
    ("emergency", "Thumb_Down"),
    ("clutch", "Closed_Fist"),
    ("left_click", "Pointing_Up"),
    ("right_click", "Victory"),
    ("scroll", "Thumb_Up"),
]

SUGGESTED_POSE = dict(SUGGESTION)

# Confiança mínima do Google para aceitar uma amostra.
MIN_SCORE = 0.70


class PresetRecognizer:

    def __init__(self, model_path=None):

        if model_path is None:
            model_path = (
                Path(__file__).resolve().parents[1]
                / "config"
                / "gesture_recognizer.task"
            )

        self.model_path = Path(model_path)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.model_path.exists():
            urllib.request.urlretrieve(MODEL_URL, self.model_path)

        options = mp.tasks.vision.GestureRecognizerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=str(self.model_path)
            ),
            running_mode=mp.tasks.vision.RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.recognizer = (
            mp.tasks.vision.GestureRecognizer.create_from_options(options)
        )

    def classify(self, frame):
        """
        Retorna (pose_do_google, confiança, amostra_normalizada).
        (None, 0.0, None) se não há mão ou pose reconhecida.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        result = self.recognizer.recognize(image)

        if not result.gestures or not result.hand_landmarks:
            return None, 0.0, None

        top = result.gestures[0][0]

        sample = GestureRecognizer.normalize_landmarks(
            result.hand_landmarks[0]
        )

        return top.category_name, float(top.score), sample

    def close(self):
        self.recognizer.close()
