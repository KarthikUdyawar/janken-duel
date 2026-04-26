import pygame
import random


class ScreenShake:
    def __init__(self):
        self.duration = 0
        self.intensity = 0

    def trigger(self, duration=300, intensity=8):
        self.duration = duration
        self.intensity = intensity

    def update(self, dt) -> tuple[int, int]:
        if self.duration > 0:
            self.duration -= dt
            ox = random.randint(-self.intensity, self.intensity)
            oy = random.randint(-self.intensity, self.intensity)
            return ox, oy
        return 0, 0


class FlashOverlay:
    def __init__(self):
        self.duration = 0
        self.color = (255, 255, 255)
        self.max_duration = 1

    def trigger(self, color=(255, 255, 255), duration=200):
        self.color = color
        self.duration = duration
        self.max_duration = duration

    def update(self, dt, surface: pygame.Surface):
        if self.duration > 0:
            self.duration -= dt
            alpha = int(180 * (self.duration / self.max_duration))
            overlay = pygame.Surface(surface.get_size())
            overlay.fill(self.color)
            overlay.set_alpha(alpha)
            surface.blit(overlay, (0, 0))
