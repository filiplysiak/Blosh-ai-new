"""
Database utilities for storing Gorgias tickets and AI suggestions.

Uses SQLite for simplicity and compatibility with Railway's filesystem.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

DEFAULT_DB_PATH = os.getenv("WIDGET_DB_PATH", os.path.join("data", "widget.db"))

_DB_INSTANCE: "Database" | None = None
_DB_LOCK = threading.Lock()


def _ensure_parent_dir(path: str) -> None:
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


@contextmanager
def _sqlite_connection(path: str) -> Iterable[sqlite3.Connection]:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class Database:
    """Thin wrapper around SQLite operations used by the widget backend."""

    def __init__(self, path: str = DEFAULT_DB_PATH) -> None:
        self.path = path
        _ensure_parent_dir(self.path)
        self._lock = threading.Lock()
        self._initialize()

    # --------------------------------------------------------------------- #
    # Initialization
    # --------------------------------------------------------------------- #
    def _initialize(self) -> None:
        schema_tickets = """
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            subject TEXT,
            customer_name TEXT,
            customer_email TEXT,
            order_number TEXT,
            channel TEXT,
            last_customer_message TEXT,
            metadata TEXT,
            created_at TEXT,
            updated_at TEXT,
            synced_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """

        schema_suggestions = """
        CREATE TABLE IF NOT EXISTS suggestions (
            ticket_id TEXT PRIMARY KEY,
            suggestion_text TEXT NOT NULL,
            quality_score REAL,
            confidence REAL,
            brand TEXT,
            warnings TEXT,
            approved INTEGER,
            generated_at TEXT,
            model_id TEXT,
            FOREIGN KEY(ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
        );
        """

        index_recent = """
        CREATE INDEX IF NOT EXISTS idx_tickets_created_at
        ON tickets(datetime(created_at) DESC);
        """

        with _sqlite_connection(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.executescript(schema_tickets)
            cursor.executescript(schema_suggestions)
            cursor.executescript(index_recent)
            conn.commit()

    # --------------------------------------------------------------------- #
    # Ticket helpers
    # --------------------------------------------------------------------- #
    def upsert_ticket(self, ticket: Dict[str, Any]) -> None:
        """Insert or update a ticket record."""
        payload = {
            "ticket_id": ticket.get("ticket_id"),
            "subject": ticket.get("subject"),
            "customer_name": ticket.get("customer_name"),
            "customer_email": ticket.get("customer_email"),
            "order_number": ticket.get("order_number"),
            "channel": ticket.get("channel"),
            "last_customer_message": ticket.get("last_customer_message"),
            "metadata": json.dumps(ticket.get("metadata", {})),
            "created_at": ticket.get("created_at"),
            "updated_at": ticket.get("updated_at") or datetime.utcnow().isoformat(),
        }

        with self._lock, _sqlite_connection(self.path) as conn:
            placeholders = ", ".join(f"{key}=excluded.{key}" for key in payload if key != "ticket_id")
            query = f"""
            INSERT INTO tickets ({", ".join(payload.keys())})
            VALUES ({", ".join("?" for _ in payload)})
            ON CONFLICT(ticket_id) DO UPDATE SET
            {placeholders},
            synced_at = CURRENT_TIMESTAMP;
            """
            conn.execute(query, tuple(payload.values()))
            conn.commit()

    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, _sqlite_connection(self.path) as conn:
            row = conn.execute(
                "SELECT * FROM tickets WHERE ticket_id = ?",
                (ticket_id,),
            ).fetchone()

        return self._row_to_ticket(row) if row else None

    def get_ticket_count(self) -> int:
        with self._lock, _sqlite_connection(self.path) as conn:
            row = conn.execute("SELECT COUNT(*) AS count FROM tickets").fetchone()
            return int(row["count"]) if row else 0

    def get_recent_tickets(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._lock, _sqlite_connection(self.path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM tickets
                ORDER BY datetime(created_at) DESC, datetime(updated_at) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [self._row_to_ticket(row) for row in rows]

    def get_recent_tickets_without_suggestion(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._lock, _sqlite_connection(self.path) as conn:
            rows = conn.execute(
                """
                SELECT t.* FROM tickets t
                LEFT JOIN suggestions s ON s.ticket_id = t.ticket_id
                WHERE s.ticket_id IS NULL
                ORDER BY datetime(t.created_at) DESC, datetime(t.updated_at) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [self._row_to_ticket(row) for row in rows]

    # --------------------------------------------------------------------- #
    # Suggestion helpers
    # --------------------------------------------------------------------- #
    def save_suggestion(self, ticket_id: str, suggestion: Dict[str, Any]) -> None:
        payload = {
            "ticket_id": ticket_id,
            "suggestion_text": suggestion.get("suggestion"),
            "quality_score": suggestion.get("quality_score"),
            "confidence": suggestion.get("confidence"),
            "brand": suggestion.get("brand"),
            "warnings": json.dumps(suggestion.get("warnings", [])),
            "approved": 1 if suggestion.get("approved") else 0,
            "generated_at": suggestion.get("generated_at") or datetime.utcnow().isoformat(),
            "model_id": suggestion.get("model_id"),
        }

        with self._lock, _sqlite_connection(self.path) as conn:
            query = """
            INSERT INTO suggestions (
                ticket_id, suggestion_text, quality_score, confidence,
                brand, warnings, approved, generated_at, model_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ticket_id) DO UPDATE SET
                suggestion_text = excluded.suggestion_text,
                quality_score = excluded.quality_score,
                confidence = excluded.confidence,
                brand = excluded.brand,
                warnings = excluded.warnings,
                approved = excluded.approved,
                generated_at = excluded.generated_at,
                model_id = excluded.model_id;
            """
            conn.execute(query, tuple(payload.values()))
            conn.commit()

    def get_suggestion(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, _sqlite_connection(self.path) as conn:
            row = conn.execute(
                "SELECT * FROM suggestions WHERE ticket_id = ?",
                (ticket_id,),
            ).fetchone()

        return self._row_to_suggestion(row) if row else None

    def has_suggestion(self, ticket_id: str) -> bool:
        with self._lock, _sqlite_connection(self.path) as conn:
            row = conn.execute(
                "SELECT 1 FROM suggestions WHERE ticket_id = ? LIMIT 1",
                (ticket_id,),
            ).fetchone()

        return row is not None

    # --------------------------------------------------------------------- #
    # Analytics
    # --------------------------------------------------------------------- #
    def get_stats(self, recent_limit: int = 10) -> Dict[str, Any]:
        total_tickets = self.get_ticket_count()

        with self._lock, _sqlite_connection(self.path) as conn:
            result = conn.execute(
                "SELECT COUNT(*) AS count FROM suggestions"
            ).fetchone()
            with_suggestions = int(result["count"]) if result else 0

        recent_tickets = self.get_recent_tickets(limit=recent_limit)
        recent_ids = [ticket["ticket_id"] for ticket in recent_tickets]

        recent_with_suggestions = 0
        if recent_ids:
            placeholders = ", ".join("?" for _ in recent_ids)
            query = f"""
            SELECT COUNT(*) AS count
            FROM suggestions
            WHERE ticket_id IN ({placeholders})
            """
            with self._lock, _sqlite_connection(self.path) as conn:
                row = conn.execute(query, tuple(recent_ids)).fetchone()
                recent_with_suggestions = int(row["count"]) if row else 0

        coverage = (
            (recent_with_suggestions / len(recent_ids)) * 100 if recent_ids else 0.0
        )

        return {
            "total_tickets": total_tickets,
            "tickets_with_suggestions": with_suggestions,
            "recent_tickets_count": len(recent_ids),
            "recent_tickets_with_suggestions": recent_with_suggestions,
            "coverage_percentage": coverage,
        }

    # --------------------------------------------------------------------- #
    # Row helpers
    # --------------------------------------------------------------------- #
    def _row_to_ticket(self, row: sqlite3.Row) -> Dict[str, Any]:
        metadata = {}
        if row["metadata"]:
            try:
                metadata = json.loads(row["metadata"])
            except json.JSONDecodeError:
                metadata = {}

        return {
            "ticket_id": row["ticket_id"],
            "subject": row["subject"],
            "customer_name": row["customer_name"],
            "customer_email": row["customer_email"],
            "order_number": row["order_number"],
            "channel": row["channel"],
            "last_customer_message": row["last_customer_message"],
            "metadata": metadata,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "synced_at": row["synced_at"],
        }

    def _row_to_suggestion(self, row: sqlite3.Row) -> Dict[str, Any]:
        warnings: List[str] = []
        if row["warnings"]:
            try:
                warnings = json.loads(row["warnings"])
            except json.JSONDecodeError:
                warnings = []

        return {
            "ticket_id": row["ticket_id"],
            "suggestion_text": row["suggestion_text"],
            "quality_score": row["quality_score"],
            "confidence": row["confidence"],
            "brand": row["brand"],
            "warnings": warnings,
            "approved": bool(row["approved"]),
            "generated_at": row["generated_at"],
            "model_id": row["model_id"],
        }


def get_db() -> Database:
    """Return singleton database instance."""
    global _DB_INSTANCE
    if _DB_INSTANCE is None:
        with _DB_LOCK:
            if _DB_INSTANCE is None:
                _DB_INSTANCE = Database()
    return _DB_INSTANCE


