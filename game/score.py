class ScoreTracker:
    def __init__(self) -> None:
        self.wins: int = 0
        self.losses: int = 0
        self.rounds: int = 0

    def record_win(self) -> None:
        self.wins += 1
        self.rounds += 1

    def record_loss(self) -> None:
        self.losses += 1
        self.rounds += 1

    def win_rate(self) -> str:
        if self.rounds == 0:
            return "N/A"
        return f"{int(self.wins / self.rounds * 100)}%"
