import random
from collections import Counter
from game.janken import Move
from game.pointing import Direction


class AI:
    def __init__(self, difficulty: str = "medium"):
        self.move_history: list[Move] = []
        self.dir_history: list[Direction] = []
        self.difficulty = difficulty

        # exploit rates per difficulty
        self.move_exploit = {"easy": 0.0, "medium": 0.7, "hard": 0.9}
        self.dir_exploit = {"easy": 0.0, "medium": 0.65, "hard": 0.85}

    # --- Janken ---
    def pick_move(self) -> Move:
        if len(self.move_history) < 3:
            return random.choice(list(Move))
        # predict player's next move based on most common
        most_common = Counter(self.move_history[-6:]).most_common(1)[0][0]
        beats = {
            Move.ROCK: Move.PAPER,
            Move.PAPER: Move.SCISSORS,
            Move.SCISSORS: Move.ROCK,
        }
        if random.random() < self.move_exploit[self.difficulty]:
            return beats[most_common]
        return random.choice(list(Move))

    def record_player_move(self, move: Move):
        self.move_history.append(move)

    # --- Pointing ---
    def pick_direction(self) -> Direction:
        if len(self.dir_history) < 3:
            return random.choice(list(Direction))
        most_common = Counter(self.dir_history[-6:]).most_common(1)[0][0]
        if random.random() < self.dir_exploit[self.difficulty]:
            return most_common
        return random.choice(list(Direction))

    def record_player_dir(self, direction: Direction):
        self.dir_history.append(direction)
