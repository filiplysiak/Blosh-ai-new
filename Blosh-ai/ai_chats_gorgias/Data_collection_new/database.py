"""
Database module for Gorgias Widget
Handles SQLite database operations for tickets and suggestions
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import os

logger = logging.getLogger(__name__)

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "widget.db")


class Database:
    """Database manager for tickets and suggestions"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_db()

    def _ensure_db_directory(self):
        """Ensure the data directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Created database directory: {db_dir}")

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}", exc_info=True)
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Tickets table
            cursor.execute("""
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
                    updated_at TEXT
                )
            """)

            # Suggestions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS suggestions (
                    ticket_id TEXT PRIMARY KEY,
                    suggestion_text TEXT NOT NULL,
                    quality_score INTEGER,
                    confidence INTEGER,
                    brand TEXT,
                    warnings TEXT,
                    approved INTEGER,
                    model_id TEXT,
                    generated_at TEXT,
                    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
                )
            """)

            # Feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT,
                    feedback_type TEXT,
                    created_at TEXT,
                    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
                )
            """)

            # Generation queue table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS generation_queue (
                    ticket_id TEXT PRIMARY KEY,
                    status TEXT,
                    priority INTEGER DEFAULT 0,
                    queued_at TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    error TEXT
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tickets_updated 
                ON tickets(updated_at DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tickets_created 
                ON tickets(created_at DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_queue_status 
                ON generation_queue(status, priority DESC)
            """)

            conn.commit()
            logger.info("Database initialized successfully")

    # ========================================================================
    # TICKET OPERATIONS
    # ========================================================================

    def upsert_ticket(self, ticket: Dict[str, Any]) -> bool:
        """Insert or update a ticket"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                metadata_json = json.dumps(ticket.get("metadata", {}))

                cursor.execute("""
                    INSERT INTO tickets (
                        ticket_id, subject, customer_name, customer_email,
                        order_number, channel, last_customer_message,
                        metadata, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(ticket_id) DO UPDATE SET
                        subject = COALESCE(excluded.subject, subject),
                        customer_name = COALESCE(excluded.customer_name, customer_name),
                        customer_email = COALESCE(excluded.customer_email, customer_email),
                        order_number = COALESCE(excluded.order_number, order_number),
                        channel = COALESCE(excluded.channel, channel),
                        last_customer_message = COALESCE(excluded.last_customer_message, last_customer_message),
                        metadata = excluded.metadata,
                        updated_at = excluded.updated_at
                """, (
                    ticket["ticket_id"],
                    ticket.get("subject"),
                    ticket.get("customer_name"),
                    ticket.get("customer_email"),
                    ticket.get("order_number"),
                    ticket.get("channel"),
                    ticket.get("last_customer_message"),
                    metadata_json,
                    ticket.get("created_at", datetime.utcnow().isoformat()),
                    ticket.get("updated_at", datetime.utcnow().isoformat())
                ))

                return True

        except Exception as e:
            logger.error(f"Error upserting ticket {ticket.get('ticket_id')}: {e}")
            return False

    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get a ticket by ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
                row = cursor.fetchone()

                if row:
                    ticket = dict(row)
                    if ticket.get("metadata"):
                        try:
                            ticket["metadata"] = json.loads(ticket["metadata"])
                        except:
                            ticket["metadata"] = {}
                    return ticket
                return None

        except Exception as e:
            logger.error(f"Error getting ticket {ticket_id}: {e}")
            return None

    def get_recent_tickets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent tickets"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM tickets 
                    ORDER BY updated_at DESC 
                    LIMIT ?
                """, (limit,))

                tickets = []
                for row in cursor.fetchall():
                    ticket = dict(row)
                    if ticket.get("metadata"):
                        try:
                            ticket["metadata"] = json.loads(ticket["metadata"])
                        except:
                            ticket["metadata"] = {}
                    tickets.append(ticket)

                return tickets

        except Exception as e:
            logger.error(f"Error getting recent tickets: {e}")
            return []

    def get_ticket_count(self) -> int:
        """Get total ticket count"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM tickets")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting ticket count: {e}")
            return 0

    # ========================================================================
    # SUGGESTION OPERATIONS
    # ========================================================================

    def upsert_suggestion(self, suggestion: Dict[str, Any]) -> bool:
        """Insert or update a suggestion"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                warnings_json = json.dumps(suggestion.get("warnings", []))

                cursor.execute("""
                    INSERT INTO suggestions (
                        ticket_id, suggestion_text, quality_score, confidence,
                        brand, warnings, approved, model_id, generated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(ticket_id) DO UPDATE SET
                        suggestion_text = excluded.suggestion_text,
                        quality_score = excluded.quality_score,
                        confidence = excluded.confidence,
                        brand = excluded.brand,
                        warnings = excluded.warnings,
                        approved = excluded.approved,
                        model_id = excluded.model_id,
                        generated_at = excluded.generated_at
                """, (
                    suggestion["ticket_id"],
                    suggestion["suggestion_text"],
                    suggestion.get("quality_score"),
                    suggestion.get("confidence"),
                    suggestion.get("brand"),
                    warnings_json,
                    suggestion.get("approved", 0),
                    suggestion.get("model_id"),
                    suggestion.get("generated_at", datetime.utcnow().isoformat())
                ))

                return True

        except Exception as e:
            logger.error(f"Error upserting suggestion for {suggestion.get('ticket_id')}: {e}")
            return False

    def get_suggestion(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get a suggestion by ticket ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM suggestions WHERE ticket_id = ?", (ticket_id,))
                row = cursor.fetchone()

                if row:
                    suggestion = dict(row)
                    if suggestion.get("warnings"):
                        try:
                            suggestion["warnings"] = json.loads(suggestion["warnings"])
                        except:
                            suggestion["warnings"] = []
                    return suggestion
                return None

        except Exception as e:
            logger.error(f"Error getting suggestion for {ticket_id}: {e}")
            return None

    def has_suggestion(self, ticket_id: str) -> bool:
        """Check if a suggestion exists for a ticket"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM suggestions WHERE ticket_id = ? LIMIT 1", (ticket_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking suggestion for {ticket_id}: {e}")
            return False

    def get_suggestion_count(self) -> int:
        """Get total suggestion count"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM suggestions")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting suggestion count: {e}")
            return 0

    # ========================================================================
    # FEEDBACK OPERATIONS
    # ========================================================================

    def record_feedback(self, ticket_id: str, feedback_type: str) -> bool:
        """Record feedback for a suggestion"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO feedback (ticket_id, feedback_type, created_at)
                    VALUES (?, ?, ?)
                """, (ticket_id, feedback_type, datetime.utcnow().isoformat()))
                return True
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            return False

    # ========================================================================
    # QUEUE OPERATIONS
    # ========================================================================

    def queue_generation(self, ticket_id: str, priority: int = 0) -> bool:
        """Add a ticket to the generation queue"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO generation_queue (ticket_id, status, priority, queued_at)
                    VALUES (?, 'pending', ?, ?)
                    ON CONFLICT(ticket_id) DO UPDATE SET
                        status = 'pending',
                        priority = excluded.priority,
                        queued_at = excluded.queued_at,
                        error = NULL
                """, (ticket_id, priority, datetime.utcnow().isoformat()))
                return True
        except Exception as e:
            logger.error(f"Error queuing generation for {ticket_id}: {e}")
            return False

    def get_next_queued_ticket(self) -> Optional[str]:
        """Get the next ticket from the queue"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ticket_id FROM generation_queue
                    WHERE status = 'pending'
                    ORDER BY priority DESC, queued_at ASC
                    LIMIT 1
                """)
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"Error getting next queued ticket: {e}")
            return None

    def update_queue_status(self, ticket_id: str, status: str, error: str = None) -> bool:
        """Update queue status for a ticket"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if status == "processing":
                    cursor.execute("""
                        UPDATE generation_queue
                        SET status = ?, started_at = ?
                        WHERE ticket_id = ?
                    """, (status, datetime.utcnow().isoformat(), ticket_id))
                elif status == "completed":
                    cursor.execute("""
                        UPDATE generation_queue
                        SET status = ?, completed_at = ?
                        WHERE ticket_id = ?
                    """, (status, datetime.utcnow().isoformat(), ticket_id))
                elif status == "failed":
                    cursor.execute("""
                        UPDATE generation_queue
                        SET status = ?, error = ?, completed_at = ?
                        WHERE ticket_id = ?
                    """, (status, error, datetime.utcnow().isoformat(), ticket_id))
                else:
                    cursor.execute("""
                        UPDATE generation_queue
                        SET status = ?
                        WHERE ticket_id = ?
                    """, (status, ticket_id))
                
                return True
        except Exception as e:
            logger.error(f"Error updating queue status for {ticket_id}: {e}")
            return False

    def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT status, COUNT(*) as count
                    FROM generation_queue
                    GROUP BY status
                """)
                stats = {row[0]: row[1] for row in cursor.fetchall()}
                return stats
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {}

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        return {
            "tickets": self.get_ticket_count(),
            "suggestions": self.get_suggestion_count(),
            "queue": self.get_queue_stats()
        }


# Singleton instance
_db_instance = None


def get_db() -> Database:
    """Get or create database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
        logger.info("Database instance created")
    return _db_instance

