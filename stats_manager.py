class StatsManager:
    """Manages player statistics such as score, kills, rounds completed, etc."""
    def __init__(self):
        self.score: int = 3950
        self.enemies_killed: int = 0
        self.rounds_completed: int = 0
        self.flags_planted: int = 0
        self.upgrades_purchased: int = 0
        self.money_spent: int = 0

    def update_score(self, points):
        self.score += points

    def update_kills(self):
        self.enemies_killed += 1

    def update_rounds(self):
        self.rounds_completed += 1

    def update_flags(self):
        self.flags_planted += 1

    def update_upgrades(self):
        self.upgrades_purchased += 1

    def update_money(self, amount: int):
        self.money_spent += amount

    def get_stats(self) -> dict:
        return {"Score": self.score,
                "Kills": self.enemies_killed,
                "Rounds": self.rounds_completed,
                "Flags": self.flags_planted,
                "Upgrades": self.upgrades_purchased,
                "Money": self.money_spent}