"""Control de saturación de pensamientos."""
from datetime import datetime
from typing import Dict


class ThoughtSatiety:
    """Evita la sobregeneración de pensamientos del mismo tipo."""
    
    def __init__(self):
        self.recent_thoughts_by_type: Dict[str, datetime] = {}
        self.cooldowns = {
            "reaction": 30,
            "association": 60,
            "curiosity": 240,
            "reflection": 900,
            "exploration": 600,
            "detected_pattern": 120,
            "visual": 15,
            "user_interaction": 5,
        }
    
    def can_generate(self, thought_type: str) -> bool:
        """Verifica si ya es momento de generar otro pensamiento de este tipo."""
        last_time = self.recent_thoughts_by_type.get(thought_type)
        if last_time is None:
            return True
        
        elapsed = (datetime.now() - last_time).total_seconds()
        return elapsed >= self.cooldowns.get(thought_type, 60)
    
    def register(self, thought_type: str):
        """Registra que se generó un pensamiento de este tipo."""
        self.recent_thoughts_by_type[thought_type] = datetime.now()
    
    def get_next_available(self) -> float:
        """Devuelve cuántos segundos faltan para el próximo pensamiento disponible."""
        if not self.recent_thoughts_by_type:
            return 0
        
        now = datetime.now()
        min_wait = float('inf')
        
        for thought_type, last_time in self.recent_thoughts_by_type.items():
            cooldown = self.cooldowns.get(thought_type, 60)
            elapsed = (now - last_time).total_seconds()
            wait = max(0, cooldown - elapsed)
            min_wait = min(min_wait, wait)
        
        return min_wait if min_wait != float('inf') else 0