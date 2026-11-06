"""
Gesto de ativação do modo mouse.

Um único gesto (ex.: o "chifre" 🤘) liga e desliga o modo mouse. Para não
disparar por acidente, a pose precisa ser MANTIDA por `hold` segundos.
Depois de acionar, é preciso desfazer a pose antes de poder acionar de novo
(evita ligar e desligar sem parar enquanto a mão continua no chifre).

Uso (a cada frame):
    if gesture.update(gesto_visto_neste_frame):   # True/False
        ...alterna o modo mouse...
"""
import time


class ActivationGesture:

    # Frames sem a pose tolerados antes de zerar a contagem (ruído da câmera).
    MISS_TOLERANCE = 3

    def __init__(self, hold=1.0, cooldown=0.8):
        self.hold = hold              # segundos segurando a pose
        self.cooldown = cooldown      # pausa depois de acionar

        self.since = None             # quando a pose começou
        self.fired = False            # já acionou nesta "segurada"
        self.misses = 0
        self.locked_until = 0.0

    @property
    def progress(self):
        """0.0 a 1.0: quanto da pose já foi mantido (0 = parado)."""
        if self.since is None or self.fired or self.hold <= 0:
            return 0.0
        return min(1.0, (self._now - self.since) / self.hold)

    _now = 0.0

    def reset(self):
        self.since = None
        self.fired = False
        self.misses = 0

    def update(self, seen, now=None):
        """seen: True se a pose de ativação foi reconhecida neste frame."""
        now = time.monotonic() if now is None else now
        self._now = now

        if now < self.locked_until:
            return False

        if not seen:
            self.misses += 1
            if self.misses >= self.MISS_TOLERANCE:
                self.reset()
            return False

        self.misses = 0

        if self.since is None:
            self.since = now
            return False

        if not self.fired and now - self.since >= self.hold:
            self.fired = True
            self.locked_until = now + self.cooldown
            return True

        return False
