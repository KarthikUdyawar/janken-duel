import threading
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"  # change to your local model

DEFAULT_TAUNTS = {
    "win": "Lucky shot...",
    "lose": "Too easy!",
    "hit": "That hurt? Good.",
    "miss": "Hah! Missed me!",
    "combo": "Can't stop me!",
    "low_hp": "Almost got you...",
}


class TauntEngine:
    def __init__(self):
        self.current_taunt = "..."
        self.enabled = True
        self._lock = threading.Lock()

    def _build_prompt(self, context: dict) -> str:
        return (
            f"You are a cocky arcade game AI opponent in a Rock-Paper-Scissors duel game. "
            f"Game state: {json.dumps(context)}. "
            f"Write ONE short taunt (max 8 words, no quotes, no punctuation at end). "
            f"Be funny, cocky, or menacing. Just the taunt, nothing else."
        )

    def _fetch(self, context: dict):
        try:
            resp = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "prompt": self._build_prompt(context),
                    "stream": False,
                },
                timeout=5,
            )
            if resp.status_code == 200:
                text = resp.json().get("response", "").strip()
                if text:
                    with self._lock:
                        self.current_taunt = text[:60]  # cap length
        except Exception:
            pass  # silently fall back to current taunt

    def trigger(self, event: str, game_state: dict):
        if not self.enabled:
            self.current_taunt = DEFAULT_TAUNTS.get(event, "...")
            return
        context = {
            "event": event,
            "player_hp": game_state.get("player_hp"),
            "ai_hp": game_state.get("ai_hp"),
            "combo": game_state.get("combo_count", 0),
            "attacker": game_state.get("attacker"),
        }
        # fire and forget — non-blocking
        threading.Thread(target=self._fetch, args=(context,), daemon=True).start()

    def get(self) -> str:
        with self._lock:
            return self.current_taunt

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled
