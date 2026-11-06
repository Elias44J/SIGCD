from pathlib import Path
import urllib.request

import cv2
import mediapipe as mp
import numpy as np


MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)


class GestureRecognizer:

    # Distância máxima para considerar que a mão "é" um gesto cadastrado.
    MATCH_THRESHOLD = 0.32

    def __init__(self, model_path=None):

        if model_path is None:
            model_path = (
                Path(__file__).resolve().parents[1]
                / "config"
                / "hand_landmarker.task"
            )

        self.model_path = Path(model_path)

        # Landmarks brutos (x, y na imagem) do último frame; usados pelo
        # mouse por gestos para saber ONDE a mão está.
        self.last_points = None

        self.model_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not self.model_path.exists():
            print("Modelo do MediaPipe não encontrado.")
            print("Baixando modelo...")

            urllib.request.urlretrieve(
                MODEL_URL,
                self.model_path
            )

            print("Modelo baixado.")

        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=str(self.model_path)
            ),

            running_mode=mp.tasks.vision.RunningMode.IMAGE,

            num_hands=1,

            min_hand_detection_confidence=0.5,

            min_hand_presence_confidence=0.5,

            min_tracking_confidence=0.5,
        )

        self.landmarker = (
            mp.tasks.vision.HandLandmarker.create_from_options(
                options
            )
        )

    @staticmethod
    def normalize_landmarks(hand_landmarks):
        """
        Converte os 21 landmarks para uma representação
        independente da posição da mão na imagem.
        """

        points = np.array(
            [
                [
                    landmark.x,
                    landmark.y,
                    landmark.z
                ]
                for landmark in hand_landmarks
            ],
            dtype=np.float32
        )

        # O pulso vira a origem.
        wrist = points[0].copy()

        points -= wrist

        # Normaliza o tamanho da mão.
        distances = np.linalg.norm(
            points[:, :2],
            axis=1
        )

        scale = np.max(distances)

        if scale < 1e-6:
            return None

        points /= scale

        return points.flatten().tolist()

    def extract(self, frame):
        """
        Retorna os landmarks normalizados da mão.

        Retorno:
            list | None
        """

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        result = self.landmarker.detect(image)

        if not result.hand_landmarks:
            self.last_points = None
            return None

        self.last_points = [
            (landmark.x, landmark.y)
            for landmark in result.hand_landmarks[0]
        ]

        return self.normalize_landmarks(
            result.hand_landmarks[0]
        )

    @staticmethod
    def distance(sample_a, sample_b):
        a = np.asarray(
            sample_a,
            dtype=np.float32
        )

        b = np.asarray(
            sample_b,
            dtype=np.float32
        )

        return float(
            np.linalg.norm(a - b)
            / np.sqrt(len(a))
        )

    def best_match(self, sample, gestures):
        """
        Gesto mais parecido com a amostra, entre os cadastrados.

        Retorna (gesture_id, distância); (None, inf) se não houver amostras.
        """

        best_gesture = None
        best_distance = float("inf")

        if sample is None or not gestures:
            return best_gesture, best_distance

        for gesture_id, gesture in gestures.items():

            for saved_sample in gesture.get("samples", []):

                if len(saved_sample) != len(sample):
                    continue

                distance = self.distance(sample, saved_sample)

                if distance < best_distance:
                    best_distance = distance
                    best_gesture = gesture_id

        return best_gesture, best_distance

    def recognize(
        self,
        frame,
        gestures,
        threshold=0.32
    ):
        """
        Compara a mão atual com todas as amostras cadastradas.

        Retorna:

            gesture_id
            confidence
            current_sample
        """

        current_sample = self.extract(frame)

        if current_sample is None:
            return None, 0.0, None

        if not gestures:
            return None, 0.0, current_sample

        best_gesture = None
        best_distance = float("inf")

        for gesture_id, gesture in gestures.items():

            samples = gesture.get(
                "samples",
                []
            )

            for saved_sample in samples:

                if len(saved_sample) != len(current_sample):
                    continue

                distance = self.distance(
                    current_sample,
                    saved_sample
                )

                if distance < best_distance:
                    best_distance = distance
                    best_gesture = gesture_id

        if best_gesture is None:
            return None, 0.0, current_sample

        confidence = 1.0 - (
            best_distance / threshold
        )

        confidence = max(
            0.0,
            min(1.0, confidence)
        )

        if best_distance > threshold:
            return (
                None,
                confidence,
                current_sample
            )

        return (
            best_gesture,
            confidence,
            current_sample
        )

    def close(self):
        self.landmarker.close()