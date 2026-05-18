from core.memory.episodic_memory import EpisodicMemory
from pathlib import Path
import json

# 1. Limpiar ChromaDB
em = EpisodicMemory()
em.reset()
print(f"ChromaDB limpio. Documentos restantes: {em.collection.count()}")

# 2. Limpiar historial (history.json)
from config import ENTITY_DATA_DIR
user_dir = ENTITY_DATA_DIR / "memory" / "users" / "default"
history_path = user_dir / "history.json"
if history_path.exists():
    history_path.write_text(json.dumps({
        "history": [],
        "thought_history": [],
        "cognitive_state": None,
        "interaction_count": 0
    }))
    print("Historial limpiado.")

# 3. Limpiar curiosidades
from config import CURIOSITY_FILE
if CURIOSITY_FILE.exists():
    CURIOSITY_FILE.write_text("[]")
    print("Curiosidades limpiadas.")

print("Reset completo.")