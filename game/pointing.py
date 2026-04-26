import random
from enum import Enum


class Direction(Enum):
    UP = "↑"
    DOWN = "↓"
    LEFT = "←"
    RIGHT = "→"


KEY_MAP = {
    "up": Direction.UP,
    "down": Direction.DOWN,
    "left": Direction.LEFT,
    "right": Direction.RIGHT,
}


def ai_direction() -> Direction:
    return random.choice(list(Direction))


def resolve(attacker_dir: Direction, defender_dir: Direction) -> bool:
    return attacker_dir == defender_dir  # match = HIT
