from enum import Enum, auto


class State(Enum):
    MENU = auto()
    JANKEN_INPUT = auto()
    JANKEN_RESULT = auto()
    POINT_INPUT = auto()
    POINT_RESULT = auto()
    DAMAGE = auto()
    GAME_OVER = auto()
    PAUSED = auto()


class StateManager:
    def __init__(self):
        self.current = State.MENU

    def transition(self, new_state: State):
        self.current = new_state

    def is_state(self, state: State) -> bool:
        return self.current == state
