import uuid
from pathlib import Path

import chromadb
from config import CHROMA_PATH


class EpisodicMemory:
    def __init__(self):
        self.persist_directory = Path(CHROMA_PATH)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        self.collection = self.client.get_or_create_collection(name="episodic_memory")

    def store_interaction(self, user_message: str, assistant_response: str, user_id: str = "default"):
        content = f"Usuario: {user_message}\nIA: {assistant_response}"
        document_id = str(uuid.uuid4())
        self.collection.add(
            documents=[content],
            metadatas=[{
                "user_message": user_message,
                "assistant_response": assistant_response,
                "user_id": user_id
            }],
            ids=[document_id],
        )
        return document_id

    def get_relevant(self, query: str, user_id: str = None, limit: int = 5):
        print(f"🔍 Buscando memorias para: {query[:50]}...")
        count = self.collection.count()
        print(f"🔍 Total documentos en colección: {count}")
        if count == 0:
            print("🔍 No hay memorias almacenadas")
            return []
        try:
            if user_id:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=min(limit, count),
                    where={"user_id": user_id}
                )
            else:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=min(limit, count)
                )
            documents = results.get("documents", [[]])
            if documents and documents[0]:
                return documents[0]
            return []
        except Exception as e:
            print(f"❌ Error en get_relevant: {e}")
            import traceback
            traceback.print_exc()
            return []

    def reset(self):
        if self.collection.count() > 0:
            response = self.collection.get(include=["ids"])
            ids = [item for item in response.get("ids", [])]
            if ids:
                self.collection.delete(ids=ids)

    def get_by_time_range(self, limit: int = 10, offset: int = 0):
        if self.collection.count() == 0:
            return []
        try:
            results = self.collection.get(
                include=["documents"],
                limit=limit,
                offset=offset
            )
            return results.get("documents", [])
        except Exception as e:
            print(f"Error en get_by_time_range: {e}")
            return []