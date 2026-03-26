import logging
import sqlite3
import json
from typing import List, Dict, Any, Optional

logger = logging.getLogger("airi_database")

class AiriDatabase:
    def __init__(self, db_path: str = "airi.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        # Memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT,
                metadata TEXT,
                created_at REAL
            )
        """)
        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT,
                details TEXT,
                priority TEXT,
                status TEXT,
                due_at REAL,
                created_at REAL,
                updated_at REAL
            )
        """)
        self.conn.commit()

    def save_memory(self, memory_id: str, content: str, metadata: Dict[str, Any], created_at: float):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO memories (id, content, metadata, created_at) VALUES (?, ?, ?, ?)",
            (memory_id, content, json.dumps(metadata), created_at)
        )
        self.conn.commit()

    def get_all_memories(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, content, metadata, created_at FROM memories")
        rows = cursor.fetchall()
        return [{"id": r[0], "content": r[1], "metadata": json.loads(r[2]), "created_at": r[3]} for r in rows]

    def close(self):
        self.conn.close()
