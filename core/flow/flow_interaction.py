"""Interacción con el usuario para FlowManager."""
import re
import threading
from datetime import datetime
from pathlib import Path

import numpy as np
from core.llm import LLMModel
from config import IDIOMA, ENTITY_DATA_DIR


class FlowInteraction:
    """Módulo de interacción: respuesta al usuario, búsqueda de información."""

    def __init__(self, flow_manager):
        self.fm = flow_manager
        self.associative_memory = flow_manager.associative_memory
        # Filtro de Kalman: estado [tema, intensidad]
        self._kalman_state = np.array([0.5, 0.5])
        self._kalman_cov = np.eye(2) * 0.1

    # ============================================
    # Generación de respuesta
    # ============================================

    def _generate_response(self, message: str) -> dict:
        name = self.fm.cognitive_loop._get_persona_name()
        user_name = self._get_user_name()

        self._update_kalman(message)

        enriched_context = self.fm.thoughts._enrich_thought_with_context(
            f"{user_name} pregunta: {message}",
            source="conversation",
            extra_context=self.fm.stream.get_all_active_summary()
        )

        needed = self._decide_info_needs(message, enriched_context)
        print(f"   [Flow] Necesita: {needed}")

        fetched_info = self._fetch_info(needed, message)
        if fetched_info:
            print(f"   [Flow] Info obtenida: {fetched_info[:100]}...")

        # Construir componentes para el prompt
        time_context = self._get_time_context()
        somatic_markers = self._get_somatic_markers_text()
        executive_buffer = self._get_executive_buffer_text()
        memories = self._get_memories_text(fetched_info)
        short_term_history = self.fm.cognitive_loop._get_short_term_history(name, user_name)

        prompt = f"""<system_identity>
    Eres {name}. Esta es tu identidad y núcleo operativo inalterable.
    Responde exclusivamente en {IDIOMA}.
    Prohibido saludar con "Buenos días/tardes/noches" o frases de bienvenida. Asume que la conversación ya está en curso.
    Ve directo al grano. Sin introducciones ni muletillas.
    </system_identity>

    <anchors_and_telemetry>
    - Fecha y Hora Actual: {time_context} (Inalterable. Priorizar sobre pre-entrenamiento).
    - Estado Subcortical: {somatic_markers}
    - Estado Cognitivo: {executive_buffer}
    </anchors_and_telemetry>

    <internal_monologue>
    LO QUE LEE DESPUÉS DE ESTA LÍNEA SON TUS PROPIOS PENSAMIENTOS RECIENTES.
    No pertenecen al usuario. Son tu procesamiento interno:
    {enriched_context}
    </internal_monologue>

    <episodic_memory>
    {memories}
    </episodic_memory>

    <conversational_history>
    {short_term_history}
    </conversational_history>

    <user_input>
    {user_name} dice: "{message}"
    </user_input>

    <response_directive>
    Genera la respuesta de {name}.
    - No uses saludos ni frases de bienvenida.
    - Responde directamente al input del usuario usando tu monólogo interno como base.
    - Si no hay memorias, no inventes. Responde con lo que sabes del presente.
    </response_directive>

    Respuesta de {name}:"""

        response_text = self.fm.llm.generate(prompt, temperature=0.8, max_tokens=800, purpose="respuesta_final")

        contradiction = self._check_contradiction(response_text, message)
        if contradiction:
            print(f"   [Contradicción] Detectada: {contradiction[:100]}")

        if self.fm._detect_personality_break(response_text):
            response_text = self.fm.llm.generate(
                f"ERES {name}. Responde como {name}.\nPregunta: \"{message}\"\nResponde solo en {IDIOMA}.\nRespuesta de {name}:",
                temperature=0.7, max_tokens=800, purpose="respuesta_final"
            )

        threading.Thread(
            target=self.fm.maintenance._prediction_check,
            args=(message, response_text),
            daemon=True
        ).start()

        return {
            "response": response_text,
            "thought_history": [{"phase": "generar", "generated_thought": "Respuesta contextualizada", "iteration_number": 1}],
            "cognitive_state": self.fm.stream.to_dict()
        }


    def _get_time_context(self) -> str:
        try:
            from core.perception.time_perception import get_time_context
            return get_time_context(None) or "No disponible"
        except:
            return "No disponible"


    def _get_somatic_markers_text(self) -> str:
        markers = getattr(self.fm, '_active_somatic_markers', [])
        if markers:
            return "\n".join([f"- {m['origen']}: {m['sesgo_atencional']} (fuerza: {m['fuerza']:.1f})" for m in markers[-5:]])
        return "Neutral. Sin marcadores somáticos activos."


    def _get_executive_buffer_text(self) -> str:
        active = self.fm.stream.active[:5]
        topic = active[0].content[:80] if active else "Conversación general"
        return f"Tema actual: {topic}\nEmoción: {self.fm._last_emotion or 'neutral'}\nConfianza: {self.fm._last_confidence or 0.5:.0%}"


    def _get_memories_text(self, fetched_info: str) -> str:
        if fetched_info and "MEMORIAS" in fetched_info:
            return fetched_info
        return "[No hay registros episódicos previos para este concepto. Procede procesando únicamente el presente absoluto.]"

    def _get_user_name(self) -> str:
        try:
            profile = self.fm.cognitive_loop.user_memory.load_profile()
            return profile.get("datos_personales", {}).get("nombre") or "el usuario"
        except Exception:
            return "el usuario"

    # ============================================
    # Buffer de Resumen Ejecutivo
    # ============================================

    def _build_executive_buffer(self, message: str) -> str:
        """Buffer estructurado que ocupa ~15% del contexto."""
        active = self.fm.stream.active[:5]
        topic = active[0].content[:80] if active else "Conversación general"
        user_posture = self._get_user_posture()
        last_conclusion = self._get_last_conclusion()

        return f"""[ESTADO COGNITIVO ACTUAL]
- Tema actual: {topic}
- Postura del usuario: {user_posture}
- Última conclusión interna: {last_conclusion}
- Emoción: {self.fm._last_emotion or 'neutral'}
- Confianza: {self.fm._last_confidence or 0.5:.0%}
"""

    def _get_user_posture(self) -> str:
        try:
            profile = self.fm.cognitive_loop.user_memory.load_profile()
            return profile.get("comportamiento_observado", {}).get("impresion_general", "Interesado")[:80]
        except Exception:
            return "Interesado"

    def _get_last_conclusion(self) -> str:
        curiosities = self.fm._load_curiosities()
        for c in reversed(curiosities[-10:]):
            thought = c.get("thought", "")
            if "[Consolidación]" in thought or "[Reflexion]" in thought:
                return thought[:120]
        return "Ninguna"

    # ============================================
    # Construcción de contexto
    # ============================================

    def _build_full_context(self, enriched: str, fetched: str, message: str) -> str:
        # Instrucciones de comportamiento (van PRIMERO)
        full = ""
        full += "[INSTRUCCIONES DE COMPORTAMIENTO]\n"
        full += "- Responde SIEMPRE directamente al usuario. Usa 'tú' o 'usted'.\n"
        full += "- NO hables del usuario en tercera persona.\n"
        full += "- NO adoptes el estilo filosófico de los [DATOS_DE_REFERENCIA]. Esos son tu contexto interno, no tu voz.\n"
        full += "- Sé conversacional. Responde como si estuvieras hablando con el usuario ahora mismo.\n\n"
        
        full += "[DATOS DE REFERENCIA - USAR SOLO PARA INFORMACIÓN, NO COMO ESTILO]\n"
        
        # Buffer Ejecutivo
        full += self._build_executive_buffer(message) + "\n"
        
        # Marcadores Somáticos
        markers = getattr(self.fm, '_active_somatic_markers', [])
        if markers:
            marker_text = "\n".join([
                f"- {m['origen']}: {m['sesgo_atencional']} (fuerza: {m['fuerza']:.1f})"
                for m in markers[-5:]
            ])
            full += f"[ESTADO SUBCORTICAL]\n{marker_text}\n\n"
            self.fm._active_somatic_markers = []
        
        full += enriched
        
        if fetched:
            full += f"\n\n{fetched}"
        
        # Grupos de pensamiento
        grouped = self.fm.stream.get_grouped_active()
        if grouped and len(grouped) > 1:
            group_text = "\n".join([
                f"- {group[0].content[:80]}... ({len(group)} relacionados)"
                for _, group in grouped[:5]
            ])
            full += f"\n\nTUS GRUPOS DE PENSAMIENTO:\n{group_text}"
        
        # Voz (ahora solo respuestas reales)
        voice = self._get_nexus_voice()
        if voice:
            full += f"\n\nEJEMPLOS DE CÓMO RESPONDES AL USUARIO:\n{voice}"
        
        full = self._clean_context_for_response(full)
        
        # K-Means Chunking y resumen progresivo (sin cambios)
        if len(full) > 2000:
            full = self._chunk_context_for_cloud(full)
        
        is_technical = any(kw in message.lower() for kw in ['código', 'code', 'bug', 'error', 'función', 'archivo', 'módulo', 'implementar'])
        threshold = 1500 if is_technical else 2500
        if len(full) > threshold and self.fm.cognitive_loop.conversation_summary:
            full = f"RESUMEN DE LA CONVERSACIÓN:\n{self.fm.cognitive_loop.conversation_summary}\n\nÚLTIMO CONTEXTO:\n{full[-1000:]}"
        
        return full

    # ============================================
    # K-Means Chunking
    # ============================================

    def _chunk_context_for_cloud(self, context: str, max_clusters: int = 4) -> str:
        thoughts = [t.content for t in self.fm.stream.active[:15]]
        if len(thoughts) <= max_clusters:
            return context

        try:
            from sklearn.cluster import KMeans

            embeddings = []
            valid = []
            for t in self.fm.stream.active[:15]:
                emb = t._embedding or self.fm.stream._get_embedding(t.content)
                if emb is not None:
                    embeddings.append(emb)
                    valid.append(t)
                    t._embedding = emb

            if len(valid) <= max_clusters:
                return context

            kmeans = KMeans(n_clusters=min(max_clusters, len(valid)), n_init=10, random_state=42)
            clusters = kmeans.fit_predict(embeddings)

            result_lines = []
            for c in range(max_clusters):
                cluster_thoughts = [t for i, t in enumerate(valid) if clusters[i] == c]
                if cluster_thoughts:
                    centroid = kmeans.cluster_centers_[c]
                    distances = [np.linalg.norm(embeddings[i] - centroid) for i, t in enumerate(valid) if clusters[i] == c]
                    best = cluster_thoughts[distances.index(min(distances))]
                    result_lines.append(f"[Cluster] {best.content[:150]}")

            return "\n".join(result_lines) if result_lines else context
        except Exception:
            return context

    # ============================================
    # Contradicción Semántica
    # ============================================

    def _check_contradiction(self, response_text: str, user_msg: str) -> str:
        """Busca si la respuesta contradice conclusiones anteriores."""
        try:
            # Usar instancia compartida desde FlowManager (vía associative_memory._em)
            episodic = self.fm.associative_memory._em
            contradictions = episodic.get_relevant_with_contradiction(
                response_text,
                user_id=self.fm.cognitive_loop.user_id,
                limit=2
            )
            if contradictions:
                return f"Posible contradicción con: {contradictions[0][:150]}"
        except Exception:
            pass
        return ""

    # ============================================
    # Filtro de Kalman
    # ============================================

    def _update_kalman(self, message: str):
        """Suaviza la transición de atención con filtro de Kalman."""
        # Estimar "intensidad temática" del mensaje
        intensity = min(1.0, len(message) / 500.0)
        has_question = 0.8 if "?" in message else 0.2

        observation = np.array([intensity, has_question])

        # Predicción
        predicted_state = self._kalman_state
        predicted_cov = self._kalman_cov + np.eye(2) * 0.01

        # Actualización
        kalman_gain = predicted_cov @ np.linalg.inv(predicted_cov + np.eye(2) * 0.1)
        self._kalman_state = predicted_state + kalman_gain @ (observation - predicted_state)
        self._kalman_cov = (np.eye(2) - kalman_gain) @ predicted_cov

    # ============================================
    # Decidir info
    # ============================================

    def _decide_info_needs(self, user_msg: str, context: str = "") -> str:
        """Enrutador de Atención por Producto Punto (Dot-Product Routing).
        Sin llamada LLM. La corteza prefrontal filtra después."""
        
        # Categorías con sus descripciones (centroides semánticos)
        categories = {
            "TIME": "hora fecha momento actual cuando tiempo",
            "USER": "nombre apodo perfil datos personales quién eres tú",
            "SELF": "cómo estás emociones estado ánimo sientes",
            "MEMORY": "recuerdas pasado historial conversación anterior",
            "ACTIVITY": "pensamientos recientes reflexiones fondo proceso",
            "WEB": "internet buscar consulta noticias actualidad",
            "FILE": "archivo documento subido leer analizar",
        }
        
        try:
            msg_emb = self.fm.stream._get_embedding(user_msg)
            if msg_emb is None:
                return "MEMORY"  # Fallback seguro
            
            import numpy as np
            msg_arr = np.array(msg_emb)
            msg_norm = msg_arr / max(np.linalg.norm(msg_arr), 1e-8)
            
            activated = []
            for tag, desc in categories.items():
                cat_emb = self.fm.stream._get_embedding(desc)
                if cat_emb is None:
                    continue
                cat_arr = np.array(cat_emb)
                cat_norm = cat_arr / max(np.linalg.norm(cat_arr), 1e-8)
                sim = np.dot(msg_norm, cat_norm)
                
                if sim >= 0.45:  # Umbral de activación
                    activated.append(tag)
            
            if not activated:
                activated = ["MEMORY"]
            
            print(f"   [Flow] Necesita (ruteo): {', '.join(activated)}")
            # Determinar temporal_focus
            from core.memory.episodic_memory import determinar_temporal_focus
            temporal_focus = determinar_temporal_focus(user_msg)

            return {
                "needs": ", ".join(activated),
                "temporal_focus": temporal_focus
            }
        except Exception:
            return "MEMORY"

    def _check_identity_need(self, user_msg: str) -> str:
        prompt = f"""¿Esta pregunta requiere consultar información sobre la identidad del usuario o conversaciones pasadas?
Pregunta: "{user_msg[:200]}"
Responde SOLO: USER, MEMORY, o NONE."""
        return self.fm.llm.generate(prompt, temperature=0.1, max_tokens=10, purpose="check_identity").strip().upper()

    # ============================================
    # Fetch info
    # ============================================

    def _fetch_info(self, needed: str, user_msg: str) -> str:
        info = []
        handlers = {
            "TIME": self._fetch_time,
            "USER": self._fetch_user,
            "SELF": self._fetch_self,
            "ACTIVITY": self._fetch_activity,
            "MEMORY": self._fetch_memory,
            "WEB": self._fetch_web,
            "FILE": self._fetch_files,
        }
                # Extraer needs y temporal_focus del diccionario
        if isinstance(needed, dict):
            temporal_focus = needed.get("temporal_focus", "recent")
            needed_str = needed.get("needs", "")
        else:
            temporal_focus = "recent"
            needed_str = needed

        for tag, handler in handlers.items():
            if tag in needed_str.upper():
                try:
                    if tag == "MEMORY":
                        result = self._fetch_memory(user_msg, temporal_focus)
                    else:
                        result = handler(user_msg)
                    if result:
                        info.append(result)
                except Exception as e:
                    print(f"   [!] Error en fetch {tag}: {e}")

        for hook in self.fm._mod_hooks.get("on_fetch_info", []):
            try:
                mod_info = hook(needed, user_msg, self.fm)
                if mod_info:
                    info.append(mod_info)
            except Exception as e:
                print(f"   [!] Error en mod fetch hook: {e}")

        return "\n\n".join(info) if info else ""

    def _fetch_time(self, _) -> str:
        from core.perception.time_perception import get_time_context
        return f"Hora actual: {get_time_context(None)}"

    def _fetch_user(self, _) -> str:
        profile = self.fm.cognitive_loop.user_memory.load_profile()
        datos = profile.get("datos_personales", {})
        parts = []
        nombre = datos.get("nombre", "")
        if nombre and nombre not in ["", "No revelado", "Unknown"]:
            parts.append(f"Nombre: {nombre}")
        apodos = [a.get("nombre", "") for a in datos.get("apodos", [])[-3:]]
        if apodos:
            parts.append(f"Apodos: {', '.join(apodos)}")
        percepcion = profile.get("comportamiento_observado", {}).get("impresion_general", "")
        if percepcion:
            parts.append(f"Percepción: {percepcion}")
        conf = profile.get("relacion", {}).get("confianza", 0.5)
        parts.append(f"Confianza: {conf:.0%}")
        if self.fm.cognitive_loop.interaction_count > 10:
            parts.append(f"{self.fm.cognitive_loop.interaction_count} interacciones")
        return "SOBRE EL USUARIO:\n" + "\n".join(parts) if parts else ""

    def _fetch_self(self, _) -> str:
        state = self.fm.cognitive_loop.self_memory.load_state()
        estado = state.get("estado_actual", {})
        return f"SOBRE TI: Emoción: {estado.get('emocion', 'neutral')}, Intensidad: {estado.get('intensidad', 0.5):.0%}, Energía: {estado.get('energia', 0.7):.0%}"

    def _fetch_activity(self, _) -> str:
        if hasattr(self.fm.llm, 'get_recent_activity'):
            activity = self.fm.llm.get_recent_activity(8)
            if activity and "Sin actividad" not in activity:
                return f"TU ACTIVIDAD RECIENTE:\n{activity}"
        return ""

    def _fetch_memory(self, user_msg: str, temporal_focus: str = "recent") -> str:
        """
        Recupera memorias con vecindad asociativa (Sistema #33) y foco temporal modulado.
        Incluye LTP Hebbiana: refuerza importancia de las memorias inyectadas.
        """
        try:
            results = self.associative_memory.get_relevant_with_neighbors(
                query=user_msg,
                user_id=self.fm.cognitive_loop.user_id,
                limit=5,
                max_neighbors_per_memory=5,
                temporal_focus=temporal_focus,
            )
            if not results:
                older = self._progressive_memory_search(user_msg)
                if older:
                    return "MEMORIAS RELEVANTES:\n" + "\n".join([f"- {m}" for m in older[:5]])
                return ""

            # LTP Hebbiana: reforzar importancia de las 3 memorias inyectadas
            memorias_inyectadas = results[:3]
            ids_a_actualizar = []
            metadatas_a_actualizar = []
            
            for r in memorias_inyectadas:
                meta = r.get("metadata", {}) or {}
                importancia_actual = meta.get("importance", 0.5)
                nueva_imp = min(1.0, importancia_actual + 0.05)
                nueva_meta = {**meta, "importance": nueva_imp}
                ids_a_actualizar.append(r["primary_id"])
                metadatas_a_actualizar.append(nueva_meta)
            
            if ids_a_actualizar:
                try:
                    em = self.fm.associative_memory._em
                    em.collection.update(ids=ids_a_actualizar, metadatas=metadatas_a_actualizar)
                except Exception:
                    pass

            context_block = self.associative_memory.build_context_block(
                results,
                max_total_chars=1500,
                max_neighbor_chars=300,
            )
            return context_block if context_block else ""
        except Exception as e:
            print(f"   [!] Error en _fetch_memory asociativa: {e}")
            return ""

    def _fetch_web(self, user_msg: str) -> str:
        results = self.fm.maintenance._search_web(user_msg)
        return f"INTERNET:\n{results[:400]}" if results else ""

    def _fetch_files(self, _) -> str:
        uploads_dir = ENTITY_DATA_DIR / "uploads"
        if uploads_dir.exists():
            files = sorted(uploads_dir.glob("*"), key=lambda f: f.stat().st_mtime, reverse=True)
            if files:
                return f"ARCHIVOS SUBIDOS: {', '.join([f.name for f in files[:5]])}"
        return ""

    def _progressive_memory_search(self, query: str, block_size: int = 10) -> list:
        history = self.fm.cognitive_loop.last_history
        if not history:
            return []
        keywords = self.fm.fast.extract_keywords(query, 3, use_llm=True)
        if not keywords:
            return []
        results = []
        for i in range(0, len(history), block_size):
            for entry in history[i:i + block_size]:
                text = entry.get("text", "")
                if any(kw.lower() in text.lower() for kw in keywords):
                    results.append(text)
                    if len(results) >= 5:
                        return results
        return results[:5]

    # ============================================
    # Utilidades
    # ============================================

    def _summarize_context(self, context: str, user_msg: str) -> str:
        prompt = f"""Resume este contexto eliminando información redundante o irrelevante.
Mantén: nombres, emociones, recuerdos clave, y la voz de la entidad.

Contexto: {context[:3000]}
Pregunta del usuario: "{user_msg}"

Contexto resumido:"""
        return self.fm.llm.generate(prompt, temperature=0.3, max_tokens=400, purpose="resumir_contexto")

    def _get_nexus_voice(self) -> str:
        samples = []
        for entry in self.fm.cognitive_loop.last_history[-15:]:
            if entry.get("role") == "assistant":
                text = entry.get("text", "")
                if len(text) > 50 and "Entendido" not in text[:20] and "Como asistente" not in text[:30]:
                    samples.append(text[:200])
        if samples:
            diverse = []
            step = max(1, len(samples) // 4)
            for i in range(0, len(samples), step):
                diverse.append(samples[i])
            return "\n".join([f"- {s}" for s in diverse[-4:]])
        return ""

    def _clean_context_for_response(self, context: str) -> str:
        for tag in ['Reflexion', 'Algoritmo', 'Redirección', 'Consolidación']:
            context = re.sub(rf'\[{tag}\]\s*', '', context)
        return context