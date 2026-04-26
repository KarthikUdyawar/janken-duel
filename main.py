import pygame
import sys
from game.state_manager import StateManager, State
from game.janken import KEY_MAP, ai_move, resolve

pygame.init()

SCREEN_W, SCREEN_H = 800, 600
FPS = 60

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Janken Duel")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 48)
font_sm = pygame.font.SysFont(None, 32)

sm = StateManager()

# Janken state
player_move = None
ai_move_choice = None
outcome = None
result_timer = 0
RESULT_DISPLAY_MS = 1500


def draw_text(text, y, color=(255, 255, 255), f=None):
    f = f or font
    surf = f.render(text, True, color)
    rect = surf.get_rect(center=(SCREEN_W // 2, y))
    screen.blit(surf, rect)


OUTCOME_COLOR = {
    "WIN": (100, 255, 100),
    "LOSE": (255, 100, 100),
    "DRAW": (255, 220, 50),
}

running = True
while running:
    dt = clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if sm.is_state(State.MENU) and event.key == pygame.K_RETURN:
                sm.transition(State.JANKEN_INPUT)

            elif sm.is_state(State.JANKEN_INPUT):
                key = pygame.key.name(event.key)
                if key in KEY_MAP:
                    player_move = KEY_MAP[key]
                    ai_move_choice = ai_move()
                    outcome = resolve(player_move, ai_move_choice)
                    result_timer = RESULT_DISPLAY_MS
                    sm.transition(State.JANKEN_RESULT)

    # Auto-advance from result
    if sm.is_state(State.JANKEN_RESULT):
        result_timer -= dt
        if result_timer <= 0:
            sm.transition(State.JANKEN_INPUT)  # loop back for now

    # --- Draw ---
    screen.fill((20, 20, 30))

    if sm.is_state(State.MENU):
        draw_text("JANKEN DUEL", 250)
        draw_text("Press ENTER to start", 320, (180, 180, 180), font_sm)

    elif sm.is_state(State.JANKEN_INPUT):
        draw_text("Make your move!", 200)
        draw_text(
            "1 = Rock    2 = Paper    3 = Scissors", 300, (180, 180, 180), font_sm
        )

    elif sm.is_state(State.JANKEN_RESULT):
        if player_move and ai_move_choice and outcome:
            draw_text(f"You: {player_move.value}", 180, (200, 200, 255))
            draw_text(f"AI:  {ai_move_choice.value}", 240, (255, 180, 180))
            color = OUTCOME_COLOR.get(outcome, (255, 255, 255))
            draw_text(outcome, 330, color)

    pygame.display.flip()

pygame.quit()
sys.exit()
