import pygame
import sys
from typing import Dict, List, Optional, Tuple, Any, TypedDict

from game.state_manager import StateManager, State
from game.janken import KEY_MAP as JANKEN_KEYS, resolve as janken_resolve
from game.pointing import KEY_MAP as DIR_KEYS, resolve as point_resolve
from game.effects import ScreenShake, FlashOverlay
from game.ai import AI
from game.score import ScoreTracker
from game.combo import ComboTracker
from game.taunts import TauntEngine
from game.speed import SpeedManager
from game.sounds import SoundEngine

# --- Type Definitions ---


class GameState(TypedDict):
    sm: StateManager
    player_move: Optional[Any]
    ai_move_choice: Optional[Any]
    janken_outcome: Optional[str]
    attacker: Optional[str]
    player_dir: Optional[Any]
    ai_dir: Optional[Any]
    point_hit: Optional[bool]
    player_hp: int
    ai_hp: int
    result_timer: float
    winner: Optional[str]
    ai: AI
    difficulty: str
    combo: ComboTracker
    speed: SpeedManager
    point_timer: float
    janken_timer: float
    janken_timed_out: bool
    timed_out: bool
    prev_state: Optional[State]


# --- Initialization ---

pygame.init()

SCREEN_W, SCREEN_H = 800, 600
FPS = 60

screen: pygame.Surface = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Janken Duel")
clock: pygame.time.Clock = pygame.time.Clock()

# Types for Fonts
font: pygame.font.Font = pygame.font.SysFont("dejavusans", 48)
font_sm: pygame.font.Font = pygame.font.SysFont("dejavusans", 32)
font_lg: pygame.font.Font = pygame.font.SysFont("dejavusans", 72)

shake: ScreenShake = ScreenShake()
flash: FlashOverlay = FlashOverlay()
score: ScoreTracker = ScoreTracker()
taunt: TauntEngine = TauntEngine()
sfx: SoundEngine = SoundEngine()
sfx.init()

MAX_HP: int = 5
DIFFICULTIES: List[str] = ["easy", "medium", "hard"]
DIFF_COLORS: Dict[str, Tuple[int, int, int]] = {
    "easy": (100, 255, 100),
    "medium": (255, 220, 50),
    "hard": (255, 80, 80),
}

selected_diff_idx: int = 1  # default medium


def make_state(difficulty: str = "medium") -> GameState:
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
        "result_timer": 0.0,
        "winner": None,
        "ai": AI(difficulty),
        "difficulty": difficulty,
        "combo": ComboTracker(),
        "speed": SpeedManager(),
        "point_timer": 0.0,
        "janken_timer": 0.0,
        "janken_timed_out": False,
        "timed_out": False,
        "prev_state": None,
    }


g: GameState = make_state()


def reset_game(difficulty: Optional[str] = None) -> None:
    global g, shake, flash
    diff = difficulty or DIFFICULTIES[selected_diff_idx]
    g = make_state(diff)
    shake = ScreenShake()
    flash = FlashOverlay()
    taunt.current_taunt = "..."


# ── Draw helpers ─────────────────────────────────────────────────────────────


def draw_text(
    surface: pygame.Surface,
    text: str,
    y: int,
    color: Tuple[int, int, int] = (255, 255, 255),
    f: Optional[pygame.font.Font] = None,
) -> None:
    f = f or font
    surf = f.render(text, True, color)
    rect = surf.get_rect(center=(SCREEN_W // 2, y))
    surface.blit(surf, rect)


def draw_hp(surface: pygame.Surface) -> None:
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


def draw_score(surface: pygame.Surface) -> None:
    txt = font_sm.render(
        f"W: {score.wins}  L: {score.losses}  ({score.win_rate()})",
        True,
        (160, 160, 160),
    )
    surface.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, SCREEN_H - 75))


def draw_difficulty_label(surface: pygame.Surface) -> None:
    diff = g["difficulty"].upper()
    color = DIFF_COLORS[g["difficulty"]]
    surf = font_sm.render(f"[ {diff} ]", True, color)
    surface.blit(surf, (SCREEN_W - surf.get_width() - 20, 20))


def draw_combo(surface: pygame.Surface) -> None:
    count = g["combo"].count
    if count >= 2:
        label = f"COMBO x{count}!"
        color = (255, 255, 100)
        if count >= 6:
            color = (255, 50, 50)
        elif count >= 3:
            color = (255, 180, 0)
        draw_text(surface, label, 140, color, font_sm)


def draw_taunt(surface: pygame.Surface) -> None:
    txt = taunt.get()
    if txt:
        surf = font_sm.render(f'AI: "{txt}"', True, (220, 180, 255))
        surface.blit(surf, surf.get_rect(center=(SCREEN_W // 2, 80)))


def draw_janken_bar(surface: pygame.Surface, sm: StateManager) -> None:
    if not sm.is_state(State.JANKEN_INPUT):
        return
    window = g["speed"].janken_window()
    remaining = max(0.0, g["janken_timer"])
    ratio = remaining / window
    bar_w, bar_h = 400, 16
    x, y = SCREEN_W // 2 - bar_w // 2, 160
    pygame.draw.rect(surface, (60, 60, 60), (x, y, bar_w, bar_h), border_radius=8)
    color = (255, 60, 60)
    if ratio > 0.5:
        color = (100, 255, 100)
    elif ratio > 0.25:
        color = (255, 220, 50)
    pygame.draw.rect(surface, color, (x, y, int(bar_w * ratio), bar_h), border_radius=8)


def draw_speed_bar(surface: pygame.Surface, sm: StateManager) -> None:
    if not sm.is_state(State.POINT_INPUT):
        return
    window = g["speed"].point_window()
    remaining = max(0.0, g["point_timer"])
    ratio = remaining / window
    bar_w, bar_h = 400, 16
    x, y = SCREEN_W // 2 - bar_w // 2, 160
    pygame.draw.rect(surface, (60, 60, 60), (x, y, bar_w, bar_h), border_radius=8)
    color = (255, 60, 60)
    if ratio > 0.5:
        color = (100, 255, 100)
    elif ratio > 0.25:
        color = (255, 220, 50)
    pygame.draw.rect(surface, color, (x, y, int(bar_w * ratio), bar_h), border_radius=8)
    round_txt = font_sm.render(f"Round {g['speed'].round + 1}", True, (140, 140, 140))
    surface.blit(round_txt, (SCREEN_W - round_txt.get_width() - 20, SCREEN_H // 2 - 20))


def draw_pause(surface: pygame.Surface) -> None:
    overlay = pygame.Surface((SCREEN_W, SCREEN_H))
    overlay.set_alpha(160)
    overlay.fill((0, 0, 0))
    surface.blit(overlay, (0, 0))
    draw_text(surface, "PAUSED", 180, (255, 255, 255), font_lg)
    items = [
        ("1 / 2 / 3", "Rock / Paper / Scissors"),
        ("Arrow keys", "Pick direction"),
        ("T", "Toggle Ollama taunts"),
        ("S", "Toggle sound"),
        ("ESC", "Resume"),
        ("R", "Restart  (game over)"),
        ("M", "Menu      (game over)"),
    ]
    y = 290
    for key, desc in items:
        k_surf = font_sm.render(key, True, (255, 220, 50))
        d_surf = font_sm.render(desc, True, (180, 180, 180))
        surface.blit(k_surf, (180, y))
        surface.blit(d_surf, (340, y))
        y += 36
    draw_text(surface, "ESC to resume", 530, (120, 120, 120), font_sm)


# ── Game Logic ─────────────────────────────────────────────────────────────

OUTCOME_COLOR: Dict[str, Tuple[int, int, int]] = {
    "WIN": (100, 255, 100),
    "LOSE": (255, 100, 100),
    "DRAW": (255, 220, 50),
}

running: bool = True
while running:
    dt: int = clock.tick(FPS)
    sm: StateManager = g["sm"]

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            # PAUSE toggle — checked first, works in any active game state
            if event.key == pygame.K_ESCAPE:
                if sm.is_state(State.PAUSED) and g["prev_state"]:
                    sm.transition(g["prev_state"])
                elif not sm.is_state(State.MENU) and not sm.is_state(State.GAME_OVER):
                    g["prev_state"] = sm.current
                    sm.transition(State.PAUSED)

            # Skip all other input while paused
            elif sm.is_state(State.PAUSED):
                pass

            # MENU
            elif sm.is_state(State.MENU):
                if event.key == pygame.K_RETURN:
                    g["janken_timer"] = float(g["speed"].janken_window())
                    g["janken_timed_out"] = False
                    sm.transition(State.JANKEN_INPUT)
                    sfx.play("select")
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
                elif event.key == pygame.K_s:
                    sfx.toggle()

            # JANKEN INPUT
            elif sm.is_state(State.JANKEN_INPUT):
                key_name = pygame.key.name(event.key)
                if key_name == "t":
                    enabled = taunt.toggle()
                    taunt.current_taunt = "Ollama ON" if enabled else "Offline mode"
                elif key_name == "s":
                    sfx.toggle()
                elif key_name in JANKEN_KEYS:
                    sfx.play("select")

                    # 1. Assign the moves
                    p_move = JANKEN_KEYS[key_name]
                    ai_move = g["ai"].pick_move()

                    # 2. Update state
                    g["player_move"] = p_move
                    g["ai_move_choice"] = ai_move

                    # 3. Type Narrowing: MyPy now knows p_move and ai_move are not None
                    g["ai"].record_player_move(p_move)

                    outcome = janken_resolve(p_move, ai_move)
                    g["janken_outcome"] = outcome

                    g["result_timer"] = float(g["speed"].result_delay())
                    sm.transition(State.JANKEN_RESULT)

            # POINT INPUT
            elif sm.is_state(State.POINT_INPUT):
                key_name = pygame.key.name(event.key)
                if key_name in DIR_KEYS:
                    sfx.play("select")
                    p_dir = DIR_KEYS[key_name]
                    a_dir = g["ai"].pick_direction()
                    g["ai"].record_player_dir(p_dir)
                    g["player_dir"], g["ai_dir"] = p_dir, a_dir
                    attacker = g["attacker"]
                    g["point_hit"] = point_resolve(
                        p_dir if attacker == "player" else a_dir,
                        a_dir if attacker == "player" else p_dir,
                    )
                    g["timed_out"] = False
                    g["result_timer"] = float(g["speed"].result_delay())
                    sm.transition(State.POINT_RESULT)

            # GAME OVER
            elif sm.is_state(State.GAME_OVER):
                if event.key == pygame.K_r:
                    reset_game()
                elif event.key == pygame.K_m:
                    reset_game()
                    g["sm"].transition(State.MENU)

    # ── Auto-advance Logic ─────────────────────────────────────────────────────

    if not sm.is_state(State.PAUSED):
        if sm.is_state(State.JANKEN_INPUT):
            g["janken_timer"] -= dt
            if g["janken_timer"] <= 0:
                sfx.play("timeout")
                g["janken_timed_out"] = True
                g["janken_outcome"], g["attacker"] = "LOSE", "ai"
                g["result_timer"] = float(g["speed"].result_delay())
                sm.transition(State.JANKEN_RESULT)

        if sm.is_state(State.JANKEN_RESULT):
            g["result_timer"] -= dt
            if g["result_timer"] <= 0:
                if g["janken_outcome"] == "DRAW":
                    sfx.play("draw")
                    g["janken_timer"] = float(g["speed"].janken_window())
                    sm.transition(State.JANKEN_INPUT)
                else:
                    g["attacker"] = "player" if g["janken_outcome"] == "WIN" else "ai"
                    g["point_timer"] = float(g["speed"].point_window())
                    sm.transition(State.POINT_INPUT)

        if sm.is_state(State.POINT_INPUT):
            g["point_timer"] -= dt
            if g["point_timer"] <= 0:
                sfx.play("timeout")
                g["timed_out"] = True
                g["ai_dir"] = g["ai"].pick_direction()
                g["combo"].miss()
                g["point_hit"] = g["attacker"] == "ai"
                g["result_timer"] = float(g["speed"].result_delay())
                sm.transition(State.POINT_RESULT)

        if sm.is_state(State.POINT_RESULT):
            g["result_timer"] -= dt
            if g["result_timer"] <= 0:
                if g["point_hit"]:
                    bonus = g["combo"].hit()
                    sfx.play("hit")
                    if g["attacker"] == "player":
                        g["ai_hp"] = max(0, g["ai_hp"] - 1 - bonus)
                        flash.trigger((255, 80, 80), 250)
                        shake.trigger(200 + bonus * 100, 6 + bonus * 4)
                        taunt.trigger("hit", dict(g))
                    else:
                        g["player_hp"] = max(0, g["player_hp"] - 1 - bonus)
                        flash.trigger((80, 80, 255), 250)
                        shake.trigger(300 + bonus * 100, 10 + bonus * 4)
                        taunt.trigger(
                            "lose" if g["player_hp"] <= 1 else "low_hp", dict(g)
                        )
                    if g["combo"].count >= 3:
                        sfx.play("combo")
                        taunt.trigger("combo", {"combo_count": g["combo"].count, **g})
                else:
                    sfx.play("miss")
                    g["combo"].miss()
                    taunt.trigger("miss", dict(g))

                if g["player_hp"] <= 0 or g["ai_hp"] <= 0:
                    sfx.play("game_over")
                    g["winner"] = "player" if g["ai_hp"] <= 0 else "ai"
                    taunt.trigger("win" if g["winner"] == "ai" else "lose", dict(g))
                    if g["winner"] == "player":
                        score.record_win()
                    else:
                        score.record_loss()
                    sm.transition(State.GAME_OVER)
                else:
                    g["janken_timer"] = float(g["speed"].janken_window())
                    g["speed"].next_round()
                    sm.transition(State.JANKEN_INPUT)

    # ── Rendering ────────────────────────────────────────────────────────────

    ox, oy = shake.update(dt) if not sm.is_state(State.PAUSED) else (0, 0)
    rs: pygame.Surface = pygame.Surface((SCREEN_W, SCREEN_H))
    rs.fill((20, 20, 30))

    if sm.is_state(State.MENU):
        draw_text(rs, "JANKEN DUEL", 160, (255, 255, 255), font_lg)
        draw_text(rs, "Select Difficulty", 270, (180, 180, 180), font_sm)
        for i, diff in enumerate(DIFFICULTIES):
            color = DIFF_COLORS[diff]
            selected = i == selected_diff_idx
            label = f"> {diff.upper()} <" if selected else diff.upper()
            x_pos = SCREEN_W // 2 + (i - 1) * 200
            surf = font.render(label, True, color if selected else (100, 100, 100))
            rs.blit(surf, surf.get_rect(center=(x_pos, 340)))
        draw_text(rs, "LEFT / RIGHT to change", 420, (120, 120, 120), font_sm)
        draw_text(
            rs, "ENTER to start   T = Ollama   S = sound", 460, (180, 180, 180), font_sm
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
        if not sm.is_state(State.PAUSED):
            draw_janken_bar(rs, sm)
            draw_speed_bar(rs, sm)

        if sm.is_state(State.PAUSED):
            draw_pause(rs)
        elif sm.is_state(State.JANKEN_INPUT):
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
            elif g["player_move"] and g["ai_move_choice"]:
                draw_text(rs, f"You: {g['player_move'].value}", 180, (200, 200, 255))
                draw_text(rs, f"AI:  {g['ai_move_choice'].value}", 240, (255, 180, 180))
                color = OUTCOME_COLOR.get(str(g["janken_outcome"]), (255, 255, 255))
                draw_text(rs, str(g["janken_outcome"]), 320, color)
                who = "You attack!" if g["janken_outcome"] == "WIN" else "AI attacks!"
                if g["janken_outcome"] != "DRAW":
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
                if g["point_hit"]:
                    draw_text(rs, "TOO SLOW — HIT!", 240, (255, 60, 60))
                else:
                    draw_text(rs, "TOO SLOW — MISS!", 240, (255, 140, 0))
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
