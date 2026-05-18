"""
Memoria Asociativa con recuperación por vecindad.
Extiende EpisodicMemory con navegación asociativa homóloga al
pattern completion del CA3 hipocampal.

Fundamento neurocientífico:
- Reactivación secuencial (Enfoque A): el hipocampo propaga la señal
  desde el engrama principal hacia nodos semánticos adyacentes mediante
  sharp-wave ripples, no en paralelo.
- Umbral dinámico sigmoide: emula el umbral de disparo celular.
  La fuerza de activación de la memoria principal (1.0 - distancia_origen)
  determina cuán lejos se propaga la activación en el espacio semántico.
- Ponderación explícita por relevancia: la activación decae con la
  distancia (spreading activation). Se inyectan etiquetas [Relevancia: X.XX]
  para guiar la atención del LLM, mitigando el sesgo lost-in-the-middle.
"""

import numpy as np
from typing import Optional, List, Dict, Any


class AssociativeMemory:
    """
    Capa asociativa sobre EpisodicMemory.

    Implementa recuperación por vecindad: para cada memoria principal
    recuperada, busca sus vecinos más cercanos en el espacio de embeddings
    usando reactivación secuencial y umbral de activación dinámico.
    """

    def __init__(self, episodic_memory):
        """
        Args:
            episodic_memory: Instancia de EpisodicMemory ya inicializada
                             y parcheada con patch_episodic_memory_get_relevant.
        """
        self._em = episodic_memory
        self._collection = episodic_memory.collection

    # ============================================
    # RECUPERACIÓN PRINCIPAL CON VECINDAD
    # ============================================

    def get_relevant_with_neighbors(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 5,
        max_neighbors_per_memory: int = 5,
        temporal_focus: str = "recent",
    ) -> List[Dict[str, Any]]:
        """
        Recupera memorias principales y sus vecinos asociativos.

        Algoritmo:
        1. Recuperar N memorias principales vía get_relevant (con IDs).
        2. Para cada memoria principal:
           a. Obtener su embedding original por ID (Opción C: inmutable).
           b. Buscar vecinos en ChromaDB usando el texto del documento como query.
           c. Calcular umbral dinámico sigmoide basado en fuerza de activación.
           d. Filtrar vecinos con distancia < umbral.
           e. Calcular relevancia normalizada para cada vecino.
        3. Retornar resultados estructurados.

        Args:
            query: Texto de búsqueda del usuario.
            user_id: Filtrar por usuario (None = todos).
            limit: Número máximo de memorias principales.
            max_neighbors_per_memory: Límite de vecinos por memoria.

        Returns:
            Lista de dicts:
            {
                "primary": str,
                "primary_id": str,
                "primary_score": float,
                "primary_distance": float,
                "neighbors": [
                    {"text": str, "id": str, "relevance": float, "distance": float},
                    ...
                ]
            }
        """
        # Paso 1: Recuperar memorias principales (con IDs)
        primary_results = self._em.get_relevant(
            query, user_id=user_id, limit=limit, include_ids=True, temporal_focus=temporal_focus
        )

        if not primary_results:
            return []

        results = []

        for primary_doc, primary_id, primary_score, primary_distance in primary_results:
            # Obtener metadata
            meta = {}
            try:
                doc_data = self._collection.get(ids=[primary_id], include=["metadatas"])
                meta = doc_data.get("metadatas", [{}])[0] or {}
            except Exception:
                pass
            
            # Paso 2a: Obtener embedding original por ID
            primary_embedding = self._get_embedding_by_id(primary_id)
            if primary_embedding is None:
                results.append({
                    "primary": primary_doc,
                    "primary_id": primary_id,
                    "primary_score": primary_score,
                    "primary_distance": primary_distance,
                    "metadata": meta,
                    "neighbors": [],
                })
                continue

            # Paso 2b: Buscar vecinos candidatos
            neighbor_candidates = self._query_neighbors(
                primary_embedding, primary_id, max_neighbors_per_memory * 2
            )

            if not neighbor_candidates:
                results.append({
                    "primary": primary_doc,
                    "primary_id": primary_id,
                    "primary_score": primary_score,
                    "primary_distance": primary_distance,
                    "metadata": meta,
                    "neighbors": [],
                })
                continue

            # Paso 2c: Calcular umbral dinámico sigmoide
            fuerza_activacion = 1.0 - primary_distance
            threshold = self._compute_activation_threshold(fuerza_activacion)

            # Paso 2d: Filtrar vecinos
            neighbors = self._filter_and_rank_neighbors(
                neighbor_candidates, threshold, max_neighbors_per_memory
            )

            results.append({
                "primary": primary_doc,
                "primary_id": primary_id,
                "primary_score": primary_score,
                "primary_distance": primary_distance,
                "metadata": meta,
                "neighbors": neighbors,
            })

        return results

    # ============================================
    # BÚSQUEDA DE VECINOS
    # ============================================

    def _query_neighbors(
        self,
        embedding: np.ndarray,
        exclude_id: str,
        n_results: int,
    ) -> List[Dict[str, Any]]:
        """
        Busca los vecinos más cercanos a un embedding en ChromaDB.

        Usa el texto del documento principal como query textual para que
        ChromaDB compute similitud sobre el espacio de embeddings de la
        colección. El embedding original se reserva como referencia inmutable.

        Args:
            embedding: Embedding de la memoria principal (referencia).
            exclude_id: ID de la memoria principal a excluir.
            n_results: Número máximo de candidatos.

        Returns:
            Lista de dicts con keys: id, text, distance, metadata.
        """
        try:
            # Recuperar el texto del documento principal para usarlo como query
            primary_data = self._collection.get(
                ids=[exclude_id], include=["documents"]
            )
            primary_docs = primary_data.get("documents", [])
            if not primary_docs or not primary_docs[0]:
                return []

            query_text = primary_docs[0]

            results = self._collection.query(
                query_texts=[query_text],
                n_results=min(n_results + 1, self._collection.count()),
            )

            documents = results.get("documents", [[]])[0]
            distances = results.get("distances", [[]])[0]
            ids = results.get("ids", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]

            # Excluir la memoria principal de sus propios vecinos
            neighbors = []
            for i, doc_id in enumerate(ids):
                if doc_id == exclude_id:
                    continue
                neighbors.append({
                    "id": doc_id,
                    "text": documents[i] if i < len(documents) else "",
                    "distance": distances[i] if i < len(distances) else 1.0,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                })

            return neighbors

        except Exception as e:
            print(f"   [!] Error en _query_neighbors: {e}")
            return []

    # ============================================
    # UMBRAL DINÁMICO SIGMOIDE
    # ============================================

    def _compute_activation_threshold(self, fuerza_activacion: float) -> float:
        """
        Calcula el umbral de activación para el vecindario.

        Emula el umbral de disparo celular: si la memoria principal se activó
        débilmente (fuerza baja), el umbral es alto (vecindario restringido).
        Si se activó fuertemente, el umbral baja (vecindario amplio).

        Fórmula:
            threshold = 0.4 * sigmoid(5 * (fuerza - 0.5))
            donde sigmoid(x) = 1 / (1 + e^(-x))

        Esto produce:
        - fuerza ≈ 0.0 (memoria difusa):  threshold ≈ 0.03
        - fuerza = 0.5 (activación media): threshold = 0.20
        - fuerza ≈ 1.0 (memoria muy cercana): threshold ≈ 0.37

        Cota superior de seguridad: 0.5 (evita ruido en espacios densos).

        Args:
            fuerza_activacion: 1.0 - distancia_origen (0.0 a 1.0).

        Returns:
            Umbral de distancia (0.0 a 0.5). Vecinos con distancia < umbral
            son incluidos.
        """
        # Sigmoide centrada en 0.5
        sigmoid = 1.0 / (1.0 + np.exp(-5.0 * (fuerza_activacion - 0.5)))
        threshold = 0.4 * sigmoid

        # Cota de seguridad
        threshold = min(threshold, 0.5)

        return threshold

    # ============================================
    # FILTRADO Y RANKING DE VECINOS
    # ============================================

    def _filter_and_rank_neighbors(
        self,
        candidates: List[Dict[str, Any]],
        threshold: float,
        max_neighbors: int,
    ) -> List[Dict[str, Any]]:
        """
        Filtra vecinos por umbral, calcula relevancia y limita cantidad.

        Args:
            candidates: Lista de vecinos candidatos con 'distance'.
            threshold: Umbral de distancia (vecinos con distancia < threshold).
            max_neighbors: Límite máximo de vecinos a retornar.

        Returns:
            Lista filtrada y ordenada con 'text', 'id', 'relevance', 'distance'.
        """
        # Filtrar por umbral
        passing = [c for c in candidates if c["distance"] < threshold]

        if not passing:
            return []

        # Ordenar por distancia (menor = más cercano)
        passing.sort(key=lambda x: x["distance"])

        # Limitar cantidad
        passing = passing[:max_neighbors]

        # Calcular relevancia normalizada
        # relevancia = 1.0 - (distancia / max_distancia_en_vecindario)
        max_dist = passing[-1]["distance"] if passing else 1.0
        if max_dist == 0:
            max_dist = 0.01

        ranked = []
        for c in passing:
            relevance = 1.0 - (c["distance"] / max_dist)
            relevance = max(0.0, min(1.0, relevance))
            ranked.append({
                "text": c["text"],
                "id": c["id"],
                "relevance": round(relevance, 4),
                "distance": round(c["distance"], 4),
            })

        return ranked

    # ============================================
    # FORMATO DE CONTEXTO PARA LLM
    # ============================================

    def build_context_block(
        self,
        results: List[Dict[str, Any]],
        max_total_chars: int = 1500,
        max_neighbor_chars: int = 300,
    ) -> str:
        """
        Construye un bloque de contexto estructurado para inyectar en el prompt.

        Formato:
            [MEMORIA PRINCIPAL 1 - Relevancia: 1.00]
            {texto}

            [MEMORIAS ASOCIADAS]
            [Relevancia: 0.87] {texto}
            [Relevancia: 0.64] {texto}

        Las etiquetas de relevancia guían la atención del LLM para que procese
        las memorias asociadas con el peso epistémico adecuado, mitigando el
        sesgo lost-in-the-middle.

        El truncado individual (max_neighbor_chars) simula la capacidad limitada
        de la memoria de trabajo (Baddeley), extrayendo solo la esencia semántica
        del recuerdo vecino (gist trace).

        Args:
            results: Resultados de get_relevant_with_neighbors().
            max_total_chars: Longitud máxima total del bloque.
            max_neighbor_chars: Longitud máxima por vecino individual.

        Returns:
            Texto formateado listo para inyectar en el prompt del LLM.
        """
        if not results:
            return ""

        blocks = []
        total_chars = 0

        for i, memory in enumerate(results):
            primary_text = memory["primary"]
            neighbors = memory.get("neighbors", [])

            # Encabezado de memoria principal
            header = f"[MEMORIA PRINCIPAL {i+1} - Relevancia: 1.00]"
            blocks.append(header)
            total_chars += len(header) + 2

            # Truncar texto principal si es necesario
            available = max_total_chars - total_chars
            if available <= 0:
                break
            truncated_primary = primary_text[:available]
            blocks.append(truncated_primary)
            total_chars += len(truncated_primary) + 2

            # Vecinos asociados
            if neighbors:
                neighbor_header = "\n[MEMORIAS ASOCIADAS]"
                blocks.append(neighbor_header)
                total_chars += len(neighbor_header) + 2

                for neighbor in neighbors:
                    relevance = neighbor["relevance"]
                    text = neighbor["text"][:max_neighbor_chars]  # Truncado individual
                    line = f"[Relevancia: {relevance:.2f}] {text}"

                    available = max_total_chars - total_chars
                    if available <= 0:
                        break
                    line = line[:available]
                    blocks.append(line)
                    total_chars += len(line) + 1

            # Separador entre memorias principales
            blocks.append("")
            total_chars += 1

        return "\n".join(blocks).strip()

    # ============================================
    # EMBEDDINGS POR ID (Opción C)
    # ============================================

    def _get_embedding_by_id(self, doc_id: str) -> Optional[np.ndarray]:
        try:
            data = self._collection.get(
                ids=[doc_id],
                include=["embeddings"],
            )
            embeddings = data.get("embeddings", [])
            if embeddings is None or (isinstance(embeddings, list) and len(embeddings) == 0):
                return None
            
            emb = embeddings[0]
            if emb is None:
                return None
            
            # Aplanar si es lista de listas
            emb_arr = np.array(emb).flatten()
            return emb_arr
        except Exception as e:
                import traceback
                print(f"   [!] Error recuperando embedding por ID {doc_id}: {e}")
                print(f"   [!] Traceback: {traceback.format_exc()}")
                return None

# ============================================
# INTEGRACIÓN CON EPISODICMEMORY
# ============================================

def patch_episodic_memory_get_relevant(episodic_memory_instance):
    """
    Extiende get_relevant() para que opcionalmente retorne IDs, scores y distancias.

    Parchea el método existente añadiendo el parámetro include_ids=False.
    Cuando include_ids=True, retorna List[Tuple[str, str, float, float]]
    en lugar de List[str].

    Args:
        episodic_memory_instance: Instancia de EpisodicMemory.

    Returns:
        La misma instancia con get_relevant extendido.
    """
    original_get_relevant = episodic_memory_instance.get_relevant

    def extended_get_relevant(
        query: str,
        user_id: Optional[str] = None,
        limit: int = 5,
        include_ids: bool = False, **kwargs
    ):
        """
        Versión extendida de get_relevant con soporte para retornar IDs,
        scores y distancias.
        """
        from datetime import datetime

        count = episodic_memory_instance.collection.count()
        if count == 0:
            return []

        search_query = episodic_memory_instance._blend_query(query)
        
        temporal_focus = kwargs.get("temporal_focus", "recent")
        try:
            if user_id:
                results = episodic_memory_instance.collection.query(
                    query_texts=[search_query],
                    n_results=min(limit * 3, count),
                    where={"user_id": user_id},
                )
            else:
                results = episodic_memory_instance.collection.query(
                    query_texts=[search_query],
                    n_results=min(limit * 3, count),
                )

            documents = results.get("documents", [[]])[0]
            distances = results.get("distances", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            ids = results.get("ids", [[]])[0]

            if not documents:
                return []

            # Puntuación Trimétrica
            scored = []
            now = datetime.now()

            for i, doc in enumerate(documents):
                similitud = 1.0 - distances[i] if i < len(distances) else 0.5

                recencia = 0.5
                meta = metadatas[i] if i < len(metadatas) else {}
                timestamp_str = meta.get("timestamp", "")
                if timestamp_str:
                    try:
                        ts = datetime.fromisoformat(timestamp_str)
                        hours_elapsed = (now - ts).total_seconds() / 3600.0
                        recencia = max(0.0, 1.0 - hours_elapsed / 168.0)
                    except Exception:
                        pass

                importancia = meta.get("importance", 0.5)
                puntaje = (similitud * 0.5) + (recencia * 0.3) + (importancia * 0.2)
                doc_id = ids[i] if i < len(ids) else ""
                scored.append((puntaje, doc, doc_id, similitud, distances[i]))

            scored.sort(key=lambda x: x[0], reverse=True)

            if include_ids:
                return [
                    (doc, doc_id, score, distance)
                    for score, doc, doc_id, _, distance in scored[:limit]
                ]
            else:
                return [doc for _, doc, _, _, _ in scored[:limit]]

        except Exception as e:
            print(f"❌ Error en get_relevant: {e}")
            import traceback
            traceback.print_exc()
            return []

    episodic_memory_instance.get_relevant = extended_get_relevant
    return episodic_memory_instance