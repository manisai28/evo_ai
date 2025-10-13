# backend/memory/knowledge_graph.py
from typing import List, Dict, Any, Optional
import os
import datetime
from neo4j import AsyncGraphDatabase

# ===========================
# Neo4j KnowledgeGraph Class
# ===========================
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

class Neo4jKnowledgeGraph:
    def __init__(self, uri: str = NEO4J_URI, user: str = NEO4J_USER, password: str = NEO4J_PASSWORD):
        if not uri or not user or not password:
            raise RuntimeError(
                "Neo4j credentials not configured in environment "
                "(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)"
            )
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    async def close(self):
        await self.driver.close()

    async def create_entity(self, label: str, props: Dict[str, Any]) -> Dict[str, Any]:
        query = f"""
        CREATE (n:{label} $props)
        RETURN id(n) as id, n
        """
        async with self.driver.session() as session:
            res = await session.run(query, props=props)
            record = await res.single()
            return {"id": record["id"], "node": dict(record["n"])}

    async def create_relation(
        self,
        from_label: str, from_props: Dict[str, Any],
        rel_type: str,
        to_label: str, to_props: Dict[str, Any],
        rel_props: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        query = f"""
        MERGE (a:{from_label} {{key: $from_key}})
        MERGE (b:{to_label} {{key: $to_key}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r += $rprops
        RETURN id(r) as id
        """
        params = {
            "from_key": from_props.get("key"),
            "to_key": to_props.get("key"),
            "rprops": rel_props or {}
        }
        async with self.driver.session() as session:
            res = await session.run(query, **params)
            record = await res.single()
            return {"id": record["id"]}

    async def find_relations(self, label: str, key: str, depth: int = 1) -> List[Dict[str, Any]]:
        query = f"""
        MATCH (n:{label} {{key: $key}})-[r*1..{depth}]-(m)
        RETURN n, r, m LIMIT 50
        """
        async with self.driver.session() as session:
            res = await session.run(query, key=key)
            recs = await res.to_list()
            return recs

# ===========================
# MongoDB/In-Memory KnowledgeGraph Class
# ===========================
class MemoryKnowledgeGraph:
    """Simple in-memory or MongoDB backed KG for user-specific relationships"""
    def __init__(self, db_collection=None):
        self.entities = {}  # In-memory fallback
        self.db_collection = db_collection  # MongoDB collection if provided

    async def add_entity_relationship(self, user_id: str, entity1: str, relationship: str, entity2: str):
        """Example: User -> loves -> Cricket, User -> admires -> Dhoni"""
        kg_doc = {
            "user_id": user_id,
            "subject": entity1,
            "predicate": relationship,
            "object": entity2,
            "timestamp": datetime.datetime.utcnow()
        }

        # Save to MongoDB if collection provided
        if self.db_collection:
            await self.db_collection.insert_one(kg_doc)
        else:
            # fallback: store in memory
            self.entities.setdefault(user_id, []).append(kg_doc)

    async def get_relationships(self, user_id: str) -> List[Dict[str, Any]]:
        if self.db_collection:
            cursor = self.db_collection.find({"user_id": user_id})
            return [doc async for doc in cursor]
        return self.entities.get(user_id, [])
