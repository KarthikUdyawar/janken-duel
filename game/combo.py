class ComboTracker:
    def __init__(self):
        self.count = 0
        self.max_combo = 0

    def hit(self) -> int:
        """Call on hit. Returns bonus damage (0 or 1)."""
        self.count += 1
        if self.count > self.max_combo:
            self.max_combo = self.count
        if self.count % 3 == 0:
            return 1  # bonus damage every 3 hits
        return 0

    def miss(self):
        self.count = 0

    def reset(self):
        self.count = 0
        self.max_combo = 0
