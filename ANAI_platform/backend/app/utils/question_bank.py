"""Small SQLite-backed question bank for the single-service deployment."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.app.config import get_settings


def _connect():
    path = Path(get_settings().QUESTION_BANK_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute("""CREATE TABLE IF NOT EXISTS questions (
        id TEXT PRIMARY KEY, subject TEXT, topic TEXT, question_type TEXT,
        difficulty TEXT, bloom_level TEXT, question_text TEXT NOT NULL,
        payload TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_questions_search ON questions(subject, topic, question_type, difficulty)")
    con.commit()
    return con


def save_question(question: Dict[str, Any], topic: str = "") -> Dict[str, Any]:
    con = _connect()
    try:
        con.execute("""INSERT OR REPLACE INTO questions
            (id, subject, topic, question_type, difficulty, bloom_level, question_text, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (
            question.get("id"), question.get("subject", ""), topic,
            question.get("question_type", ""), question.get("difficulty_level", question.get("difficulty", "")),
            question.get("bloom_level", ""), question.get("question_text", question.get("question", "")),
            json.dumps(question, ensure_ascii=False),
        ))
        con.commit()
        return {"status": "saved", "id": question.get("id")}
    finally:
        con.close()


def search_questions(q: Optional[str] = None, subject: Optional[str] = None, difficulty: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    con = _connect()
    try:
        clauses, params = [], []
        if q:
            clauses.append("(question_text LIKE ? OR topic LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%"])
        if subject:
            clauses.append("subject = ?")
            params.append(subject)
        if difficulty:
            clauses.append("difficulty = ?")
            params.append(difficulty)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        rows = con.execute(f"SELECT payload FROM questions{where} ORDER BY created_at DESC LIMIT ?", (*params, max(1, min(limit, 200)))).fetchall()
        return [json.loads(row[0]) for row in rows]
    finally:
        con.close()
