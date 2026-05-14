"""Ciclo de automejora."""
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import ENTITY_DATA_DIR
from mods.self_engineer.code_reader import CodeReader


class SelfEngineer:
    def __init__(self, flow_manager, base_dir: Path):
        self.flow = flow_manager
        self.llm = flow_manager.llm
        self.reader = CodeReader(base_dir)
        self.proposals_file = ENTITY_DATA_DIR / "memory" / "improvement_proposals.json"
        self._load_proposals()
    
    def _load_proposals(self):
        if self.proposals_file.exists():
            try:
                self.proposals = json.loads(self.proposals_file.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self.proposals = []
        else:
            self.proposals = []
    
    def _save_proposals(self):
        self.proposals_file.parent.mkdir(parents=True, exist_ok=True)
        self.proposals_file.write_text(
            json.dumps(self.proposals, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    
    def analyze_file(self, file_path: str) -> Optional[str]:
        self.reader.index_codebase()
        file_data = self.reader.get_file(file_path)
        
        if "error" in file_data:
            return None
        
        content = file_data["content"]
        
        if len(content) <= 6000:
            result = self._analyze_chunk(file_path, content, file_data)
        else:
            chunks = self._split_into_chunks(content, chunk_size=4000)
            previous_findings = ""
            all_findings = []
            
            for i, chunk in enumerate(chunks):
                chunk_result = self._analyze_chunk(
                    f"{file_path} (parte {i+1}/{len(chunks)})",
                    chunk,
                    file_data,
                    previous_findings=previous_findings
                )
                if chunk_result and "SIN_PROBLEMAS" not in chunk_result.upper():
                    all_findings.append(chunk_result)
                    previous_findings = chunk_result[:300]
            
            if not all_findings:
                result = "SIN_PROBLEMAS"
            else:
                result = self._consolidate_analyses(file_path, all_findings)
        
        if result and "SIN_PROBLEMAS" not in result.upper():
            proposal = {
                "file": file_path,
                "timestamp": datetime.now().isoformat(),
                "analysis": result
            }
            self.proposals.append(proposal)
            self._save_proposals()
            
            from core.flow.flow_stream import ThoughtItem
            self.flow.stream.add_thought(ThoughtItem(
                content=f"[Automejora] Propuesta para {file_path}",
                thought_type="self_improvement",
                priority=0.85,
                source="self_engineer"
            ))
        
        return result
    
    def _analyze_chunk(self, label: str, code: str, file_data: dict, previous_findings: str = "") -> Optional[str]:
        context = ""
        if previous_findings:
            context = f"Hallazgos previos en este archivo (NO los repitas):\n{previous_findings}\n\n"
        
        prompt = f"""{context}Analiza este fragmento de código:

ARCHIVO: {label}
LÍNEAS TOTALES: {file_data.get('lines', '?')}
FUNCIONES EN EL ARCHIVO: {', '.join(file_data.get('functions', [])[:20])}

{code}

Identifica problemas REALES. NO repitas hallazgos previos.
Si una función está incompleta en este fragmento, NO la analices.
Si no ves problemas, responde SIN_PROBLEMAS.

Para cada problema:
---
PROBLEMA: [breve]
FUNCIÓN: [nombre exacto]
SEVERIDAD: [baja/media/alta]
EXPLICACIÓN: [por qué es un problema]
SOLUCIÓN: [código o pseudocódigo]
TRADE-OFF: [qué se pierde al aplicar el cambio]
---"""
        
        return self.llm.generate(prompt, temperature=0.2, max_tokens=400, purpose="interpretar")
    
    def _split_into_chunks(self, content: str, chunk_size: int = 4000) -> list:
        lines = content.split('\n')
        chunks = []
        current = []
        current_len = 0

        for line in lines:
            current.append(line)
            current_len += len(line) + 1

            if current_len >= chunk_size and line.strip().startswith('def '):
                chunks.append('\n'.join(current))
                current = []
                current_len = 0

        if current:
            chunks.append('\n'.join(current))

        return chunks
    
    def _consolidate_analyses(self, file_path: str, analyses: list) -> str:
        combined = "\n\n".join(analyses)

        if len(combined) <= 500:
            return combined

        prompt = f"""Consolida estos análisis del archivo {file_path}.
Elimina duplicados y falsos positivos obvios.
Mantén solo problemas reales.

{combined[:2000]}

Análisis consolidado:"""

        return self.llm.generate(prompt, temperature=0.1, max_tokens=500, purpose="evaluar")
    
    def run_cycle(self):
        self.reader.index_codebase()
        files = list(self.reader.index.keys())
        if not files:
            return None
        
        target = random.choice(files)
        print(f"   [SelfEngineer] Analizando: {target}")
        return self.analyze_file(target)
    
    def get_proposals(self) -> list:
        return self.proposals