import pygame
import sys
from game.state_manager import StateManager, State
from game.janken import KEY_MAP as JANKEN_KEYS, ai_move, resolve as janken_resolve
from game.pointing import KEY_MAP as DIR_KEYS, ai_direction, resolve as point_resolve
from game.effects import ScreenShake, FlashOverlay

pygame.init()

SCREEN_W, SCREEN_H = 800, 600
FPS = 60

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Janken Duel")
clock = pygame.time.Clock()
font = pygame.font.SysFont("dejavusans", 48)
font_sm = pygame.font.SysFont("dejavusans", 32)
font_lg = pygame.font.SysFont("dejavusans", 72)

shake = ScreenShake()
flash = FlashOverlay()

MAX_HP = 5


def make_state():
    return {
        "sm": StateManager(),
        "player_move": None,
        "ai_move_choice": None,
        "janken_outcome": None,
        "attacker": None,
        "player_dir": None,
        "ai_dir": None,
        "point_hit": None,
        "player_hp": MAX_HP,
        "ai_hp": MAX_HP,
        "result_timer": 0,
        "winner": None,
    }


g = make_state()

RESULT_MS = 1500
OUTCOME_COLOR = {
    "WIN": (100, 255, 100),
    "LOSE": (255, 100, 100),
    "DRAW": (255, 220, 50),
}

running = True
while running:
    dt = clock.tick(FPS)
    sm = g["sm"]

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if sm.is_state(State.MENU) and event.key == pygame.K_RETURN:
                sm.transition(State.JANKEN_INPUT)

            elif sm.is_state(State.JANKEN_INPUT):
                key = pygame.key.name(event.key)
                if key in JANKEN_KEYS:
                    g["player_move"] = JANKEN_KEYS[key]
                    g["ai_move_choice"] = ai_move()
                    g["janken_outcome"] = janken_resolve(
                        g["player_move"], g["ai_move_choice"]
                    )
                    g["result_timer"] = RESULT_MS
                    sm.transition(State.JANKEN_RESULT)

            elif sm.is_state(State.POINT_INPUT):
                key = pygame.key.name(event.key)
                if key in DIR_KEYS:
                    player_dir = DIR_KEYS[key]
                    ai_dir = ai_direction()
                    g["player_dir"] = player_dir
                    g["ai_dir"] = ai_dir
                    attacker = g["attacker"]
                    g["point_hit"] = point_resolve(
                        player_dir if attacker == "player" else ai_dir,
                        ai_dir if attacker == "player" else player_dir,
                    )
                    g["result_timer"] = RESULT_MS
                    sm.transition(State.POINT_RESULT)

            elif sm.is_state(State.GAME_OVER):
                if event.key == pygame.K_r:
                    g = make_state()
                    shake = ScreenShake()
                    flash = FlashOverlay()
                    continue

    # Auto-advance
    if sm.is_state(State.JANKEN_RESULT):
        g["result_timer"] -= dt
        if g["result_timer"] <= 0:
            if g["janken_outcome"] == "DRAW":
                sm.transition(State.JANKEN_INPUT)
            else:
                g["attacker"] = "player" if g["janken_outcome"] == "WIN" else "ai"
                sm.transition(State.POINT_INPUT)

    if sm.is_state(State.POINT_RESULT):
        g["result_timer"] -= dt
        if g["result_timer"] <= 0:
            # Apply damage
            if g["point_hit"]:
                if g["attacker"] == "player":
                    g["ai_hp"] = max(0, g["ai_hp"] - 1)
                    flash.trigger((255, 80, 80), 250)  # red — AI hit
                    shake.trigger(200, 6)
                else:
                    g["player_hp"] = max(0, g["player_hp"] - 1)
                    flash.trigger((80, 80, 255), 250)  # blue — player hit
                    shake.trigger(300, 10)
            if g["player_hp"] <= 0 or g["ai_hp"] <= 0:
                g["winner"] = "player" if g["ai_hp"] <= 0 else "ai"
                sm.transition(State.GAME_OVER)
            else:
                sm.transition(State.JANKEN_INPUT)

    # --- Draw ---
    ox, oy = shake.update(dt)
    render_surface = pygame.Surface((SCREEN_W, SCREEN_H))
    render_surface.fill((20, 20, 30))

    # draw to render_surface via temp redirect
    _blit = screen.blit

    def draw_text(text, y, color=(255, 255, 255), f=None):
        f = f or font
        surf = f.render(text, True, color)
        rect = surf.get_rect(center=(SCREEN_W // 2, y))
        render_surface.blit(surf, rect)

    def draw_hp():
        ai_label = font_sm.render(
            f"AI HP:  {'[ ]' * g['ai_hp']}{'[X]' * (MAX_HP - g['ai_hp'])}",
            True,
            (255, 120, 120),
        )
        render_surface.blit(ai_label, (20, 20))
        pl_label = font_sm.render(
            f"YOU HP: {'[ ]' * g['player_hp']}{'[X]' * (MAX_HP - g['player_hp'])}",
            True,
            (120, 200, 255),
        )
        render_surface.blit(pl_label, (20, SCREEN_H - 40))

    draw_hp()

    if sm.is_state(State.MENU):
        draw_text("JANKEN DUEL", 250)
        draw_text("Press ENTER to start", 320, (180, 180, 180), font_sm)

    elif sm.is_state(State.JANKEN_INPUT):
        draw_text("Make your move!", 220)
        draw_text(
            "1 = Rock    2 = Paper    3 = Scissors", 300, (180, 180, 180), font_sm
        )

    elif sm.is_state(State.JANKEN_RESULT):
        if g["player_move"] and g["ai_move_choice"] and g["janken_outcome"]:
            draw_text(f"You: {g['player_move'].value}", 180, (200, 200, 255))
            draw_text(f"AI:  {g['ai_move_choice'].value}", 240, (255, 180, 180))
            color = OUTCOME_COLOR.get(g["janken_outcome"], (255, 255, 255))
            draw_text(g["janken_outcome"], 320, color)
            if g["janken_outcome"] != "DRAW":
                who = "You attack!" if g["janken_outcome"] == "WIN" else "AI attacks!"
                draw_text(who, 380, (220, 220, 100), font_sm)

    elif sm.is_state(State.POINT_INPUT):
        who = (
            "YOU point — pick direction!"
            if g["attacker"] == "player"
            else "AI points — dodge!"
        )
        draw_text(who, 220)
        draw_text("Arrow keys to choose", 300, (180, 180, 180), font_sm)

    elif sm.is_state(State.POINT_RESULT):
        if g["player_dir"] and g["ai_dir"]:
            draw_text(f"You: {g['player_dir'].value}   AI: {g['ai_dir'].value}", 240)
            if g["point_hit"]:
                color = (255, 80, 80) if g["attacker"] == "player" else (80, 255, 80)
                draw_text("HIT!", 320, color)
            else:
                draw_text("MISS!", 320, (180, 180, 180))

    elif sm.is_state(State.GAME_OVER):
        if g["winner"] == "player":
            draw_text("YOU WIN!", 240, (100, 255, 100), font_lg)
        else:
            draw_text("YOU LOSE!", 240, (255, 80, 80), font_lg)
        draw_text("Press R to play again", 340, (180, 180, 180), font_sm)

    flash.update(dt, render_surface)
    screen.blit(render_surface, (ox, oy))
    pygame.display.flip()

pygame.quit()
sys.exit()
