import numpy as np
import pygame


def _generate(
    frequency: float,
    duration_ms: int,
    volume: float = 0.3,
    wave: str = "sine",
    decay: bool = True,
) -> pygame.mixer.Sound:
    sample_rate = 44100
    samples = int(sample_rate * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, samples, False)

    if wave == "sine":
        data = np.sin(2 * np.pi * frequency * t)
    elif wave == "square":
        data = np.sign(np.sin(2 * np.pi * frequency * t))
    elif wave == "noise":
        data = np.random.uniform(-1, 1, samples)
    else:
        data = np.sin(2 * np.pi * frequency * t)

    if decay:
        envelope = np.linspace(1.0, 0.0, samples)
        data = data * envelope

    data = (data * volume * 32767).astype(np.int16)
    stereo = np.column_stack((data, data))
    return pygame.sndarray.make_sound(stereo)


class SoundEngine:
    def __init__(self):
        self.enabled = True
        self._sounds: dict = {}

    def init(self):
        """Call after pygame.init()"""
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self._sounds = {
            "select": _generate(440, 80, 0.2, "sine", decay=True),
            "win": _generate(660, 300, 0.3, "sine", decay=True),
            "lose": _generate(220, 400, 0.3, "sine", decay=True),
            "hit": _generate(180, 200, 0.4, "square", decay=True),
            "miss": _generate(300, 150, 0.2, "sine", decay=True),
            "combo": _generate(880, 200, 0.35, "sine", decay=False),
            "timeout": _generate(150, 300, 0.4, "square", decay=True),
            "draw": _generate(350, 200, 0.2, "sine", decay=True),
            "game_over": _generate(110, 600, 0.4, "square", decay=True),
        }

    def play(self, name: str):
        if not self.enabled or not self._sounds:
            return
        sound = self._sounds.get(name)
        if sound:
            sound.play()

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled
