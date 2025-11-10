"""
Utilities for synchronising tickets from Gorgias into the local database.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from database import Database, get_db
from gorgias_client import GorgiasClient, get_client

logger = logging.getLogger(__name__)

_SYNC_INSTANCE: "TicketSync" | None = None


class TicketSync:
    def __init__(self, db: Database, client: GorgiasClient) -> None:
        self.db = db
        self.client = client

    # ------------------------------------------------------------------ #
    # Public methods
    # ------------------------------------------------------------------ #
    def sync_recent_tickets(self, limit: int = 20) -> int:
        """
        Fetch the most recent tickets from Gorgias and persist them locally.
        Returns the number of tickets stored.
        """
        raw_tickets = self.client.fetch_recent_tickets(limit=limit)
        stored = 0
        for raw in raw_tickets:
            ticket_id = str(raw.get("id"))
            if not ticket_id:
                continue

            messages = None
            info = self.client.extract_ticket_info(raw, messages=None)

            # Ensure we have a customer message; fetch messages if missing.
            if info and not info.get("last_customer_message"):
                messages = self.client.fetch_ticket_messages(ticket_id)
                info = self.client.extract_ticket_info(raw, messages=messages)

            if not info:
                logger.debug("Skipping ticket %s - unable to extract info", ticket_id)
                continue

            self._persist_ticket(info)
            stored += 1

        if stored:
            logger.info("Synced %s recent tickets from Gorgias", stored)
        else:
            logger.info("No recent tickets synced from Gorgias")

        return stored

    def sync_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single ticket and upsert it locally.
        Returns the stored ticket data or None when unavailable.
        """
        raw_ticket = self.client.fetch_ticket(ticket_id)
        if not raw_ticket:
            return None

        messages = self.client.fetch_ticket_messages(ticket_id)
        info = self.client.extract_ticket_info(raw_ticket, messages=messages)

        if not info:
            logger.warning("Unable to extract ticket info for %s", ticket_id)
            return None

        self._persist_ticket(info)
        return info

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _persist_ticket(self, info: Dict[str, Any]) -> None:
        info = dict(info)
        info["created_at"] = self._normalize_datetime(info.get("created_at"))
        info["updated_at"] = self._normalize_datetime(info.get("updated_at"))
        self.db.upsert_ticket(info)

    def _normalize_datetime(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float)):
            return datetime.utcfromtimestamp(value).isoformat()
        return datetime.utcnow().isoformat()


def get_sync() -> TicketSync:
    global _SYNC_INSTANCE
    if _SYNC_INSTANCE is None:
        _SYNC_INSTANCE = TicketSync(get_db(), get_client())
    return _SYNC_INSTANCE


