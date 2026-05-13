from pydantic import BaseModel
from typing import Any, Dict, List


class Interaction(BaseModel):
    message: str
    timestamp: str


class CognitiveState(BaseModel):
    persona: Dict[str, Any]
    user_perception: Dict[str, Any]
    self_perception: Dict[str, Any]
    time_context: str
    current_interaction: Interaction
    relevant_memories: List[str]
    recent_summary: str = "" 