import random
from enum import Enum


class Move(Enum):
    ROCK = "Rock"
    PAPER = "Paper"
    SCISSORS = "Scissors"


KEY_MAP: dict[str, Move] = {
    "1": Move.ROCK,
    "2": Move.PAPER,
    "3": Move.SCISSORS,
}


def ai_move() -> Move:
    return random.choice(list(Move))  # nosec B311


def resolve(player: Move, ai: Move) -> str:
    if player == ai:
        return "DRAW"
    wins: dict[Move, Move] = {
        Move.ROCK: Move.SCISSORS,
        Move.PAPER: Move.ROCK,
        Move.SCISSORS: Move.PAPER,
    }
    return "WIN" if wins[player] == ai else "LOSE"
