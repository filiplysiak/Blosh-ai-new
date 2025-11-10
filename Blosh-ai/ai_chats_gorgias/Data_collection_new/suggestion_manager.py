"""
Suggestion manager coordinates background generation and avoids duplicate work.
"""

from __future__ import annotations

import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, Optional

from database import Database, get_db
from improved_response_generator import FINETUNED_MODEL_ID, generate_response
from ticket_sync import TicketSync, get_sync

logger = logging.getLogger(__name__)

_MANAGER_INSTANCE: "SuggestionManager" | None = None


class SuggestionManager:
    def __init__(
        self,
        db: Database,
        sync: TicketSync,
        max_workers: int = 4,
    ) -> None:
        self.db = db
        self.sync = sync
        worker_count = max(1, int(os.getenv("SUGGESTION_WORKERS", max_workers)))
        self.executor = ThreadPoolExecutor(max_workers=worker_count)
        self._pending: set[str] = set()
        self._pending_lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def ensure_suggestions_for_top_n(self, n: int = 10) -> Dict[str, Any]:
        tickets = self.db.get_recent_tickets(limit=n)
        queued = 0
        ready = 0

        for ticket in tickets:
            ticket_id = ticket["ticket_id"]
            if self.db.has_suggestion(ticket_id):
                ready += 1
                continue

            # Make sure ticket details are present before scheduling.
            if not ticket.get("last_customer_message"):
                self.sync.sync_ticket(ticket_id)

            if self.generate_suggestion_async(ticket_id):
                queued += 1

        summary = {
            "total": len(tickets),
            "ready": ready,
            "queued": queued,
        }
        return summary

    def generate_suggestion_async(self, ticket_id: str) -> bool:
        with self._pending_lock:
            if ticket_id in self._pending:
                return False
            self._pending.add(ticket_id)

        logger.info("Queueing suggestion generation for ticket %s", ticket_id)
        self.executor.submit(self._generate_async_task, ticket_id)
        return True

    def generate_suggestion_for_ticket(self, ticket: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not ticket:
            return None

        ticket_id = ticket["ticket_id"]

        if not ticket.get("last_customer_message"):
            synced = self.sync.sync_ticket(ticket_id)
            if synced:
                ticket = synced
            else:
                ticket = self.db.get_ticket(ticket_id) or ticket

        if not ticket.get("last_customer_message"):
            logger.warning("Ticket %s has no customer message; skipping generation", ticket_id)
            return None

        try:
            logger.info("Generating suggestion for ticket %s", ticket_id)
            result = generate_response(
                customer_message=ticket["last_customer_message"],
                customer_name=ticket.get("customer_name", ""),
                order_number=ticket.get("order_number"),
                subject=ticket.get("subject"),
            )

            if not result:
                logger.error("Generation returned no result for ticket %s", ticket_id)
                return None

            payload = {
                "ticket_id": ticket_id,
                "suggestion": result["response"],
                "quality_score": result["quality_score"],
                "confidence": result["quality_score"],
                "brand": result["brand"],
                "warnings": result.get("warnings", []),
                "approved": result["approved"],
                "generated_at": datetime.utcnow().isoformat(),
                "model_id": FINETUNED_MODEL_ID,
            }

            self.db.save_suggestion(ticket_id, payload)
            logger.info("Saved suggestion for ticket %s (quality: %s)", ticket_id, result["quality_score"])
            return payload

        except Exception as exc:  # pragma: no cover - safety net
            logger.error("Error generating suggestion for ticket %s: %s", ticket_id, exc, exc_info=True)
            return None

    def get_top_n_tickets(self, n: int = 10):
        return self.db.get_recent_tickets(limit=n)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _generate_async_task(self, ticket_id: str) -> None:
        try:
            ticket = self.db.get_ticket(ticket_id)
            if not ticket:
                ticket = self.sync.sync_ticket(ticket_id)
            self.generate_suggestion_for_ticket(ticket)
        finally:
            with self._pending_lock:
                self._pending.discard(ticket_id)


def get_manager() -> SuggestionManager:
    global _MANAGER_INSTANCE
    if _MANAGER_INSTANCE is None:
        _MANAGER_INSTANCE = SuggestionManager(
            db=get_db(),
            sync=get_sync(),
        )
    return _MANAGER_INSTANCE


