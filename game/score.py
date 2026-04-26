class ScoreTracker:
    def __init__(self):
        self.wins = 0
        self.losses = 0
        self.rounds = 0

    def record_win(self):
        self.wins += 1
        self.rounds += 1

    def record_loss(self):
        self.losses += 1
        self.rounds += 1

    def win_rate(self) -> str:
        if self.rounds == 0:
            return "N/A"
        return f"{int(self.wins / self.rounds * 100)}%"
