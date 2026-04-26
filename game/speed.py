class SpeedManager:
    def __init__(self, base_ms: int = 1500, min_ms: int = 400):
        self.base_ms = base_ms
        self.min_ms = min_ms
        self.round = 0

    def next_round(self):
        self.round += 1

    def result_delay(self) -> int:
        """Shrinks every 2 rounds, floors at min_ms."""
        reduction = (self.round // 2) * 100
        return max(self.min_ms, self.base_ms - reduction)
    
    def janken_window(self) -> int:
        """Time to pick rock/paper/scissors. Shrinks every 4 rounds."""
        base = 5000
        reduction = (self.round // 4) * 300
        return max(1500, base - reduction)

    def point_window(self) -> int:
        """Time player has to input direction before auto-miss."""
        base = 3000
        reduction = (self.round // 3) * 200
        return max(800, base - reduction)

    def reset(self):
        self.round = 0
        self.result_delay()
