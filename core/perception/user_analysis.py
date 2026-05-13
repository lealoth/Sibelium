import json
import re

from core.llm import LLMModel
from config import THOUGHT_TEMPERATURE


def analyze_user_message(message: str) -> dict:
    prompt = f"""msg → analyze(intent, emotion, topics)
msg: "{message}"

Δ → {{"intent":"...", "emotion":"...", "topics":"..."}}"""
    
    llm = LLMModel.get_instance()
    answer = llm.generate(prompt, temperature=0.3, max_tokens=100)
    
    try:
        import re as _re
        json_match = _re.search(r'\{.*\}', answer, _re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group(0))
            return {
                "intention": parsed.get("intent", ""),
                "emotion": parsed.get("emotion", ""),
                "topics": parsed.get("topics", ""),
            }
    except:
        pass
    
    return {"intention": "", "emotion": "", "topics": ""}