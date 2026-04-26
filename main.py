import pygame
import sys
from game.state_manager import StateManager, State
from game.janken import KEY_MAP as JANKEN_KEYS, resolve as janken_resolve
from game.pointing import KEY_MAP as DIR_KEYS, resolve as point_resolve
from game.effects import ScreenShake, FlashOverlay
from game.ai import AI
from game.score import ScoreTracker
from game.combo import ComboTracker
from game.taunts import TauntEngine
from game.speed import SpeedManager

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
score = ScoreTracker()
taunt = TauntEngine()

MAX_HP = 5
DIFFICULTIES = ["easy", "medium", "hard"]
DIFF_COLORS = {
    "easy": (100, 255, 100),
    "medium": (255, 220, 50),
    "hard": (255, 80, 80),
}

selected_diff_idx = 1  # default medium


def make_state(difficulty="medium"):
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
        "ai": AI(difficulty),
        "difficulty": difficulty,
        "combo": ComboTracker(),
        "speed": SpeedManager(),
        "point_timer": 0,
        "janken_timer": 0,
        "janken_timed_out": False,
        "timed_out": False,
    }


g = make_state()


def reset_game(difficulty=None):
    global g, shake, flash
    diff = difficulty or DIFFICULTIES[selected_diff_idx]
    g = make_state(diff)
    shake = ScreenShake()
    flash = FlashOverlay()
    taunt.current_taunt = "..."


# ── Draw helpers ────────────────────────────────────────────────────────────


def draw_text(surface, text, y, color=(255, 255, 255), f=None):
    f = f or font
    surf = f.render(text, True, color)
    rect = surf.get_rect(center=(SCREEN_W // 2, y))
    surface.blit(surf, rect)


def draw_hp(surface):
    ai_label = font_sm.render(
        f"AI HP:  {'[ ]' * g['ai_hp']}{'[X]' * (MAX_HP - g['ai_hp'])}",
        True,
        (255, 120, 120),
    )
    surface.blit(ai_label, (20, 20))
    pl_label = font_sm.render(
        f"YOU HP: {'[ ]' * g['player_hp']}{'[X]' * (MAX_HP - g['player_hp'])}",
        True,
        (120, 200, 255),
    )
    surface.blit(pl_label, (20, SCREEN_H - 40))


def draw_score(surface):
    txt = font_sm.render(
        f"W: {score.wins}  L: {score.losses}  ({score.win_rate()})",
        True,
        (160, 160, 160),
    )
    surface.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, SCREEN_H - 75))


def draw_difficulty_label(surface):
    diff = g["difficulty"].upper()
    color = DIFF_COLORS[g["difficulty"]]
    surf = font_sm.render(f"[ {diff} ]", True, color)
    surface.blit(surf, (SCREEN_W - surf.get_width() - 20, 20))


def draw_combo(surface):
    count = g["combo"].count
    if count >= 2:
        label = f"COMBO x{count}!"
        if count >= 6:
            color = (255, 50, 50)
        elif count >= 3:
            color = (255, 180, 0)
        else:
            color = (255, 255, 100)
        draw_text(surface, label, 140, color, font_sm)


def draw_taunt(surface):
    txt = taunt.get()
    if txt:
        surf = font_sm.render(f'AI: "{txt}"', True, (220, 180, 255))
        surface.blit(surf, surf.get_rect(center=(SCREEN_W // 2, 80)))


def draw_speed_bar(surface, sm):
    if not sm.is_state(State.POINT_INPUT):
        return
    window = g["speed"].point_window()
    remaining = max(0, g["point_timer"])
    ratio = remaining / window
    bar_w, bar_h = 400, 16
    x = SCREEN_W // 2 - bar_w // 2
    y = 160
    pygame.draw.rect(surface, (60, 60, 60), (x, y, bar_w, bar_h), border_radius=8)
    if ratio > 0.5:
        color = (100, 255, 100)
    elif ratio > 0.25:
        color = (255, 220, 50)
    else:
        color = (255, 60, 60)
    pygame.draw.rect(surface, color, (x, y, int(bar_w * ratio), bar_h), border_radius=8)
    round_txt = font_sm.render(f"Round {g['speed'].round + 1}", True, (140, 140, 140))
    surface.blit(round_txt, (SCREEN_W - round_txt.get_width() - 20, SCREEN_H // 2 - 20))


def draw_janken_bar(surface, sm):
    if not sm.is_state(State.JANKEN_INPUT):
        return
    window = g["speed"].janken_window()
    remaining = max(0, g["janken_timer"])
    ratio = remaining / window
    bar_w, bar_h = 400, 16
    x = SCREEN_W // 2 - bar_w // 2
    y = 160
    pygame.draw.rect(surface, (60, 60, 60), (x, y, bar_w, bar_h), border_radius=8)
    if ratio > 0.5:
        color = (100, 255, 100)
    elif ratio > 0.25:
        color = (255, 220, 50)
    else:
        color = (255, 60, 60)
    pygame.draw.rect(surface, color, (x, y, int(bar_w * ratio), bar_h), border_radius=8)


# ── Constants ────────────────────────────────────────────────────────────────

OUTCOME_COLOR = {
    "WIN": (100, 255, 100),
    "LOSE": (255, 100, 100),
    "DRAW": (255, 220, 50),
}

# ── Main loop ────────────────────────────────────────────────────────────────

running = True
while running:
    dt = clock.tick(FPS)
    sm = g["sm"]

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            # MENU
            if sm.is_state(State.MENU):
                if event.key == pygame.K_RETURN:
                    g["janken_timer"] = g["speed"].janken_window()
                    g["janken_timed_out"] = False
                    sm.transition(State.JANKEN_INPUT)
                elif event.key == pygame.K_LEFT:
                    selected_diff_idx = (selected_diff_idx - 1) % 3
                    reset_game(DIFFICULTIES[selected_diff_idx])
                    g["sm"].transition(State.MENU)
                elif event.key == pygame.K_RIGHT:
                    selected_diff_idx = (selected_diff_idx + 1) % 3
                    reset_game(DIFFICULTIES[selected_diff_idx])
                    g["sm"].transition(State.MENU)
                elif event.key == pygame.K_t:
                    enabled = taunt.toggle()
                    taunt.current_taunt = "Ollama ON" if enabled else "Offline mode"

            # JANKEN INPUT
            elif sm.is_state(State.JANKEN_INPUT):
                key = pygame.key.name(event.key)
                if key == "t":
                    enabled = taunt.toggle()
                    taunt.current_taunt = "Ollama ON" if enabled else "Offline mode"
                elif key in JANKEN_KEYS:
                    g["player_move"] = JANKEN_KEYS[key]
                    g["ai_move_choice"] = g["ai"].pick_move()
                    g["ai"].record_player_move(g["player_move"])
                    g["janken_outcome"] = janken_resolve(
                        g["player_move"], g["ai_move_choice"]
                    )
                    g["result_timer"] = g["speed"].result_delay()
                    sm.transition(State.JANKEN_RESULT)

            # POINT INPUT
            elif sm.is_state(State.POINT_INPUT):
                key = pygame.key.name(event.key)
                if key in DIR_KEYS:
                    player_dir = DIR_KEYS[key]
                    ai_dir = g["ai"].pick_direction()
                    g["ai"].record_player_dir(player_dir)
                    g["player_dir"] = player_dir
                    g["ai_dir"] = ai_dir
                    attacker = g["attacker"]
                    g["point_hit"] = point_resolve(
                        player_dir if attacker == "player" else ai_dir,
                        ai_dir if attacker == "player" else player_dir,
                    )
                    g["timed_out"] = False
                    g["result_timer"] = g["speed"].result_delay()
                    sm.transition(State.POINT_RESULT)

            # GAME OVER
            elif sm.is_state(State.GAME_OVER):
                if event.key == pygame.K_r:
                    reset_game()
                elif event.key == pygame.K_m:
                    reset_game()
                    g["sm"].transition(State.MENU)

    # ── Auto-advance ─────────────────────────────────────────────────────────

    if sm.is_state(State.JANKEN_RESULT):
        g["result_timer"] -= dt
        if g["result_timer"] <= 0:
            if g["janken_outcome"] == "DRAW":
                g["janken_timer"] = g["speed"].janken_window()
                g["janken_timed_out"] = False
                sm.transition(State.JANKEN_INPUT)
            else:
                g["attacker"] = "player" if g["janken_outcome"] == "WIN" else "ai"
                g["point_timer"] = g["speed"].point_window()
                g["timed_out"] = False
                sm.transition(State.POINT_INPUT)

    if sm.is_state(State.POINT_INPUT):
        g["point_timer"] -= dt
        if g["point_timer"] <= 0:
            g["timed_out"] = True
            g["point_hit"] = False
            g["player_dir"] = None
            g["ai_dir"] = g["ai"].pick_direction()
            g["combo"].miss()
            g["result_timer"] = g["speed"].result_delay()
            sm.transition(State.POINT_RESULT)

    if sm.is_state(State.JANKEN_INPUT):
        g["janken_timer"] -= dt
        if g["janken_timer"] <= 0:
            g["janken_timed_out"] = True
            g["player_move"] = None
            g["ai_move_choice"] = None
            g["janken_outcome"] = "LOSE"  # timeout = lose janken
            g["attacker"] = "ai"
            g["point_timer"] = g["speed"].point_window()
            g["timed_out"] = False
            g["result_timer"] = g["speed"].result_delay()
            sm.transition(State.JANKEN_RESULT)

    if sm.is_state(State.POINT_RESULT):
        g["result_timer"] -= dt
        if g["result_timer"] <= 0:
            if g["point_hit"]:
                bonus = g["combo"].hit()
                if g["attacker"] == "player":
                    g["ai_hp"] = max(0, g["ai_hp"] - 1 - bonus)
                    flash.trigger((255, 80, 80), 250)
                    shake.trigger(200 + bonus * 100, 6 + bonus * 4)
                    taunt.trigger("hit", g)
                else:
                    g["player_hp"] = max(0, g["player_hp"] - 1 - bonus)
                    flash.trigger((80, 80, 255), 250)
                    shake.trigger(300 + bonus * 100, 10 + bonus * 4)
                    taunt.trigger("lose" if g["player_hp"] <= 1 else "low_hp", g)
                if g["combo"].count >= 3:
                    taunt.trigger("combo", {"combo_count": g["combo"].count, **g})
            else:
                g["combo"].miss()
                taunt.trigger("miss", g)

            if g["player_hp"] <= 0 or g["ai_hp"] <= 0:
                g["winner"] = "player" if g["ai_hp"] <= 0 else "ai"
                taunt.trigger("win" if g["winner"] == "ai" else "lose", g)
                if g["winner"] == "player":
                    score.record_win()
                else:
                    score.record_loss()
                sm.transition(State.GAME_OVER)
            else:
                g["janken_timer"] = g["speed"].janken_window()
                g["janken_timed_out"] = False
                g["speed"].next_round()
                sm.transition(State.JANKEN_INPUT)

    # ── Draw ─────────────────────────────────────────────────────────────────

    ox, oy = shake.update(dt)
    rs = pygame.Surface((SCREEN_W, SCREEN_H))
    rs.fill((20, 20, 30))

    if sm.is_state(State.MENU):
        draw_text(rs, "JANKEN DUEL", 160, (255, 255, 255), font_lg)
        draw_text(rs, "Select Difficulty", 270, (180, 180, 180), font_sm)

        for i, diff in enumerate(DIFFICULTIES):
            color = DIFF_COLORS[diff]
            selected = i == selected_diff_idx
            label = f"> {diff.upper()} <" if selected else diff.upper()
            x = SCREEN_W // 2 + (i - 1) * 200
            surf = font.render(label, True, color if selected else (100, 100, 100))
            rs.blit(surf, surf.get_rect(center=(x, 340)))

        draw_text(rs, "LEFT / RIGHT to change", 420, (120, 120, 120), font_sm)
        draw_text(
            rs, "ENTER to start   T = toggle Ollama", 460, (180, 180, 180), font_sm
        )

        if score.rounds > 0:
            draw_text(
                rs,
                f"Session: {score.wins}W - {score.losses}L  ({score.win_rate()})",
                520,
                (100, 100, 100),
                font_sm,
            )

    else:
        draw_hp(rs)
        draw_difficulty_label(rs)
        draw_score(rs)
        draw_combo(rs)
        draw_taunt(rs)
        draw_janken_bar(rs, sm)
        draw_speed_bar(rs, sm)

        if sm.is_state(State.JANKEN_INPUT):
            draw_text(rs, "Make your move!", 220)
            draw_text(
                rs,
                "1 = Rock    2 = Paper    3 = Scissors",
                300,
                (180, 180, 180),
                font_sm,
            )

        elif sm.is_state(State.JANKEN_RESULT):
            if g.get("janken_timed_out"):
                draw_text(rs, "TOO SLOW!", 180, (255, 60, 60))
                draw_text(rs, "AI attacks!", 260, (220, 220, 100), font_sm)
            elif g["player_move"] and g["ai_move_choice"] and g["janken_outcome"]:
                draw_text(rs, f"You: {g['player_move'].value}", 180, (200, 200, 255))
                draw_text(rs, f"AI:  {g['ai_move_choice'].value}", 240, (255, 180, 180))
                color = OUTCOME_COLOR.get(g["janken_outcome"], (255, 255, 255))
                draw_text(rs, g["janken_outcome"], 320, color)
                if g["janken_outcome"] != "DRAW":
                    who = (
                        "You attack!" if g["janken_outcome"] == "WIN" else "AI attacks!"
                    )
                    draw_text(rs, who, 380, (220, 220, 100), font_sm)

        elif sm.is_state(State.POINT_INPUT):
            who = (
                "YOU point — pick direction!"
                if g["attacker"] == "player"
                else "AI points — dodge!"
            )
            draw_text(rs, who, 220)
            draw_text(rs, "Arrow keys to choose", 300, (180, 180, 180), font_sm)

        elif sm.is_state(State.POINT_RESULT):
            if g.get("timed_out"):
                draw_text(rs, "TOO SLOW!", 240, (255, 60, 60))
            elif g["player_dir"] and g["ai_dir"]:
                draw_text(
                    rs, f"You: {g['player_dir'].value}   AI: {g['ai_dir'].value}", 240
                )
                if g["point_hit"]:
                    color = (
                        (255, 80, 80) if g["attacker"] == "player" else (80, 255, 80)
                    )
                    draw_text(rs, "HIT!", 320, color)
                else:
                    draw_text(rs, "MISS!", 320, (180, 180, 180))

        elif sm.is_state(State.GAME_OVER):
            if g["winner"] == "player":
                draw_text(rs, "YOU WIN!", 220, (100, 255, 100), font_lg)
            else:
                draw_text(rs, "YOU LOSE!", 220, (255, 80, 80), font_lg)
            draw_text(rs, "R = play again   M = menu", 340, (180, 180, 180), font_sm)
            if g["combo"].max_combo >= 2:
                draw_text(
                    rs,
                    f"Best combo: x{g['combo'].max_combo}",
                    390,
                    (255, 200, 50),
                    font_sm,
                )
            if score.rounds > 0:
                draw_text(
                    rs,
                    f"Session: {score.wins}W - {score.losses}L  ({score.win_rate()})",
                    430,
                    (120, 120, 120),
                    font_sm,
                )

    flash.update(dt, rs)
    screen.blit(rs, (ox, oy))
    pygame.display.flip()

pygame.quit()
sys.exit()
