import pygame
import random
from typing import Tuple


class ScreenShake:
    def __init__(self) -> None:
        self.duration: int = 0
        self.intensity: int = 0

    def trigger(self, duration: int = 300, intensity: int = 8) -> None:
        self.duration = duration
        self.intensity = intensity

    def update(self, dt: int) -> Tuple[int, int]:
        if self.duration > 0:
            self.duration -= dt
            ox = random.randint(-self.intensity, self.intensity)
            oy = random.randint(-self.intensity, self.intensity)
            return ox, oy
        return 0, 0


class FlashOverlay:
    def __init__(self) -> None:
        self.duration: int = 0
        self.color: Tuple[int, int, int] = (255, 255, 255)
        self.max_duration: int = 1

    def trigger(
        self,
        color: Tuple[int, int, int] = (255, 255, 255),
        duration: int = 200,
    ) -> None:
        self.color = color
        self.duration = duration
        self.max_duration = duration

    def update(self, dt: int, surface: pygame.Surface) -> None:
        if self.duration > 0:
            self.duration -= dt
            alpha = int(180 * (self.duration / self.max_duration))
            overlay = pygame.Surface(surface.get_size())
            overlay.fill(self.color)
            overlay.set_alpha(alpha)
            surface.blit(overlay, (0, 0))
