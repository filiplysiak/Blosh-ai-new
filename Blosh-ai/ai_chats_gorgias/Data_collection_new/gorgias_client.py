"""
Helper for interacting with the Gorgias API.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

_CLIENT: "GorgiasClient" | None = None


class GorgiasClient:
    """Simple REST client for interacting with Gorgias."""

    def __init__(self) -> None:
        self.base_url = os.getenv("GORGIAS_BASE_URL", "https://freebirdicons.gorgias.com/api")
        self.auth_header = os.getenv("GORGIAS_AUTH")

    # ------------------------------------------------------------------ #
    # HTTP helpers
    # ------------------------------------------------------------------ #
    def _headers(self) -> Dict[str, str]:
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
        }
        if self.auth_header:
            headers["authorization"] = self.auth_header
        return headers

    def _get(self, path: str, **kwargs: Any) -> Optional[requests.Response]:
        if not self.auth_header:
            logger.warning("GORGIAS_AUTH not configured; skipping request to %s", path)
            return None

        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        timeout = kwargs.pop("timeout", 10)

        try:
            response = requests.get(url, headers=self._headers(), timeout=timeout, **kwargs)
            if response.status_code >= 400:
                logger.error("Request to %s failed: %s - %s", url, response.status_code, response.text)
                return None
            return response
        except requests.RequestException as exc:
            logger.error("Request to %s failed: %s", url, exc)
            return None

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def fetch_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        response = self._get(f"tickets/{ticket_id}")
        if response is None:
            return None
        try:
            return response.json()
        except ValueError:
            logger.error("Invalid JSON when fetching ticket %s", ticket_id)
            return None

    def fetch_ticket_messages(self, ticket_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        params = {"limit": limit, "order_by": "created_datetime:desc"}
        response = self._get(f"tickets/{ticket_id}/messages", params=params)
        if response is None:
            return []
        try:
            data = response.json()
            if isinstance(data, dict) and "data" in data:
                return data["data"]
            if isinstance(data, list):
                return data
            return []
        except ValueError:
            logger.error("Invalid JSON when fetching messages for ticket %s", ticket_id)
            return []

    def fetch_recent_tickets(self, limit: int = 20) -> List[Dict[str, Any]]:
        capped_limit = max(1, min(limit, 100))
        params = {"limit": capped_limit, "order_by": "created_datetime:desc"}
        response = self._get("tickets", params=params)
        if response is None:
            return []
        try:
            data = response.json()
            if isinstance(data, dict) and "data" in data:
                return data["data"]
            if isinstance(data, list):
                return data
            return []
        except ValueError:
            logger.error("Invalid JSON when fetching recent tickets")
            return []

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def extract_ticket_info(
        self,
        ticket_data: Dict[str, Any],
        messages: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not ticket_data:
            return None

        ticket_id = ticket_data.get("id")
        if not ticket_id:
            return None

        if messages is None and "messages" in ticket_data:
            messages = ticket_data.get("messages") or []

        messages = messages or []

        customer = ticket_data.get("customer") or {}
        customer_name = customer.get("firstname")
        if not customer_name:
            full_name = customer.get("name") or ""
            customer_name = full_name.split()[0] if full_name else ""

        last_customer_message = self._find_last_customer_message(messages, ticket_data)

        order_number = self._extract_order_number(ticket_data)

        created_at = (
            ticket_data.get("created_datetime")
            or ticket_data.get("created_at")
            or datetime.utcnow().isoformat()
        )

        return {
            "ticket_id": str(ticket_id),
            "subject": ticket_data.get("subject"),
            "customer_name": customer_name or "",
            "customer_email": customer.get("email") or "",
            "order_number": order_number,
            "channel": ticket_data.get("channel"),
            "last_customer_message": last_customer_message or "",
            "metadata": {
                "status": ticket_data.get("status"),
                "tags": ticket_data.get("tags", []),
                "assignee": ticket_data.get("assignee"),
            },
            "created_at": created_at,
            "updated_at": ticket_data.get("updated_datetime") or created_at,
        }

    def _find_last_customer_message(
        self,
        messages: List[Dict[str, Any]],
        ticket_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        for message in messages:
            from_agent = message.get("from_agent")
            if from_agent is False and message.get("body_text"):
                return message["body_text"]

            source = message.get("source", {})
            if source.get("type") == "customer" and message.get("body_text"):
                return message["body_text"]

        if ticket_data:
            last_message = ticket_data.get("last_message") or {}
            body = last_message.get("body_text")
            if body:
                return body

        return None

    def _extract_order_number(self, ticket_data: Dict[str, Any]) -> Optional[str]:
        import re

        tags = ticket_data.get("tags") or []
        for tag in tags:
            tag_name = tag.get("name") if isinstance(tag, dict) else str(tag)
            if isinstance(tag_name, str) and (tag_name.startswith("102") or tag_name.startswith("203")):
                return tag_name

        subject = ticket_data.get("subject") or ""
        match = re.search(r"\b(102\d{6}|203\d{5})\b", subject)
        if match:
            return match.group(1)

        return None


def get_client() -> GorgiasClient:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = GorgiasClient()
    return _CLIENT


