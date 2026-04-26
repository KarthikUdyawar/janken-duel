import pygame
import sys
from game.state_manager import StateManager, State

pygame.init()

SCREEN_W, SCREEN_H = 800, 600
FPS = 60

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Janken Duel")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 48)

sm = StateManager()


def draw_text(text, y, color=(255, 255, 255)):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(SCREEN_W // 2, y))
    screen.blit(surf, rect)


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if sm.is_state(State.MENU) and event.key == pygame.K_RETURN:
                sm.transition(State.JANKEN_INPUT)

    screen.fill((20, 20, 30))

    if sm.is_state(State.MENU):
        draw_text("JANKEN DUEL", 250)
        draw_text("Press ENTER to start", 320, (180, 180, 180))
    elif sm.is_state(State.JANKEN_INPUT):
        draw_text("Choose: 1=Rock  2=Paper  3=Scissors", 300)
    else:
        draw_text(f"State: {sm.current.name}", 300, (100, 200, 255))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
