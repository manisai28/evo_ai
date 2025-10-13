# backend/memory/semantic_memory.py
from typing import List, Dict, Any
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.core.database import semantic_collection

class SemanticMemory:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # You already used this in MemoryManager; keep consistent
        self.model = SentenceTransformer(model_name)
        self.col = semantic_collection

    def _cosine(self, a: List[float], b: List[float]) -> float:
        a = np.array(a, dtype=float)
        b = np.array(b, dtype=float)
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    async def store(self, user_id: str, text: str, meta: dict = None):
        emb = self.model.encode(text).tolist()
        doc = {
            "user_id": user_id,
            "text": text,
            "embedding": emb,
            "meta": meta or {},
            "timestamp": datetime.utcnow()
        }
        await self.col.insert_one(doc)

    async def query(self, user_id: str, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        q_emb = self.model.encode(query_text).tolist()
        cursor = self.col.find({"user_id": user_id})
        all_docs = await cursor.to_list(length=200)  # limit to reasonable number
        scored = []
        for d in all_docs:
            score = self._cosine(d.get("embedding", []), q_emb)
            scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored[:top_k]]
