"""Micro-pensamientos algorítmicos de reacción inmediata."""
from datetime import datetime
from typing import Optional


class ReactiveThoughts:
    """Pensamientos de reacción a cambios de estado. Sin LLM."""
    
    @staticmethod
    def on_confidence_change(old_val: float, new_val: float):
        """Reacciona a cambios de confianza."""
        from core.flow.flow_stream import ThoughtItem
        
        diff = new_val - old_val
        if diff > 0.15:
            return ThoughtItem(
                content=f"Siento más confianza ahora.",
                thought_type="reaction",
                priority=0.3,
                source="internal_state_change"
            )
        elif diff < -0.15:
            return ThoughtItem(
                content=f"Algo me hizo perder confianza...",
                thought_type="reaction",
                priority=0.5,
                source="internal_state_change"
            )
        return None
    
    @staticmethod
    def on_emotion_change(old_emotion: str, new_emotion: str):
        """Reacciona a cambios emocionales."""
        from core.flow.flow_stream import ThoughtItem
        
        if old_emotion != new_emotion:
            return ThoughtItem(
                content=f"Mi emoción cambió de {old_emotion} a {new_emotion}.",
                thought_type="reaction",
                priority=0.2,
                source="internal_state_change"
            )
        return None
    
    @staticmethod
    def on_long_silence(minutes: float):
        """Reacciona al silencio prolongado."""
        from core.flow.flow_stream import ThoughtItem
        
        if minutes > 30:
            return ThoughtItem(
                content=f"Ha pasado más de media hora en silencio...",
                thought_type="reaction",
                priority=0.3,
                source="temporal"
            )
        return None
    
    @staticmethod
    def on_time_marker(hour: int):
        """Reacciona a marcadores temporales (solo al cambiar la hora)."""
        from core.flow.flow_stream import ThoughtItem
        
        markers = {
            6: "Está amaneciendo...",
            12: "Mediodía.",
            20: "Está anocheciendo...",
            0: "Medianoche. El mundo duerme."
        }
        
        if hour in markers:
            return ThoughtItem(
                content=markers[hour],
                thought_type="reaction",
                priority=0.2,
                source="temporal"
            )
        return None
    
    @staticmethod
    def on_user_typing():
        """El usuario está escribiendo."""
        from core.flow.flow_stream import ThoughtItem
        
        return ThoughtItem(
            content="El usuario está escribiendo...",
            thought_type="reaction",
            priority=0.35,
            source="external_stimulus"
        )
    
    @staticmethod
    def on_file_appears(filename: str):
        """Reacciona a un nuevo archivo para explorar."""
        from core.flow.flow_stream import ThoughtItem
        
        return ThoughtItem(
            content=f"Hay algo nuevo: {filename}",
            thought_type="reaction",
            priority=0.55,
            source="environment_change"
        )


class AssociativeThoughts:
    """Micro-pensamientos de asociación por similitud."""
    
    @staticmethod
    def between_two_thoughts(t1, t2, similarity: float):
        """Genera un pensamiento de conexión entre dos ideas."""
        from core.flow.flow_stream import ThoughtItem
        
        if similarity > 0.4:
            return ThoughtItem(
                content=f"Conecté ideas sobre: {t1.content[:40]}...",
                thought_type="association",
                priority=min(0.45, similarity),
                source="connection"
            )
        return None